"""
LLM Configuration
Centralized configuration for all LLM instances across the system.
Supports both OpenAI and Google Gemini.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List, Union
import os

# Determine which provider to use
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # 'openai' or 'gemini'

if LLM_PROVIDER == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI as ChatLLM
    DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
else:
    from langchain_openai import ChatOpenAI as ChatLLM
    DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


class LLMConfig:
    """Centralized LLM configuration."""
    
    # Default model settings
    PROVIDER = LLM_PROVIDER
    DEFAULT_MODEL = DEFAULT_MODEL
    DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", os.getenv("OPENAI_TEMPERATURE", "0")))
    DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", os.getenv("OPENAI_MAX_TOKENS", "2000"))) if os.getenv("LLM_MAX_TOKENS") or os.getenv("OPENAI_MAX_TOKENS") else None
    
    @staticmethod
    def get_default_llm() -> ChatLLM:
        """
        Get default LLM instance with standard configuration.
        
        Returns:
            ChatLLM instance with default settings
        """
        kwargs = {
            "model": LLMConfig.DEFAULT_MODEL,
            "temperature": LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = LLMConfig.DEFAULT_MAX_TOKENS
        
        return ChatLLM(**kwargs)
    
    @staticmethod
    def get_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatLLM:
        """
        Get LLM instance with custom configuration.
        
        Args:
            model: Model name (default: from config)
            temperature: Temperature setting (default: from config)
            max_tokens: Max tokens (default: from config)
        
        Returns:
            ChatLLM instance
        """
        kwargs = {
            "model": model or LLMConfig.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if max_tokens or LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = max_tokens or LLMConfig.DEFAULT_MAX_TOKENS
        
        return ChatLLM(**kwargs)
    
    @staticmethod
    def get_llm_with_callbacks(
        callbacks: Optional[List] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatLLM:
        """
        Get LLM instance with callbacks for token tracking.
        
        Args:
            callbacks: List of callback handlers
            model: Model name (default: from config)
            temperature: Temperature setting (default: from config)
            max_tokens: Max tokens (default: from config)
        
        Returns:
            ChatLLM instance with callbacks
        """
        kwargs = {
            "model": model or LLMConfig.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else LLMConfig.DEFAULT_TEMPERATURE
        }
        
        if max_tokens or LLMConfig.DEFAULT_MAX_TOKENS:
            kwargs["max_tokens"] = max_tokens or LLMConfig.DEFAULT_MAX_TOKENS
        
        if callbacks:
            kwargs["callbacks"] = callbacks
        
        return ChatLLM(**kwargs)
