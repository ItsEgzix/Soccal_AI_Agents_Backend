"""
Company Context Agent

Extracts company information from Supabase pgvector using semantic queries.
Migrated to use BaseAgent and AgentPathManager.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any, Optional
import json
import sys
from pathlib import Path

# Import core infrastructure
_agents_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_agents_root))
from core.base_agent import BaseAgent
from core.path_manager import AgentPathManager

# Setup imports for this agent
AgentPathManager.setup_imports("company_context", "company_context")

# Import team-specific utilities
_team_utils = _agents_root / "teams" / "company_context" / "utils"
sys.path.insert(0, str(_team_utils))
from prompt_loader import PromptLoader

# Import tools
_tool_path = _agents_root / "teams" / "company_context" / "tools" / "web_scraper"
if str(_tool_path) not in sys.path:
    sys.path.insert(0, str(_tool_path))
from scraper import CompanyScraper


class CompanyContextAgent(BaseAgent):
    """
    Agent that extracts company context from Supabase pgvector.
    
    Inherits from BaseAgent for consistent initialization and logging.
    """
    
    @staticmethod
    def _clean_json_response(content: str) -> str:
        """
        Clean LLM response by removing markdown code blocks.
        
        Args:
            content: Raw LLM response that may contain ```json ... ``` blocks
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        content = content.strip()
        
        # Pattern to match ```json or ``` at start and ``` at end
        if content.startswith('```'):
            # Find the end of the first line (```json or ```)
            first_newline = content.find('\n')
            if first_newline != -1:
                content = content[first_newline + 1:]
            
            # Remove trailing ```
            if content.endswith('```'):
                content = content[:-3]
        
        return content.strip()
    
    @staticmethod
    def _parse_json_list(content: str) -> list:
        """
        Parse JSON list from LLM response, handling markdown code blocks.
        
        Args:
            content: LLM response that should contain a JSON list
            
        Returns:
            Parsed list or empty list on failure
        """
        cleaned = CompanyContextAgent._clean_json_response(content)
        
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            return [result] if result else []
        except json.JSONDecodeError:
            # Fallback: try to extract items line by line
            lines = cleaned.split('\n')
            items = []
            for line in lines:
                line = line.strip()
                # Skip empty lines and JSON brackets
                if not line or line in ['[', ']', '{', '}']:
                    continue
                # Remove leading/trailing quotes and commas
                line = line.strip('",').strip("'")
                if line and not line.startswith('```'):
                    items.append(line)
            return items
    
    def __init__(self, company_id: str, llm=None, log_callback=None, token_tracker=None):
        """
        Initialize Company Context Agent.
        
        Args:
            company_id: Company ID in Supabase
            llm: LangChain LLM instance (default: from LLMConfig via BaseAgent)
            log_callback: Function to send logs (for WebSocket streaming)
            token_tracker: TokenUsageTracker instance for tracking token usage
        """
        # Initialize base class (handles LLM setup)
        super().__init__(llm=llm, log_callback=log_callback, token_tracker=token_tracker)
        
        # Agent-specific initialization
        self.company_id = company_id
        self.scraper = CompanyScraper()
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute agent logic (required by BaseAgent).
        
        Args:
            **kwargs: Additional parameters (currently unused)
        
        Returns:
            Dictionary with extracted company profile
        """
        return self.extract_company_profile()
    
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
            
            # Parse as JSON list for list fields
            if key in ['pain_points', 'interests']:
                audience[key] = self._parse_json_list(content)
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
            
            # Parse as JSON list
            business[key] = self._parse_json_list(content)
            
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

