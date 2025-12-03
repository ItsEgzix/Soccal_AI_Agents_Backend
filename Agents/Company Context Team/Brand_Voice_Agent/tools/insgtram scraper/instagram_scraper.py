"""
Instagram Scraper Tool
Scrapes the last 5 posts from an Instagram account and returns only captions.
"""

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    ApifyClient = None

from typing import List, Dict, Optional
import os


class InstagramScraper:
    """
    Scraper for Instagram posts - returns only captions for AI analysis.
    """
    
    def __init__(self, apify_api_key: Optional[str] = None):
        """
        Initialize Instagram scraper.
        
        Args:
            apify_api_key: Apify API key (or set APIFY_API_KEY env variable)
        """
        if not APIFY_AVAILABLE:
            raise ImportError(
                "apify_client package is not installed. "
                "Please install it with: pip install apify-client"
            )
        
        self.apify_api_key = apify_api_key or os.getenv('APIFY_API_KEY')
        
        if not self.apify_api_key:
            raise Exception("Apify API key is required. Set APIFY_API_KEY env variable or pass apify_api_key parameter.")
        
        # Initialize ApifyClient
        self.client = ApifyClient(self.apify_api_key)
    
    def scrape_with_apify(self, username: str, limit: int = 5) -> List[str]:
        """
        Scrape Instagram posts and return only captions.
        
        Args:
            username: Instagram username (without @)
            limit: Number of posts to scrape (default: 5)
        
        Returns:
            List of captions (strings only)
        """
        username = username.replace('@', '').strip()
        
        # Prepare the Actor input
        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": limit,
            "searchType": "user",
            "addParentData": False
        }
        
        print(f"Starting Apify actor run for @{username}...")
        
        # Run the Actor and wait for it to finish
        try:
            run = self.client.actor("apify/instagram-scraper").call(run_input=run_input)
            
            print(f"Run completed successfully!")
            print(f"Run ID: {run['id']}")
            print(f"Dataset ID: {run['defaultDatasetId']}")
            
        except Exception as e:
            raise Exception(f"Apify actor run failed: {str(e)}")
        
        # Extract only captions
        captions = []
        
        # Fetch results from the run's dataset
        try:
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                caption = item.get('caption', '').strip()
                if caption:
                    captions.append(caption)
                
                # Stop when we have enough posts
                if len(captions) >= limit:
                    break
        
        except Exception as e:
            raise Exception(f"Error fetching results from dataset: {str(e)}")
        
        print(f"Extracted {len(captions)} captions for AI analysis")
        
        return captions
    
    def scrape_posts(self, username: str, limit: int = 5) -> List[str]:
        """
        Scrape Instagram posts and return only captions.
        
        Args:
            username: Instagram username (without @)
            limit: Number of posts to scrape (default: 5)
        
        Returns:
            List of captions (strings only)
        """
        return self.scrape_with_apify(username, limit)
