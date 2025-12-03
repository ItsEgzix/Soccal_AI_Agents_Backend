"""
Simple Website Scraper
Scrapes homepage, About Us, and Services pages from a company website.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from typing import Dict, Optional, List
import re


class WebsiteScraper:
    def __init__(self, base_url: str):
        """
        Initialize scraper with base URL.
        
        Args:
            base_url: Base URL of the website (e.g., "https://example.com")
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.scraped_data = {}
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove newlines and tabs
        text = text.replace('\n', ' ').replace('\t', ' ')
        return text.strip()
    
    def _is_placeholder_text(self, text: str) -> bool:
        """Check if text is placeholder/lorem ipsum."""
        text_lower = text.lower()
        placeholder_patterns = [
            r'lorem ipsum',
            r'this is the heading',
            r'this is a heading',
            r'placeholder',
            r'sample text',
            r'dummy text',
            r'add your text here',
            r'click to edit'
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _is_navigation_text(self, text: str) -> bool:
        """Check if text looks like navigation/menu."""
        text_lower = text.lower().strip()
        nav_patterns = [
            r'^(home|about|services|contact|portfolio|blog|login|sign up|menu)$',
            r'^(home|about|services|contact)$',
        ]
        # Very short text that's likely navigation
        if len(text) < 15 and text.isupper():
            return True
        return False
    
    def _extract_text_from_soup(self, soup: BeautifulSoup) -> str:
        """Extract main text content from BeautifulSoup object."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        return self._clean_text(text)
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract structured content with headings.
        
        Returns:
            List of content blocks with headings and text
        """
        # Remove unwanted elements more thoroughly
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button"]):
            element.decompose()
        
        # Remove elements with common navigation/UI classes
        for element in soup.find_all(class_=re.compile(r'nav|menu|button|form|search|social|share|cookie|popup|modal', re.I)):
            element.decompose()
        
        content_blocks = []
        current_heading = None
        current_text = []
        
        # Find main content area
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return []
        
        # Process headings and paragraphs in order (skip generic divs)
        for element in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            tag_name = element.name.lower()
            
            # Skip if it's in a nav or unwanted container
            parent_classes = ' '.join(element.parent.get('class', [])) if element.parent else ''
            if re.search(r'nav|menu|header|footer', parent_classes, re.I):
                continue
            
            # If it's a heading, save previous block and start new one
            if tag_name.startswith('h'):
                heading_text = self._clean_text(element.get_text())
                
                # Skip navigation headings
                if self._is_navigation_text(heading_text):
                    continue
                
                # Save previous block if it has content
                if current_heading or current_text:
                    text = ' '.join(current_text).strip()
                    if text and len(text) > 30:  # Only meaningful blocks
                        content_blocks.append({
                            'heading': current_heading,
                            'text': self._clean_text(text)
                        })
                
                # Start new block with new heading
                current_heading = heading_text
                current_text = []
            
            # If it's a paragraph, add to current block
            elif tag_name == 'p':
                text = element.get_text()
                cleaned = self._clean_text(text)
                
                # Filter out placeholder, navigation, and very short text
                if (cleaned and 
                    len(cleaned) > 30 and  # Minimum length
                    not self._is_placeholder_text(cleaned) and
                    not self._is_navigation_text(cleaned)):
                    current_text.append(cleaned)
        
        # Save last block
        if current_heading or current_text:
            text = ' '.join(current_text).strip()
            if text and len(text) > 30:
                content_blocks.append({
                    'heading': current_heading,
                    'text': self._clean_text(text)
                })
        
        return content_blocks
    
    def _remove_duplicates(self, content_blocks: List[Dict]) -> List[Dict]:
        """Remove duplicate and similar content blocks."""
        seen_texts = set()
        unique_blocks = []
        
        for block in content_blocks:
            text = block.get('text', '')
            
            # Skip placeholder text
            if self._is_placeholder_text(text):
                continue
            
            # Normalize text for comparison
            normalized = re.sub(r'\s+', ' ', text.lower().strip())
            
            # Skip if too short
            if len(normalized) < 30:
                continue
            
            # Check for exact duplicates
            if normalized in seen_texts:
                continue
            
            # Check for partial duplicates (if 80% of text matches something we've seen)
            is_duplicate = False
            for seen in seen_texts:
                # Check if one contains the other (with some threshold)
                if len(normalized) > 50 and len(seen) > 50:
                    # If one is mostly contained in the other
                    shorter = normalized if len(normalized) < len(seen) else seen
                    longer = seen if len(normalized) < len(seen) else normalized
                    
                    # Check if shorter is 80% contained in longer
                    if shorter in longer or longer in shorter:
                        # Check similarity more carefully
                        words_shorter = set(shorter.split())
                        words_longer = set(longer.split())
                        if len(words_shorter) > 0:
                            overlap = len(words_shorter & words_longer) / len(words_shorter)
                            if overlap > 0.8:  # 80% overlap
                                is_duplicate = True
                                break
            
            if is_duplicate:
                continue
            
            seen_texts.add(normalized)
            unique_blocks.append(block)
        
        return unique_blocks
    
    def _find_section_on_homepage(self, soup: BeautifulSoup, section_keywords: List[str]) -> Optional[Dict]:
        """
        Find a section (About, Services) on the homepage.
        
        Args:
            soup: BeautifulSoup object of homepage
            section_keywords: Keywords to search for (e.g., ['about', 'about us', 'who we are'])
        
        Returns:
            Section content with heading and text, or None
        """
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return None
        
        # Search for headings that match keywords
        for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in main.find_all(heading_tag):
                heading_text = self._clean_text(heading.get_text()).lower()
                
                # Check if heading matches any keyword
                for keyword in section_keywords:
                    if keyword.lower() in heading_text:
                        # Found matching heading, find its parent section
                        parent = heading.parent
                        
                        # Try to find a section/div container
                        for _ in range(3):  # Go up max 3 levels
                            if parent and parent.name in ['section', 'div', 'article']:
                                # Extract all text from this container
                                section_text = parent.get_text()
                                cleaned = self._clean_text(section_text)
                                
                                # Remove the heading text from content
                                heading_clean = self._clean_text(heading.get_text())
                                if cleaned.startswith(heading_clean):
                                    cleaned = cleaned[len(heading_clean):].strip()
                                
                                # Filter out placeholder text
                                if self._is_placeholder_text(cleaned):
                                    continue
                                
                                # Limit length and ensure it's meaningful
                                if len(cleaned) > 50:
                                    # Take first reasonable chunk (up to 2000 chars)
                                    cleaned = cleaned[:2000]
                                    return {
                                        'heading': self._clean_text(heading.get_text()),
                                        'text': cleaned
                                    }
                            
                            if parent:
                                parent = parent.parent
                        
                        # Fallback: collect siblings after heading
                        section_content = []
                        current = heading.next_sibling
                        count = 0
                        while current and count < 10:  # Limit to 10 elements
                            if hasattr(current, 'name') and current.name:
                                if current.name.startswith('h'):
                                    break  # Stop at next heading
                                if current.name in ['p', 'div', 'section', 'li']:
                                    text = self._clean_text(current.get_text())
                                    if text and len(text) > 20:
                                        section_content.append(text)
                            current = getattr(current, 'next_sibling', None)
                            count += 1
                        
                        if section_content:
                            # Filter out placeholder text
                            filtered_content = [
                                text for text in section_content[:5]
                                if not self._is_placeholder_text(text) and len(text) > 30
                            ]
                            
                            if filtered_content:
                                combined = ' '.join(filtered_content)
                                if len(combined) > 50:
                                    return {
                                        'heading': self._clean_text(heading.get_text()),
                                        'text': combined[:2000]  # Limit length
                                    }
        
        return None
    
    def _extract_meta_info(self, soup: BeautifulSoup) -> Dict:
        """Extract meta tags and basic info."""
        meta_info = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            meta_info['title'] = self._clean_text(title_tag.get_text())
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc:
            meta_info['description'] = meta_desc.get('content', '').strip()
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            meta_info['keywords'] = meta_keywords.get('content', '').strip()
        
        return meta_info
    
    def _find_page_url(self, page_name: str, possible_paths: list) -> Optional[str]:
        """Try to find a page URL from possible paths."""
        for path in possible_paths:
            url = urljoin(self.base_url, path)
            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    return response.url
            except:
                continue
        return None
    
    def scrape_page(self, url: str, page_type: str) -> Optional[Dict]:
        """
        Scrape a single page with structured content.
        
        Args:
            url: URL to scrape
            page_type: Type of page (home, about, services)
        
        Returns:
            Dictionary with scraped data or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract meta info
            meta_info = self._extract_meta_info(soup)
            
            # Extract structured content with headings
            structured_content = self._extract_structured_content(soup)
            
            # Remove duplicates and placeholder text
            structured_content = self._remove_duplicates(structured_content)
            
            # Filter out any remaining placeholder text
            structured_content = [
                block for block in structured_content 
                if not self._is_placeholder_text(block.get('text', ''))
            ]
            
            # Combine into readable format
            content_parts = []
            for block in structured_content:
                heading = block.get('heading')
                text = block.get('text', '')
                
                # Skip if text is too short or placeholder
                if len(text) < 30 or self._is_placeholder_text(text):
                    continue
                
                if heading:
                    content_parts.append(f"{heading}\n{text}")
                else:
                    content_parts.append(text)
            
            combined_content = "\n\n".join(content_parts)
            
            return {
                'url': response.url,
                'page_type': page_type,
                'meta': meta_info,
                'content': combined_content,
                'structured_content': structured_content  # Keep structured version
            }
        
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_homepage(self) -> Optional[Dict]:
        """Scrape homepage."""
        print(f"Scraping homepage: {self.base_url}")
        return self.scrape_page(self.base_url, 'home')
    
    def scrape_about(self) -> Optional[Dict]:
        """Scrape About Us page."""
        possible_paths = ['/about', '/about-us', '/aboutus', '/company', '/our-story', '/who-we-are']
        url = self._find_page_url('about', possible_paths)
        
        if url:
            print(f"Scraping About page: {url}")
            return self.scrape_page(url, 'about')
        else:
            print("About page not found")
            return None
    
    def scrape_services(self) -> Optional[Dict]:
        """Scrape Services/Products page."""
        possible_paths = [
            '/services', '/products', '/solutions', '/solution', 
            '/offerings', '/what-we-do', '/our-services', '/our-solutions'
        ]
        url = self._find_page_url('services', possible_paths)
        
        if url:
            print(f"Scraping Services page: {url}")
            return self.scrape_page(url, 'services')
        else:
            print("Services page not found")
            return None
    
    def scrape_all(self) -> Dict:
        """
        Scrape homepage and extract About/Services sections from it.
        
        Returns:
            Dictionary with all scraped data
        """
        print(f"\n{'='*50}")
        print(f"Scraping website: {self.base_url}")
        print(f"{'='*50}\n")
        
        results = {
            'base_url': self.base_url,
            'home': None,
            'about': None,
            'services': None
        }
        
        # Scrape homepage
        results['home'] = self.scrape_homepage()
        
        # Extract About section from homepage
        if results['home']:
            try:
                response = self.session.get(self.base_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                about_section = self._find_section_on_homepage(
                    soup, 
                    ['about', 'about us', 'who we are', 'our story', 'company']
                )
                
                if about_section:
                    print("Found About section on homepage")
                    results['about'] = {
                        'url': self.base_url,
                        'page_type': 'about',
                        'section_type': 'homepage_section',
                        'heading': about_section.get('heading'),
                        'content': about_section.get('text'),
                        'meta': {}
                    }
                else:
                    print("About section not found on homepage, trying separate page...")
                    results['about'] = self.scrape_about()
                
                # Extract Services section from homepage
                services_section = self._find_section_on_homepage(
                    soup,
                    [
                        'services', 'products', 'solutions', 'solution',
                        'what we do', 'offerings', 'our services', 'our service',
                        'our solutions', 'our solution', 'what we offer',
                        'our offerings', 'what we provide', 'our products'
                    ]
                )
                
                if services_section:
                    print("Found Services section on homepage")
                    results['services'] = {
                        'url': self.base_url,
                        'page_type': 'services',
                        'section_type': 'homepage_section',
                        'heading': services_section.get('heading'),
                        'content': services_section.get('text'),
                        'meta': {}
                    }
                else:
                    print("Services section not found on homepage, trying separate page...")
                    results['services'] = self.scrape_services()
            except Exception as e:
                print(f"Error extracting sections: {str(e)}")
                # Fallback to separate pages
                results['about'] = self.scrape_about()
                results['services'] = self.scrape_services()
        else:
            # If homepage failed, try separate pages
            results['about'] = self.scrape_about()
            results['services'] = self.scrape_services()
        
        # Store results
        self.scraped_data = results
        
        return results
    
    def get_text_chunks(self, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
        """
        Split scraped content into chunks for vector storage.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        chunk_id = 0
        
        for page_type in ['home', 'about', 'services']:
            page_data = self.scraped_data.get(page_type)
            if not page_data or not page_data.get('content'):
                continue
            
            text = page_data['content']
            url = page_data.get('url', '')
            meta = page_data.get('meta', {})
            
            # Split text into chunks
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                if chunk_text.strip():
                    chunks.append({
                        'id': f"{page_type}_{chunk_id}",
                        'text': chunk_text.strip(),
                        'metadata': {
                            'page_type': page_type,
                            'url': url,
                            'title': meta.get('title', ''),
                            'description': meta.get('description', ''),
                            'base_url': self.base_url,
                            'chunk_index': chunk_id
                        }
                    })
                    chunk_id += 1
                
                start = end - chunk_overlap
        
        return chunks
    
    def save_to_json(self, filename: str = 'scraped_data.json'):
        """Save scraped data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    
    def get_combined_text(self) -> str:
        """Get all scraped text combined."""
        combined = []
        
        for page_type in ['home', 'about', 'services']:
            page_data = self.scraped_data.get(page_type)
            if page_data and page_data.get('content'):
                combined.append(f"=== {page_type.upper()} PAGE ===")
                combined.append(page_data['content'])
                combined.append("")
        
        return "\n".join(combined)


def main():
    """Example usage."""
    # Example: Scrape a website
    url = input("Enter website URL (e.g., https://example.com): ").strip()
    
    if not url:
        print("No URL provided")
        return
    
    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Create scraper and scrape
    scraper = WebsiteScraper(url)
    results = scraper.scrape_all()
    
    # Save to JSON
    scraper.save_to_json('scraped_data.json')
    
    # Print summary
    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")
    print(f"Homepage: {'✓' if results['home'] else '✗'}")
    print(f"About: {'✓' if results['about'] else '✗'}")
    print(f"Services: {'✓' if results['services'] else '✗'}")
    
    # Print combined text preview
    combined = scraper.get_combined_text()
    print(f"\n{'='*50}")
    print("COMBINED TEXT PREVIEW (first 500 chars):")
    print(f"{'='*50}")
    print(combined[:500] + "..." if len(combined) > 500 else combined)


if __name__ == "__main__":
    main()

