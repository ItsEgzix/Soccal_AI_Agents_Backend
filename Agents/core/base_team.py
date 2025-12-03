"""
Base Team Class

Teams coordinate multiple agents to accomplish complex tasks.
All teams should inherit from this class for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class BaseTeam(ABC):
    """
    Base class for all agent teams.
    
    Teams orchestrate multiple agents to accomplish complex workflows.
    Examples: Company Context Team (extracts company info + brand voice)
    
    Usage:
        class MyTeam(BaseTeam):
            def execute(self, **kwargs) -> Dict[str, Any]:
                # Orchestrate agents
                result1 = self.agent1.execute(...)
                result2 = self.agent2.execute(...)
                return combined_result
    """
    
    def __init__(self, **kwargs):
        """
        Initialize team.
        
        Args:
            **kwargs: Team-specific configuration
        """
        self.config = kwargs
        self.agents: Dict[str, BaseAgent] = {}
        self._initialized = False
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute team workflow.
        
        Must be implemented by each team subclass.
        This method orchestrates multiple agents to accomplish a task.
        
        Args:
            **kwargs: Team-specific input parameters
        
        Returns:
            Dictionary with team execution results
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent with the team.
        
        Args:
            name: Agent name/identifier
            agent: Agent instance
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Agent must be an instance of BaseAgent, got {type(agent)}")
        self.agents[name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get a registered agent by name.
        
        Args:
            name: Agent name/identifier
        
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys())
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate team input parameters.
        
        Override in subclasses to add custom validation.
        
        Args:
            **kwargs: Input parameters to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        return True

