"""
Tester for Brand Voice Agent.

Handles testing of the Brand Voice Agent with Instagram scraping
and prompt management.
"""
import time
from typing import Dict, Any, List
from .base_tester import BaseAgentTester
from ..config.paths import PathManager


class BrandVoiceTester(BaseAgentTester):
    """Tests Brand Voice Agent."""
    
    def test(
        self,
        prompt_ids: List[str],
        use_draft: bool,
        test_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test Brand Voice Agent.
        
        Args:
            prompt_ids: List of prompt UUIDs to use
            use_draft: Whether to use draft prompts
            test_variables: Must contain 'instagram_account' or 'instagram_captions'
            
        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        
        try:
            # 1. Get Instagram captions
            instagram_captions = test_variables.get("instagram_captions")
            instagram_account = test_variables.get("instagram_account")
            
            if instagram_account and not instagram_captions:
                print(f"[BrandVoiceTester] Scraping Instagram account: {instagram_account}")
                instagram_captions = self.scraper_service.scrape_instagram(
                    instagram_account,
                    limit=5
                )
            
            if not instagram_captions:
                raise ValueError(
                    "Either instagram_account or instagram_captions must be provided"
                )
            
            # 2. Fetch and override prompts
            self._fetch_and_override_prompts(prompt_ids, use_draft)
            
            try:
                # 3. Import and run agent
                agents_path = PathManager.get_agents_dir()
                PathManager.add_to_sys_path(agents_path)
                
                from Brand_Voice_Agent.agent import BrandVoiceAgent
                
                print(f"[BrandVoiceTester] Starting agent execution with {len(instagram_captions)} captions")
                agent = BrandVoiceAgent()
                result = agent.analyze_brand_voice(instagram_captions)
                print(f"[BrandVoiceTester] Agent execution completed successfully")
                
                execution_time = time.time() - start_time
                
                return self._create_result(
                    success=True,
                    agent_name='Brand_Voice_Agent',
                    result=result,
                    execution_time=execution_time
                )
            finally:
                # Always restore prompts, even on error
                self._restore_prompts()
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._restore_prompts()
            
            error_msg = str(e)
            print(f"[BrandVoiceTester] ERROR: {error_msg}")
            import traceback
            print(f"[BrandVoiceTester] Traceback: {traceback.format_exc()}")
            
            return self._create_result(
                success=False,
                agent_name='Brand_Voice_Agent',
                error=error_msg,
                execution_time=execution_time
            )

