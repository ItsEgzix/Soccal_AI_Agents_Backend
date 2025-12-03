"""
Base Tool Class

All tools should inherit from this class for consistency.
Tools are reusable components used by agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Tools are reusable components that agents use to perform specific tasks.
    Examples: web scrapers, image processors, API clients, etc.
    
    Usage:
        class MyTool(BaseTool):
            def execute(self, **kwargs) -> Any:
                # Your tool logic here
                return result
    """
    
    def __init__(self, **kwargs):
        """
        Initialize tool with configuration.
        
        Args:
            **kwargs: Tool-specific configuration parameters
        """
        self.config = kwargs
        self._initialized = True
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute tool operation.
        
        Must be implemented by each tool subclass.
        
        Args:
            **kwargs: Tool-specific input parameters
        
        Returns:
            Tool execution result (type depends on tool)
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
    
    def validate(self, **kwargs) -> bool:
        """
        Validate tool inputs.
        
        Override in subclasses to add custom validation.
        
        Args:
            **kwargs: Input parameters to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get tool configuration.
        
        Returns:
            Dictionary with tool configuration
        """
        return self.config.copy()
    
    def update_config(self, **kwargs) -> None:
        """
        Update tool configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)

