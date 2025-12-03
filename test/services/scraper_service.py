"""
Service for website and Instagram scraping.

Provides a clean abstraction for scraping operations, handling
path management and scraper initialization internally.
"""
from typing import Optional
import uuid
from urllib.parse import urlparse
from ..config.paths import PathManager


class ScraperService:
    """
    Handles all scraping operations.
    
    Manages scraper initialization and provides convenient methods
    for common scraping tasks like ensuring a company exists.
    """
    
    def __init__(self):
        """Initialize scraper service."""
        self._company_scraper = None
        self._instagram_scraper = None
    
    def get_company_scraper(self):
        """
        Get or create company scraper instance.
        
        Uses lazy loading to avoid importing scraper modules
        until they're actually needed.
        
        Returns:
            CompanyScraper instance
        """
        if self._company_scraper is None:
            scraper_path = PathManager.get_scraper_path()
            PathManager.add_to_sys_path(scraper_path)
            
            from scraper import CompanyScraper
            self._company_scraper = CompanyScraper()
        
        return self._company_scraper
    
    def get_instagram_scraper(self):
        """
        Get or create Instagram scraper instance.
        
        Returns:
            InstagramScraper instance
        """
        if self._instagram_scraper is None:
            scraper_path = PathManager.get_instagram_scraper_path()
            PathManager.add_to_sys_path(scraper_path)
            
            from instagram_scraper import InstagramScraper
            self._instagram_scraper = InstagramScraper()
        
        return self._instagram_scraper
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize a website URL.
        
        Ensures URL has protocol and no trailing slash.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        if not url:
            return url
        
        normalized = url.strip()
        if normalized and not normalized.startswith(("http://", "https://")):
            normalized = f"https://{normalized}"
        
        return normalized.rstrip("/") if normalized else normalized
    
    def ensure_company_exists(self, website_url: str) -> str:
        """
        Ensure company exists in database, creating if necessary.
        
        Args:
            website_url: Company website URL
            
        Returns:
            Company ID (UUID string)
            
        Raises:
            ValueError: If website_url is not provided
            Exception: If scraping fails
        """
        if not website_url:
            raise ValueError("website_url must be provided")
        
        website_url = self.normalize_url(website_url)
        scraper = self.get_company_scraper()
        
        # Check if company already exists
        existing_company_id = scraper.storage.find_company_by_url(website_url)
        
        if existing_company_id:
            return existing_company_id
        
        # Create new company and scrape
        company_id = str(uuid.uuid4())
        parsed = urlparse(website_url)
        company_name = parsed.netloc.replace('www.', '').split('.')[0]
        
        scraper.scrape_and_save(
            base_url=website_url,
            company_name=company_name,
            company_id=company_id
        )
        
        return company_id
    
    def scrape_instagram(self, instagram_account: str, limit: int = 5) -> list:
        """
        Scrape Instagram posts for an account.
        
        Args:
            instagram_account: Instagram username (without @)
            limit: Maximum number of posts to scrape
            
        Returns:
            List of Instagram captions
        """
        scraper = self.get_instagram_scraper()
        posts = scraper.scrape_posts(instagram_account, limit=limit)
        
        # Extract captions from posts
        captions = []
        for post in posts:
            if post.get('caption'):
                captions.append(post['caption'])
        
        return captions

