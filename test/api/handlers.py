"""
Request handlers for test API.

Contains business logic for handling test requests,
separated from route definitions for better testability.
"""
import time
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ..testers.factory import TesterFactory
from ..database.test_result_repository import TestResultRepository
from ..database.connection import DatabaseConnection
from ..config.settings import DatabaseConfig, TestConfig
from .models import CompareRequest


class TestHandler:
    """
    Handles test requests.
    
    Orchestrates test execution, result formatting, and persistence.
    """
    
    def __init__(self, executor: ThreadPoolExecutor = None):
        """
        Initialize test handler.
        
        Args:
            executor: Thread pool executor for running tests (optional)
        """
        self.factory = TesterFactory()
        self.executor = executor or ThreadPoolExecutor(
            max_workers=TestConfig.from_env().max_workers
        )
        
        # Setup test result repository
        db_config = DatabaseConfig.from_env()
        db_connection = DatabaseConnection(db_config)
        self.result_repo = TestResultRepository(db_connection)
    
    async def compare_agents(self, request: CompareRequest) -> Dict[str, Any]:
        """
        Compare draft vs published prompts.
        
        Args:
            request: Comparison request with agent name, prompt IDs, and test variables
            
        Returns:
            Dictionary with comparison results
        """
        start_time = time.time()
        
        print(f"[TestHandler] Received test request: agent={request.agentName}, "
              f"draft_ids={len(request.draftPromptIds)}, "
              f"published_ids={len(request.publishedPromptIds)}")
        
        # Validate
        if not request.draftPromptIds and not request.publishedPromptIds:
            raise ValueError(
                "At least one prompt ID (draft or published) must be provided"
            )
        
        # Get appropriate tester
        tester = self.factory.create(request.agentName)
        
        # Run tests sequentially to avoid database conflicts
        loop = asyncio.get_event_loop()
        test_vars = request.testVariables or {}
        
        # Run draft test
        print(f"[TestHandler] Starting draft test...")
        draft_result = await loop.run_in_executor(
            self.executor,
            tester.test,
            request.draftPromptIds if request.draftPromptIds else request.publishedPromptIds,
            True,  # use_draft
            test_vars
        )
        print(f"[TestHandler] Draft test completed: success={draft_result.get('success')}")
        
        # Run published test
        print(f"[TestHandler] Starting published test...")
        published_result = await loop.run_in_executor(
            self.executor,
            tester.test,
            request.publishedPromptIds if request.publishedPromptIds else request.draftPromptIds,
            False,  # use_draft
            test_vars
        )
        print(f"[TestHandler] Published test completed: success={published_result.get('success')}")
        
        # Format results
        overall_success = draft_result.get('success') and published_result.get('success')
        execution_time = time.time() - start_time
        
        results_for_db = {
            'draft': draft_result,
            'published': published_result
        }
        
        # Save to database (non-blocking)
        test_result_id = None
        try:
            test_result_id = self.result_repo.save_test_result(
                published_prompt_ids=request.publishedPromptIds,
                draft_prompt_ids=request.draftPromptIds,
                test_variables=test_vars,
                results=results_for_db,
                success=overall_success,
                admin_id=request.adminId
            )
        except Exception as save_error:
            print(f"[TestHandler] Warning: Failed to save test result: {save_error}")
        
        # Return formatted response
        return {
            "testResultId": test_result_id,
            "success": overall_success,
            "agent": request.agentName,
            "draftResult": draft_result,
            "publishedResult": published_result,
            "executionTime": execution_time,
            "comparison": {
                "draftResult": draft_result,
                "publishedResult": published_result,
                "draftSuccess": draft_result.get("success", False),
                "publishedSuccess": published_result.get("success", False),
                "draftExecutionTime": draft_result.get("executionTime", 0),
                "publishedExecutionTime": published_result.get("executionTime", 0),
                "timeDifference": abs(
                    draft_result.get("executionTime", 0) - 
                    published_result.get("executionTime", 0)
                )
            }
        }

