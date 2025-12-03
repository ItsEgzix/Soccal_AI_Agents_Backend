"""
Token Usage Tracker
Tracks token usage across all LLM calls in a request.
"""

from typing import Dict, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenUsageTracker(BaseCallbackHandler):
    """Callback handler to track token usage from LLM calls."""
    
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.llm_calls = 0
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM finishes."""
        if response.llm_output and 'token_usage' in response.llm_output:
            token_usage = response.llm_output['token_usage']
            
            # Handle different token usage formats
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            
            # If total_tokens is not provided, calculate it
            if total_tokens == 0:
                total_tokens = prompt_tokens + completion_tokens
            
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            self.llm_calls += 1
    
    def get_usage(self) -> Dict:
        """Get current token usage statistics."""
        return {
            'prompt_tokens': self.total_prompt_tokens,
            'completion_tokens': self.total_completion_tokens,
            'total_tokens': self.total_tokens,
            'llm_calls': self.llm_calls
        }
    
    def reset(self):
        """Reset all counters."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.llm_calls = 0

