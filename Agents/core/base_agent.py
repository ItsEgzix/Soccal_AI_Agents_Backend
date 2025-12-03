"""
Base Agent Class

All agents MUST inherit from this class.
Provides common functionality and ensures consistency across all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import sys
from pathlib import Path

# Add shared utils to path for LLM config
_agents_root = Path(__file__).parent.parent
if str(_agents_root) not in sys.path:
    sys.path.insert(0, str(_agents_root))

try:
    from shared.llms.config import LLMConfig
except ImportError:
    # Fallback if shared utils not yet migrated
    _old_utils = _agents_root.parent / "utils" / "llms"
    if _old_utils.exists():
        if str(_old_utils.parent) not in sys.path:
            sys.path.insert(0, str(_old_utils.parent))
        from llms.config import LLMConfig
    else:
        raise ImportError("Could not import LLMConfig from shared.llms.config or utils.llms.config")


class BaseAgent(ABC):
    """
    Base class for all AI agents.
    
    Every agent should inherit from this to ensure:
    - Consistent initialization
    - Standardized logging
    - Common LLM setup
    - Token tracking
    - Error handling
    
    Usage:
        class MyAgent(BaseAgent):
            def execute(self, **kwargs) -> Dict[str, Any]:
                # Your agent logic here
                return result
    """
    
    def __init__(
        self,
        llm=None,
        log_callback: Optional[Callable] = None,
        token_tracker=None,
        **kwargs
    ):
        """
        Initialize base agent.
        
        Args:
            llm: Optional LLM instance (defaults to LLMConfig)
            log_callback: Optional logging callback function
            token_tracker: Optional token usage tracker instance
            **kwargs: Additional agent-specific parameters
        """
        self.token_tracker = token_tracker
        self.log_callback = log_callback
        
        # Standardized LLM initialization
        if token_tracker:
            self.llm = LLMConfig.get_llm_with_callbacks(
                callbacks=[token_tracker]
            )
        else:
            self.llm = llm or LLMConfig.get_default_llm()
    
    def _log(self, message: str, log_type: str = "info") -> None:
        """
        Standardized logging across all agents.
        
        Args:
            message: Log message
            log_type: Log type (info, warning, error, success)
        """
        agent_name = self.__class__.__name__
        formatted_message = f"[{agent_name}] {message}"
        
        if self.log_callback:
            try:
                if hasattr(self.log_callback, 'send_log_sync'):
                    self.log_callback.send_log_sync(formatted_message, log_type)
                elif callable(self.log_callback):
                    self.log_callback(formatted_message, log_type)
                else:
                    print(formatted_message)
            except Exception as e:
                # Fallback to print if callback fails
                print(f"{formatted_message} (callback error: {e})")
        else:
            print(formatted_message)
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        This is the main entry point for agent execution.
        Must be implemented by each agent subclass.
        
        Args:
            **kwargs: Agent-specific input parameters
        
        Returns:
            Dictionary with agent execution results
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Override in subclasses to add custom validation.
        This method is called before execute() to ensure inputs are valid.
        
        Args:
            **kwargs: Input parameters to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        return True
    
    def get_token_usage(self) -> Optional[Dict[str, int]]:
        """
        Get token usage statistics if token tracker is available.
        
        Returns:
            Dictionary with token usage or None if no tracker
        """
        if self.token_tracker and hasattr(self.token_tracker, 'get_usage'):
            return self.token_tracker.get_usage()
        return None

