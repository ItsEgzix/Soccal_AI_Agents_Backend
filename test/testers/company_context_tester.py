"""
Tester for Company Context Agent.

Handles testing of the Company Context Agent with proper setup,
prompt management, and result formatting.
"""
import time
from typing import Dict, Any, List
from .base_tester import BaseAgentTester
from ..config.paths import PathManager


class CompanyContextTester(BaseAgentTester):
    """Tests Company Context Agent."""
    
    def test(
        self,
        prompt_ids: List[str],
        use_draft: bool,
        test_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test Company Context Agent.
        
        Args:
            prompt_ids: List of prompt UUIDs to use
            use_draft: Whether to use draft prompts
            test_variables: Must contain 'website_url' or 'company_id'
            
        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        
        try:
            # 1. Ensure company exists
            website_url = test_variables.get("website_url")
            company_id = test_variables.get("company_id")
            
            if website_url:
                company_id = self.scraper_service.ensure_company_exists(website_url)
            elif not company_id:
                raise ValueError("Either website_url or company_id must be provided")
            
            # 2. Fetch and override prompts
            self._fetch_and_override_prompts(prompt_ids, use_draft)
            
            try:
                # 3. Import and run agent
                agents_root = PathManager.get_project_root() / "Agents"
                PathManager.add_to_sys_path(agents_root)
                
                from teams.company_context.agents.company_context.agent import CompanyContextAgent
                
                print(f"[CompanyContextTester] Starting agent execution with company_id: {company_id}")
                agent = CompanyContextAgent(company_id=company_id)
                result = agent.execute()  # Use execute() method from BaseAgent
                print(f"[CompanyContextTester] Agent execution completed successfully")
                
                execution_time = time.time() - start_time
                
                return self._create_result(
                    success=True,
                    agent_name='Company_Context_Agent',
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
            print(f"[CompanyContextTester] ERROR: {error_msg}")
            import traceback
            print(f"[CompanyContextTester] Traceback: {traceback.format_exc()}")
            
            return self._create_result(
                success=False,
                agent_name='Company_Context_Agent',
                error=error_msg,
                execution_time=execution_time
            )

