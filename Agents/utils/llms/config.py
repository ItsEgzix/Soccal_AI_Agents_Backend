"""
LLM Configuration
Centralized configuration for all LLM instances across the system.
"""

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from typing import Optional, List
import os


class LLMConfig:
    """Centralized LLM configuration."""
    
    # Default model settings
    DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    DEFAULT_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000")) if os.getenv("OPENAI_MAX_TOKENS") else None
    
    @staticmethod
    def get_default_llm() -> ChatOpenAI:
        """
        Get default LLM instance with standard configuration.
        
        Returns:
            ChatOpenAI instance with default settings
        """
        kwargs = {
            "model": LLMConfig.DEFAULT_MODEL,
            "temperature": LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = LLMConfig.DEFAULT_MAX_TOKENS
        
        return ChatOpenAI(**kwargs)
    
    @staticmethod
    def get_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatOpenAI:
        """
        Get LLM instance with custom configuration.
        
        Args:
            model: Model name (default: from config)
            temperature: Temperature setting (default: from config)
            max_tokens: Max tokens (default: from config)
        
        Returns:
            ChatOpenAI instance
        """
        kwargs = {
            "model": model or LLMConfig.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if max_tokens or LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = max_tokens or LLMConfig.DEFAULT_MAX_TOKENS
        
        return ChatOpenAI(**kwargs)
    
    @staticmethod
    def get_llm_with_callbacks(
        callbacks: Optional[List] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatOpenAI:
        """
        Get LLM instance with callbacks for token tracking.
        
        Args:
            callbacks: List of callback handlers
            model: Model name (default: from config)
            temperature: Temperature setting (default: from config)
            max_tokens: Max tokens (default: from config)
        
        Returns:
            ChatOpenAI instance with callbacks
        """
        kwargs = {
            "model": model or LLMConfig.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if max_tokens or LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = max_tokens or LLMConfig.DEFAULT_MAX_TOKENS
        
        if callbacks:
            kwargs["callbacks"] = callbacks
        
        return ChatOpenAI(**kwargs)

