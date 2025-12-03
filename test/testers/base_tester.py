"""
Base class for all agent testers.

Provides common functionality and defines the interface that all
testers must implement, ensuring consistency across different agent types.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
from ..database.prompt_repository import PromptRepository
from ..services.scraper_service import ScraperService
from ..services.prompt_service import PromptService


class BaseAgentTester(ABC):
    """
    Abstract base class for agent testing.
    
    Provides common functionality like result formatting, timing,
    and prompt management. Subclasses implement agent-specific logic.
    """
    
    def __init__(
        self,
        prompt_repository: PromptRepository,
        scraper_service: ScraperService,
        prompt_service: PromptService
    ):
        """
        Initialize base tester.
        
        Args:
            prompt_repository: Repository for fetching prompts
            scraper_service: Service for scraping operations
            prompt_service: Service for prompt loading/overriding
        """
        self.prompt_repo = prompt_repository
        self.scraper_service = scraper_service
        self.prompt_service = prompt_service
    
    @abstractmethod
    def test(
        self,
        prompt_ids: List[str],
        use_draft: bool,
        test_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the test and return results.
        
        Args:
            prompt_ids: List of prompt UUIDs to use
            use_draft: Whether to use draft prompts
            test_variables: Test input variables
            
        Returns:
            Dictionary with test results containing:
            - success: bool
            - result: Any (agent-specific result)
            - error: str or None
            - executionTime: float
        """
        pass
    
    def _create_result(
        self,
        success: bool,
        agent_name: str,
        result: Any = None,
        error: str = None,
        execution_time: float = None
    ) -> Dict[str, Any]:
        """
        Create standardized result dictionary.
        
        Args:
            success: Whether test succeeded
            agent_name: Name of the agent being tested
            result: Agent result data
            error: Error message if failed
            execution_time: Test execution time in seconds
            
        Returns:
            Standardized result dictionary
        """
        return {
            'success': success,
            'agent': agent_name,
            'result': result,
            'error': error,
            'executionTime': execution_time or 0
        }
    
    def _fetch_and_override_prompts(
        self,
        prompt_ids: List[str],
        use_draft: bool
    ) -> None:
        """
        Fetch prompts and override PromptLoader.
        
        Args:
            prompt_ids: List of prompt UUIDs
            use_draft: Whether to use draft prompts
        """
        if not prompt_ids:
            raise ValueError(
                f"No prompt IDs provided for {'draft' if use_draft else 'published'} prompts"
            )
        
        # Fetch prompts from database
        prompt_map = self.prompt_repo.fetch_prompts_by_ids(prompt_ids, use_draft)
        
        if not prompt_map:
            raise ValueError(
                f"No prompts found for the provided IDs. "
                f"Check if prompt IDs are correct."
            )
        
        # Override PromptLoader to use fetched prompts
        self.prompt_service.override_with_prompts(prompt_map, use_draft)
    
    def _restore_prompts(self) -> None:
        """Restore original PromptLoader method."""
        self.prompt_service.restore_original()

