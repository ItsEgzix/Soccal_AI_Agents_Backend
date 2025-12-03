"""
Company Context Agent
Extracts company information from Supabase pgvector using semantic queries.
"""

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Optional
import json
import sys
import os

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'web scraper'))
from scraper import CompanyScraper

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_loader import PromptLoader

# Add LLM config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from llms.config import LLMConfig


class CompanyContextAgent:
    """
    Agent that extracts company context from Supabase pgvector.
    """
    
    def __init__(self, company_id: str, llm=None, log_callback=None, token_tracker=None):
        """
        Initialize Company Context Agent.
        
        Args:
            company_id: Company ID in Supabase
            llm: LangChain LLM instance (default: from LLMConfig)
            log_callback: Function to send logs (for WebSocket streaming)
            token_tracker: TokenUsageTracker instance for tracking token usage
        """
        self.company_id = company_id
        self.token_tracker = token_tracker
        
        # Create LLM with callbacks if token_tracker is provided
        if token_tracker:
            self.llm = LLMConfig.get_llm_with_callbacks(callbacks=[token_tracker])
        else:
            self.llm = llm or LLMConfig.get_default_llm()
        
        self.scraper = CompanyScraper()
        self.log_callback = log_callback
    
    def _log(self, message: str, log_type: str = "info"):
        """Send log message via callback if available, otherwise print."""
        if self.log_callback:
            try:
                if hasattr(self.log_callback, 'send_log_sync'):
                    self.log_callback.send_log_sync(message, log_type)
                else:
                    print(message)
            except:
                print(message)
        else:
            print(message)
    
    def _query_supabase(self, query: str, n_results: int = 5) -> list:
        """Query Supabase for relevant content."""
        results = self.scraper.query(query, company_id=self.company_id, n_results=n_results)
        texts = [r['text'] for r in results]
        
        # Debug logging
        self._log(f"  Query: '{query}' -> Found {len(texts)} results", "info")
        if not texts:
            self._log(f"    No results for query. Trying broader search...", "warning")
            # Fallback: get all company content
            all_content = self.scraper.get_company_content(self.company_id)
            if all_content:
                self._log(f"    Found {len(all_content)} total chunks for company", "success")
                # Return first few chunks as fallback
                return [item['text'] for item in all_content[:n_results]]
        
        return texts
    
    def extract_basic_info(self) -> Dict:
        """Extract basic company information."""
        # Get broader context first - use keyword-based queries
        self._log("  Extracting basic info...", "info")
        
        # Get all relevant content with broader queries
        all_content = self._query_supabase("company information about", n_results=10)
        if not all_content:
            # Fallback: get all content
            all_content_data = self.scraper.get_company_content(self.company_id)
            if all_content_data:
                all_content = [item['text'] for item in all_content_data[:10]]
        
        full_context = "\n".join(all_content) if all_content else ""
        
        if not full_context:
            self._log("    ⚠ No content found in Supabase", "warning")
            return {
                'name': "Not found",
                'description': "Not found",
                'industry': "Not found",
                'mission': "Not found"
            }
        
        # Extract all fields from full context
        basic_info = {}
        field_queries = {
            'name': "What is the company name?",
            'description': "What does this company do? Provide a detailed description.",
            'industry': "What industry or sector is this company in?",
            'mission': "What is the company's mission statement?"
        }
        
        for key, query in field_queries.items():
            prompt = PromptLoader.load_prompt_from_agent_dir(
                "Company_Context_Agent",
                "basic_info",
                context=full_context,
                field=key
            )
            
            response = self.llm.invoke(prompt)
            basic_info[key] = response.content.strip()
            self._log(f"    Extracted {key}", "success")
        
        return basic_info
    
    def extract_target_audience(self) -> Dict:
        """Extract target audience information."""
        self._log("  Extracting target audience...", "info")
        
        # Get broader context
        all_content = self._query_supabase("target audience customers clients", n_results=10)
        if not all_content:
            all_content_data = self.scraper.get_company_content(self.company_id)
            if all_content_data:
                all_content = [item['text'] for item in all_content_data[:10]]
        
        full_context = "\n".join(all_content) if all_content else ""
        
        if not full_context:
            return {
                'demographics': "Not found",
                'pain_points': [],
                'interests': []
            }
        
        audience = {}
        field_queries = {
            'demographics': "Predict and infer the target audience demographics based on company information.",
            'pain_points': "What problems does this company solve? What are customer pain points?",
            'interests': "What topics interest the target audience?"
        }
        
        for key, query in field_queries.items():
            if key == 'demographics':
                # Use specific demographics prediction prompt
                prompt = PromptLoader.load_prompt_from_agent_dir(
                    "Company_Context_Agent",
                    "demographics",
                    context=full_context
                )
            elif key == 'pain_points' or key == 'interests':
                prompt = PromptLoader.load_prompt_from_agent_dir(
                    "Company_Context_Agent",
                    "target_audience_list",
                    context=full_context,
                    field=key
                )
            else:
                prompt = PromptLoader.load_prompt_from_agent_dir(
                    "Company_Context_Agent",
                    "target_audience",
                    context=full_context,
                    field=key
                )
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to parse as JSON if it's a list
            if key in ['pain_points', 'interests']:
                try:
                    audience[key] = json.loads(content)
                except:
                    # If not JSON, split by lines or commas
                    audience[key] = [item.strip() for item in content.replace('\n', ',').split(',') if item.strip()]
            else:
                audience[key] = content
            
            self._log(f"    Extracted {key}", "success")
        
        return audience
    
    def extract_business_context(self) -> Dict:
        """Extract business context."""
        self._log("  Extracting business context...", "info")
        
        # Get broader context
        all_content = self._query_supabase("products services offerings", n_results=10)
        if not all_content:
            all_content_data = self.scraper.get_company_content(self.company_id)
            if all_content_data:
                all_content = [item['text'] for item in all_content_data[:10]]
        
        full_context = "\n".join(all_content) if all_content else ""
        
        if not full_context:
            return {
                'products_services': [],
                'key_differentiators': []
            }
        
        business = {}
        field_queries = {
            'products_services': "What products or services does this company offer?",
            'key_differentiators': "What makes this company unique? What are key differentiators?"
        }
        
        for key, query in field_queries.items():
            prompt = PromptLoader.load_prompt_from_agent_dir(
                "Company_Context_Agent",
                "business_context_list",
                context=full_context,
                field=key
            )
            
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Try to parse as JSON if it's a list
            try:
                business[key] = json.loads(content)
            except:
                # If not JSON, split by lines or commas
                business[key] = [item.strip() for item in content.replace('\n', ',').split(',') if item.strip()]
            
            self._log(f"    Extracted {key}", "success")
        
        return business
    
    def extract_content_mix(self) -> str:
        """Extract and propose content mix for the company."""
        self._log("  Proposing content mix...", "info")
        
        # Get broader context about the company
        all_content = self._query_supabase("company business products services target audience", n_results=10)
        if not all_content:
            all_content_data = self.scraper.get_company_content(self.company_id)
            if all_content_data:
                all_content = [item['text'] for item in all_content_data[:10]]
        
        full_context = "\n".join(all_content) if all_content else ""
        
        if not full_context:
            # Default content mix if no context available
            self._log("    ⚠ No content found, using default mix", "warning")
            return "50% educational, 20% promotional, 20% company news, 10% community"
        
        # Load prompt for content mix
        prompt = PromptLoader.load_prompt_from_agent_dir(
            "Company_Context_Agent",
            "content_mix",
            context=full_context
        )
        
        response = self.llm.invoke(prompt)
        content_mix = response.content.strip()
        
        # Validate and normalize the content mix
        # Remove any quotes if present
        content_mix = content_mix.strip('"\'')
        
        # Verify it contains 4 percentages that add up to 100
        import re
        percentages = re.findall(r'(\d+)%', content_mix)
        
        if len(percentages) == 4:
            total = sum(int(p) for p in percentages)
            if total != 100:
                # Normalize to 100%
                self._log(f"    ⚠ Percentages sum to {total}, normalizing to 100%", "warning")
                # Extract the 4 content types
                parts = re.split(r',\s*', content_mix)
                if len(parts) == 4:
                    # Extract percentages and normalize proportionally
                    old_percentages = [int(p) for p in percentages]
                    # Scale proportionally
                    normalized_percentages = []
                    for i in range(3):  # First 3: scale proportionally
                        new_pct = round((old_percentages[i] / total) * 100)
                        normalized_percentages.append(new_pct)
                    # Last one: remainder to make exactly 100
                    normalized_percentages.append(100 - sum(normalized_percentages))
                    
                    # Rebuild the content mix string with proper content type names
                    content_type_keywords = {
                        0: 'educational',
                        1: 'promotional', 
                        2: 'company news',
                        3: 'community'
                    }
                    
                    normalized_parts = []
                    for i, part in enumerate(parts):
                        # Try to extract content type from the part
                        part_lower = part.lower()
                        if 'educational' in part_lower or 'education' in part_lower:
                            content_type = 'educational'
                        elif 'promotional' in part_lower or 'promotion' in part_lower:
                            content_type = 'promotional'
                        elif 'company news' in part_lower or 'news' in part_lower or 'announcement' in part_lower:
                            content_type = 'company news'
                        elif 'community' in part_lower or 'user-generated' in part_lower or 'testimonial' in part_lower:
                            content_type = 'community'
                        else:
                            # Use default based on position
                            content_type = content_type_keywords[i]
                        
                        normalized_parts.append(f"{normalized_percentages[i]}% {content_type}")
                    
                    content_mix = ', '.join(normalized_parts)
        else:
            # If we don't have exactly 4 percentages, use default
            self._log(f"    ⚠ Invalid format (found {len(percentages)} percentages), using default mix", "warning")
            content_mix = "50% educational, 20% promotional, 20% company news, 10% community"
        
        self._log(f"    Proposed content mix: {content_mix}", "success")
        return content_mix
    
    def extract_company_profile(self) -> Dict:
        """
        Extract complete company profile from Supabase.
        
        Returns:
            Dictionary with company profile data
        """
        self._log("Extracting company profile from Supabase...", "info")
        self._log(f"  Company ID have been found", "info")
        
        # First, verify we have data
        all_content = self.scraper.get_company_content(self.company_id)
        if not all_content:
            self._log("  ⚠ No content found in Supabase for this company_id", "warning")
            return {
                'basic_info': {
                    'name': "Not found",
                    'description': "Not found",
                    'industry': "Not found",
                    'mission': "Not found"
                },
                'target_audience': {
                    'demographics': "Not found",
                    'pain_points': [],
                    'interests': []
                },
                'business_context': {
                    'products_services': [],
                    'key_differentiators': []
                }
            }
        
        self._log(f"  Found {len(all_content)} chunks in Supabase", "success")
        
        profile = {
            'basic_info': self.extract_basic_info(),
            'target_audience': self.extract_target_audience(),
            'business_context': self.extract_business_context(),
            'content_mix': self.extract_content_mix(),
        }
        
        return profile

