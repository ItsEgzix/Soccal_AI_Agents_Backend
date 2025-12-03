"""
Tester for full workflow (both agents).

Orchestrates testing of both Company Context and Brand Voice agents
in sequence, combining their results.
"""
import time
from typing import Dict, Any, List
from .base_tester import BaseAgentTester
from .company_context_tester import CompanyContextTester
from .brand_voice_tester import BrandVoiceTester


class FullWorkflowTester(BaseAgentTester):
    """Tests full workflow (both agents together)."""
    
    def __init__(self, *args, **kwargs):
        """Initialize full workflow tester with sub-testers."""
        super().__init__(*args, **kwargs)
        self.company_tester = CompanyContextTester(*args, **kwargs)
        self.brand_tester = BrandVoiceTester(*args, **kwargs)
    
    def test(
        self,
        prompt_ids: List[str],
        use_draft: bool,
        test_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test full workflow (both agents).
        
        Args:
            prompt_ids: List of prompt UUIDs to use (for both agents)
            use_draft: Whether to use draft prompts
            test_variables: Must contain both website_url/company_id and instagram_account/captions
            
        Returns:
            Dictionary with combined test results
        """
        start_time = time.time()
        
        try:
            # Test Company Context Agent
            print(f"[FullWorkflowTester] Testing Company Context Agent...")
            company_result = self.company_tester.test(
                prompt_ids=prompt_ids,
                use_draft=use_draft,
                test_variables=test_variables
            )
            
            # Test Brand Voice Agent
            print(f"[FullWorkflowTester] Testing Brand Voice Agent...")
            brand_result = self.brand_tester.test(
                prompt_ids=prompt_ids,
                use_draft=use_draft,
                test_variables=test_variables
            )
            
            execution_time = time.time() - start_time
            
            return self._create_result(
                success=company_result['success'] and brand_result['success'],
                agent_name='full_workflow',
                result={
                    'company_context': company_result,
                    'brand_voice': brand_result
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_msg = str(e)
            print(f"[FullWorkflowTester] ERROR: {error_msg}")
            import traceback
            print(f"[FullWorkflowTester] Traceback: {traceback.format_exc()}")
            
            return self._create_result(
                success=False,
                agent_name='full_workflow',
                error=error_msg,
                execution_time=execution_time
            )

