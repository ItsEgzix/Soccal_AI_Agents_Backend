"""
Factory for creating agent testers.

Provides a simple way to create the appropriate tester based on agent name,
handling all the dependency injection internally.
"""
from typing import Dict
from .base_tester import BaseAgentTester
from .company_context_tester import CompanyContextTester
from .brand_voice_tester import BrandVoiceTester
from .full_workflow_tester import FullWorkflowTester
from ..database.connection import DatabaseConnection
from ..database.prompt_repository import PromptRepository
from ..services.scraper_service import ScraperService
from ..services.prompt_service import PromptService
from ..config.settings import DatabaseConfig


class TesterFactory:
    """
    Factory for creating agent testers.
    
    Handles dependency injection and configuration, making it easy
    to create testers without worrying about setup.
    """
    
    def __init__(self):
        """Initialize factory with shared dependencies."""
        # Load configuration
        db_config = DatabaseConfig.from_env()
        
        # Create shared services
        self.db_connection = DatabaseConnection(db_config)
        self.prompt_repo = PromptRepository(self.db_connection)
        self.scraper_service = ScraperService()
        self.prompt_service = PromptService()
    
    def create(self, agent_name: str) -> BaseAgentTester:
        """
        Create a tester for the specified agent.
        
        Args:
            agent_name: Name of the agent ('Company_Context_Agent', 
                       'Brand_Voice_Agent', or 'full_workflow')
        
        Returns:
            Appropriate tester instance
            
        Raises:
            ValueError: If agent_name is not recognized
        """
        # Shared dependencies
        dependencies = (
            self.prompt_repo,
            self.scraper_service,
            self.prompt_service
        )
        
        # Create appropriate tester
        if agent_name == "Company_Context_Agent":
            return CompanyContextTester(*dependencies)
        elif agent_name == "Brand_Voice_Agent":
            return BrandVoiceTester(*dependencies)
        elif agent_name == "full_workflow":
            return FullWorkflowTester(*dependencies)
        else:
            raise ValueError(f"Unknown agent name: {agent_name}")

