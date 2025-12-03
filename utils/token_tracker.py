"""
Token Usage Tracker
Tracks token usage across all LLM calls in a request.
Supports both OpenAI and Google Gemini.
"""

from typing import Dict, Optional, Any
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
        self.llm_calls += 1
        
        # Try to get token usage from llm_output
        if response.llm_output:
            token_usage = self._extract_token_usage(response.llm_output)
            if token_usage:
                self.total_prompt_tokens += token_usage.get('prompt_tokens', 0)
                self.total_completion_tokens += token_usage.get('completion_tokens', 0)
                self.total_tokens += token_usage.get('total_tokens', 0)
                return
        
        # Fallback: try to get from generation metadata
        if response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, 'generation_info') and gen.generation_info:
                        token_usage = self._extract_token_usage(gen.generation_info)
                        if token_usage:
                            self.total_prompt_tokens += token_usage.get('prompt_tokens', 0)
                            self.total_completion_tokens += token_usage.get('completion_tokens', 0)
                            self.total_tokens += token_usage.get('total_tokens', 0)
                            return
                    
                    # Try response_metadata for newer langchain versions
                    if hasattr(gen, 'message') and hasattr(gen.message, 'response_metadata'):
                        meta = gen.message.response_metadata
                        token_usage = self._extract_token_usage(meta)
                        if token_usage:
                            self.total_prompt_tokens += token_usage.get('prompt_tokens', 0)
                            self.total_completion_tokens += token_usage.get('completion_tokens', 0)
                            self.total_tokens += token_usage.get('total_tokens', 0)
                            return
    
    def _extract_token_usage(self, data: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """
        Extract token usage from various response formats.
        
        Supports:
        - OpenAI format: {'token_usage': {'prompt_tokens': X, 'completion_tokens': Y, 'total_tokens': Z}}
        - Gemini format: {'usage_metadata': {'prompt_token_count': X, 'candidates_token_count': Y, 'total_token_count': Z}}
        - Direct format: {'prompt_tokens': X, 'completion_tokens': Y, 'total_tokens': Z}
        """
        if not data:
            return None
        
        # OpenAI format
        if 'token_usage' in data:
            usage = data['token_usage']
            return {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0) or (usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0))
            }
        
        # Gemini format (usage_metadata)
        if 'usage_metadata' in data:
            usage = data['usage_metadata']
            prompt = usage.get('prompt_token_count', 0)
            completion = usage.get('candidates_token_count', 0)
            total = usage.get('total_token_count', 0) or (prompt + completion)
            return {
                'prompt_tokens': prompt,
                'completion_tokens': completion,
                'total_tokens': total
            }
        
        # Direct format (some providers)
        if 'prompt_tokens' in data or 'completion_tokens' in data:
            prompt = data.get('prompt_tokens', 0)
            completion = data.get('completion_tokens', 0)
            total = data.get('total_tokens', 0) or (prompt + completion)
            return {
                'prompt_tokens': prompt,
                'completion_tokens': completion,
                'total_tokens': total
            }
        
        # Gemini direct format
        if 'prompt_token_count' in data or 'candidates_token_count' in data:
            prompt = data.get('prompt_token_count', 0)
            completion = data.get('candidates_token_count', 0)
            total = data.get('total_token_count', 0) or (prompt + completion)
            return {
                'prompt_tokens': prompt,
                'completion_tokens': completion,
                'total_tokens': total
            }
        
        return None
    
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
