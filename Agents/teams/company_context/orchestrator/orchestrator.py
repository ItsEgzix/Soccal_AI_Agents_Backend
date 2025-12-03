"""
Orchestrator Agent
Coordinates the Company Context Team workflow using LangGraph.
"""

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Optional, Callable
from langgraph.graph import StateGraph, END
import sys
import os
from pathlib import Path
import uuid
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Import from shared LLM config
# orchestrator.py is at: Agents/teams/company_context/orchestrator/orchestrator.py
# So parent.parent.parent.parent = Agents root
_agents_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_agents_root))
from shared.llms.config import LLMConfig

# Import token tracker from backend utils
_backend_root = _agents_root.parent
sys.path.insert(0, str(_backend_root))
from utils.token_tracker import TokenUsageTracker


class CompanyContextState(TypedDict, total=False):
    """State for the company context workflow."""
    company_name: str
    website_url: str
    instagram_account: str
    company_id: str
    website_scraped: bool
    instagram_scraped: bool
    supabase_ready: bool
    instagram_captions: list
    company_context_data: dict
    brand_voice_data: dict
    final_output: dict


class OrchestratorAgent:
    """
    Orchestrator agent that coordinates the workflow.
    """
    
    def __init__(self, llm=None, log_callback=None):
        """
        Initialize orchestrator.
        
        Args:
            llm: LangChain LLM instance (default: from LLMConfig)
            log_callback: Function to send logs (can be sync or async, for WebSocket streaming)
        """
        self.llm = llm or LLMConfig.get_default_llm()
        self.log_callback = log_callback
        self.token_tracker = TokenUsageTracker()
        self.workflow = self._build_workflow()
    
    def set_log_callback(self, callback):
        """Set log callback for real-time streaming."""
        self.log_callback = callback
    
    def _log(self, message: str, log_type: str = "info"):
        """
        Send log message via callback if available, otherwise print.
        Handles both sync and async callbacks from synchronous context.
        
        Args:
            message: Log message
            log_type: Type of log (info, success, error, warning, progress)
        """
        if self.log_callback:
            try:
                # Check if callback has send_log_sync method (queue-based)
                if hasattr(self.log_callback, 'send_log_sync'):
                    self.log_callback.send_log_sync(message, log_type)
                # Check if it's async
                elif asyncio.iscoroutinefunction(self.log_callback):
                    # Try to get running event loop
                    try:
                        loop = asyncio.get_running_loop()
                        # Schedule in running loop
                        asyncio.create_task(self.log_callback(message, log_type))
                    except RuntimeError:
                        # No running loop, use queue if available
                        if hasattr(self.log_callback, 'send_log_sync'):
                            self.log_callback.send_log_sync(message, log_type)
                        else:
                            print(message)
                else:
                    # Sync callback
                    self.log_callback(message, log_type)
            except Exception:
                # Fallback to print if callback fails
                print(message)
        else:
            print(message)
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(CompanyContextState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("scrape_website", self._scrape_website)
        workflow.add_node("scrape_instagram", self._scrape_instagram)
        workflow.add_node("extract_company_context", self._extract_company_context)
        workflow.add_node("extract_brand_voice", self._extract_brand_voice)
        workflow.add_node("compile_output", self._compile_output)
        
        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scrape_website")
        workflow.add_edge("scrape_website", "scrape_instagram")
        workflow.add_edge("scrape_instagram", "extract_company_context")
        workflow.add_edge("extract_company_context", "extract_brand_voice")
        workflow.add_edge("extract_brand_voice", "compile_output")
        workflow.add_edge("compile_output", END)
        
        return workflow.compile()
    
    def _initialize(self, state: CompanyContextState) -> CompanyContextState:
        """Initialize the workflow."""
        import sys
        import os
        
        # Check if company already exists by URL before generating new ID
        # Use new structure paths - calculate Agents root correctly
        # orchestrator.py is at: Agents/teams/company_context/orchestrator/orchestrator.py
        # So parent.parent.parent.parent = Agents root
        _agents_root = Path(__file__).parent.parent.parent.parent
        _tool_path = _agents_root / "teams" / "company_context" / "tools" / "web_scraper"
        if str(_tool_path) not in sys.path:
            sys.path.insert(0, str(_tool_path))
        from scraper import CompanyScraper
        
        scraper = CompanyScraper()
        existing_company_id = scraper.storage.find_company_by_url(state["website_url"])
        
        if existing_company_id:
            # Use existing company_id
            state["company_id"] = existing_company_id
            self._log(f"Found existing company for URL: {state['website_url']}", "success")
            self._log(f"  Using existing Company ID: {state['company_id']}", "info")
        else:
            # Generate new company_id only if not found
            state["company_id"] = str(uuid.uuid4())
            self._log(f"Initialized new workflow for: {state['company_name']}", "success")
            self._log(f"  New Company ID: {state['company_id']}", "info")
        
        state["website_scraped"] = False
        state["instagram_scraped"] = False
        state["supabase_ready"] = False
        state["company_context_data"] = {}
        state["brand_voice_data"] = {}
        state["final_output"] = {}
        
        return state
    
    def _scrape_website(self, state: CompanyContextState) -> CompanyContextState:
        """Scrape website and save to Supabase."""
        # Use new structure paths - calculate Agents root correctly
        _agents_root = Path(__file__).parent.parent.parent.parent
        _tool_path = _agents_root / "teams" / "company_context" / "tools" / "web_scraper"
        if str(_tool_path) not in sys.path:
            sys.path.insert(0, str(_tool_path))
        from scraper import CompanyScraper
        
        try:
            scraper = CompanyScraper()
            results = scraper.scrape_and_save(
                base_url=state["website_url"],
                company_name=state["company_name"],
                company_id=state["company_id"]  # Use the ID from initialization (existing or new)
            )
            
            state["website_scraped"] = True
            state["supabase_ready"] = True
            self._log(f"Website scraped and saved to Supabase", "success")
            
        except Exception as e:
            self._log(f"✗ Error scraping website: {str(e)}", "error")
            state["website_scraped"] = False
        
        return state
    
    def _scrape_instagram(self, state: CompanyContextState) -> CompanyContextState:
        """Scrape Instagram and get captions."""
        # Use new structure paths - calculate Agents root correctly
        _agents_root = Path(__file__).parent.parent.parent.parent
        _tool_path = _agents_root / "teams" / "company_context" / "tools" / "instagram_scraper"
        if str(_tool_path) not in sys.path:
            sys.path.insert(0, str(_tool_path))
        from instagram_scraper import InstagramScraper
        
        try:
            scraper = InstagramScraper()
            captions = scraper.scrape_posts(state["instagram_account"], limit=5)
            
            state["instagram_scraped"] = True
            state["instagram_captions"] = captions
            self._log(f"Instagram scraped: {len(captions)} captions extracted", "success")
            
        except Exception as e:
            self._log(f"✗ Error scraping Instagram: {str(e)}", "error")
            state["instagram_scraped"] = False
            state["instagram_captions"] = []
        
        return state
    
    def _extract_company_context(self, state: CompanyContextState) -> CompanyContextState:
        """Extract company context from Supabase."""
        # Use new structure paths - calculate Agents root correctly
        _agents_root = Path(__file__).parent.parent.parent.parent
        _agent_path = _agents_root / "teams" / "company_context" / "agents" / "company_context"
        if str(_agent_path) not in sys.path:
            sys.path.insert(0, str(_agent_path))
        
        # Import using importlib to avoid conflicts
        import importlib.util
        agent_path = _agent_path / "agent.py"
        spec = importlib.util.spec_from_file_location("company_context_agent", str(agent_path))
        company_context_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(company_context_module)
        CompanyContextAgent = company_context_module.CompanyContextAgent
        
        if not state["supabase_ready"]:
            self._log("✗ Supabase not ready, skipping context extraction", "warning")
            return state
        
        try:
            agent = CompanyContextAgent(
                company_id=state["company_id"], 
                log_callback=self.log_callback,
                token_tracker=self.token_tracker
            )
            context_data = agent.extract_company_profile()
            
            state["company_context_data"] = context_data
            self._log(f"Company context extracted", "success")
            
        except Exception as e:
            self._log(f"✗ Error extracting company context: {str(e)}", "error")
            state["company_context_data"] = {}
        
        return state
    
    def _extract_brand_voice(self, state: CompanyContextState) -> CompanyContextState:
        """Extract brand voice from Instagram captions."""
        # Use new structure paths - calculate Agents root correctly
        _agents_root = Path(__file__).parent.parent.parent.parent
        _agent_path = _agents_root / "teams" / "company_context" / "agents" / "brand_voice"
        if str(_agent_path) not in sys.path:
            sys.path.insert(0, str(_agent_path))
        
        # Import using importlib to avoid conflicts
        import importlib.util
        agent_path = _agent_path / "agent.py"
        spec = importlib.util.spec_from_file_location("brand_voice_agent", str(agent_path))
        brand_voice_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(brand_voice_module)
        BrandVoiceAgent = brand_voice_module.BrandVoiceAgent
        
        if not state.get("instagram_scraped") or not state.get("instagram_captions"):
            self._log("✗ Instagram not scraped, skipping brand voice extraction", "warning")
            return state
        
        try:
            agent = BrandVoiceAgent(
                log_callback=self.log_callback,
                token_tracker=self.token_tracker
            )
            brand_voice_data = agent.analyze_brand_voice(state["instagram_captions"])
            
            state["brand_voice_data"] = brand_voice_data
            self._log(f"Brand voice extracted", "success")
            
        except Exception as e:
            self._log(f"✗ Error extracting brand voice: {str(e)}", "error")
            state["brand_voice_data"] = {}
        
        return state
    
    def _compile_output(self, state: CompanyContextState) -> CompanyContextState:
        """Compile final JSON output."""
        final_output = {
            "company_name": state["company_name"],
            "company_id": state["company_id"],
            "website_url": state["website_url"],
            "instagram_account": state["instagram_account"],
            "company_profile": {
                "basic_info": state["company_context_data"].get("basic_info", {}),
                "target_audience": state["company_context_data"].get("target_audience", {}),
                "business_context": state["company_context_data"].get("business_context", {}),
                "content_mix": state["company_context_data"].get("content_mix", ""),
                "brand_voice": state["brand_voice_data"],
            }
        }
        
        state["final_output"] = final_output
        self._log(f"Final output compiled", "success")
        
        return state
    
    def process(self, company_name: str, website_url: str, instagram_account: str) -> dict:
        """
        Process company context request.
        
        Args:
            company_name: Company name
            website_url: Website URL
            instagram_account: Instagram account (without @)
        
        Returns:
            Final JSON output with company profile and usage stats
        """
        # Reset token tracker for new request
        self.token_tracker.reset()
        
        # Start timing
        start_time = time.time()
        
        initial_state = {
            "company_name": company_name,
            "website_url": website_url,
            "instagram_account": instagram_account.replace('@', '').strip()
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get token usage
        token_usage = self.token_tracker.get_usage()
        
        # Add usage stats to final output
        final_output = final_state["final_output"]
        final_output["usage_stats"] = {
            "processing_time_seconds": round(processing_time, 2),
            "token_usage": token_usage
        }
        
        return final_output

