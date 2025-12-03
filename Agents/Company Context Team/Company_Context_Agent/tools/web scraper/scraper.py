"""
Simple Website Scraper
Scrapes homepage, About Us, and Services pages and saves to Supabase pgvector.
"""

from website_scraper import WebsiteScraper
from supabase_vector_storage import SupabaseVectorStorage
import uuid
import os
from typing import Optional, List, Dict
from datetime import datetime


class CompanyScraper:
    """
    Scraper that saves to Supabase pgvector database.
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize scraper.
        
        Args:
            connection_string: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        # Initialize Supabase storage
        try:
            self.storage = SupabaseVectorStorage(connection_string=connection_string)
        except Exception as e:
            raise Exception(f"Could not initialize Supabase storage: {str(e)}")
    
    def scrape_and_save(self, base_url: str, company_name: Optional[str] = None, company_id: Optional[str] = None, replace_existing: bool = False) -> dict:
        """
        Scrape a company website and save to Supabase.
        
        Args:
            base_url: Website URL to scrape
            company_name: Optional company name
            company_id: Optional company ID (auto-generated if not provided)
            replace_existing: If True, replace existing data (default: False - reuses existing data)
        
        Returns:
            Dictionary with scraping results
        """
        if not base_url:
            raise ValueError("Base URL is required")
        
        normalized_url = base_url.strip()
        if not normalized_url.startswith(('http://', 'https://')):
            normalized_url = f"https://{normalized_url}"
        normalized_url = normalized_url.rstrip('/')
        
        print(f"\n{'='*60}")
        print(f"CHECKING: {normalized_url}")
        if company_name:
            print(f"Company: {company_name}")
        print(f"{'='*60}\n")
        
        # First, check if URL already exists in Supabase
        existing_company_id = self.storage.find_company_by_url(normalized_url)
        
        if existing_company_id:
            print(f"Found existing data for URL: {normalized_url}")
            print(f"  Company ID: {existing_company_id}")
            
            if replace_existing:
                print(f"⚠ Will replace existing data.")
                company_id = existing_company_id
            else:
                print(f"Using existing data. Skipping scrape.")
                existing_content = self.storage.get_company_content(existing_company_id)
                return {
                    'company_id': existing_company_id,
                    'company_name': company_name,
                    'base_url': normalized_url,
                    'pages_scraped': {
                        'home': True,
                        'about': True,
                        'services': True
                    },
                    'chunks': len(existing_content),
                    'skipped': True
                }
        else:
            print(f"ℹ No existing data found for URL: {normalized_url}")
            print(f"  Will scrape and store new data.")
        
        # Generate company ID if not provided and not found
        if not company_id:
            company_id = existing_company_id or str(uuid.uuid4())
        
        # Check if company already exists by ID (additional check)
        if self.storage.company_exists(company_id):
            if replace_existing:
                print(f"⚠ Company {company_id} already exists. Will replace existing data.")
            else:
                print(f"⚠ Company {company_id} already exists. Skipping scrape.")
                existing_content = self.storage.get_company_content(company_id)
                return {
                    'company_id': company_id,
                    'company_name': company_name,
                    'base_url': normalized_url,
                    'pages_scraped': {
                        'home': True,
                        'about': True,
                        'services': True
                    },
                    'chunks': len(existing_content),
                    'skipped': True
                }
        
        # Scrape website (only if not found)
        print(f"\n{'='*60}")
        print(f"SCRAPING: {normalized_url}")
        print(f"{'='*60}\n")
        
        scraper = WebsiteScraper(normalized_url)
        scraped_data = scraper.scrape_all()
        
        # Add metadata
        scraped_data['scraped_at'] = datetime.now().isoformat()
        scraped_data['company_name'] = company_name
        scraped_data['company_id'] = company_id
        
        # Save to Supabase (will delete existing if replace_existing=True)
        print("\nStoring in Supabase...")
        chunks_stored = self.storage.store_company_content(
            company_id=company_id,
            base_url=normalized_url,
            scraped_data=scraped_data,
            replace_existing=replace_existing
        )
        
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"URL: {normalized_url}")
        print(f"Company ID: {company_id}")
        print(f"Homepage: {'✓' if scraped_data['home'] else '✗'}")
        print(f"About: {'✓' if scraped_data['about'] else '✗'}")
        print(f"Services: {'✓' if scraped_data['services'] else '✗'}")
        print(f"Stored {chunks_stored} chunks in Supabase")
        print(f"{'='*60}\n")
        
        return {
            'company_id': company_id,
            'company_name': company_name,
            'base_url': normalized_url,
            'pages_scraped': {
                'home': scraped_data['home'] is not None,
                'about': scraped_data['about'] is not None,
                'services': scraped_data['services'] is not None
            },
            'chunks': chunks_stored
        }
    
    def query(self, query: str, company_id: Optional[str] = None, n_results: int = 5) -> List[Dict]:
        """
        Query Supabase for relevant content.
        
        Args:
            query: Search query
            company_id: Optional company ID to filter results
            n_results: Number of results to return
        
        Returns:
            List of relevant chunks
        """
        return self.storage.query(query, company_id=company_id, n_results=n_results)
    
    def get_company_content(self, company_id: str) -> List[Dict]:
        """
        Get all content for a specific company from Supabase.
        
        Args:
            company_id: Company identifier
        
        Returns:
            List of all chunks for the company
        """
        return self.storage.get_company_content(company_id)
    
    def delete_company(self, company_id: str) -> bool:
        """
        Delete all content for a company from Supabase.
        
        Args:
            company_id: Company identifier
        
        Returns:
            True if successful
        """
        return self.storage.delete_company(company_id)


def main():
    """Command line usage."""
    import sys
    
    scraper = CompanyScraper()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        company_name = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        url = input("Enter website URL (e.g., https://example.com): ").strip()
        company_name = input("Enter company name (optional): ").strip() or None
    
    if not url:
        print("No URL provided")
        return
    
    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Scrape and save
    results = scraper.scrape_and_save(url, company_name=company_name)
    
    print(f"\nScraping complete!")
    print(f"Company ID: {results['company_id']}")
    print(f"Chunks stored: {results['chunks']}")


if __name__ == "__main__":
    main()

