"""
Brand Voice Agent
Analyzes Instagram captions to extract brand voice characteristics.
"""

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
import json
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_loader import PromptLoader

# Add LLM config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from llms.config import LLMConfig


class BrandVoiceAgent:
    """
    Agent that analyzes brand voice from Instagram captions.
    """
    
    def __init__(self, llm=None, log_callback=None, token_tracker=None):
        """
        Initialize Brand Voice Agent.
        
        Args:
            llm: LangChain LLM instance (default: from LLMConfig)
            log_callback: Function to send logs (for WebSocket streaming)
            token_tracker: TokenUsageTracker instance for tracking token usage
        """
        self.token_tracker = token_tracker
        
        # Create LLM with callbacks if token_tracker is provided
        if token_tracker:
            self.llm = LLMConfig.get_llm_with_callbacks(callbacks=[token_tracker])
        else:
            self.llm = llm or LLMConfig.get_default_llm()
        
        self.log_callback = log_callback
    
    def _log(self, message: str, log_type: str = "info"):
        """Send log message via callback if available, otherwise print."""
        if self.log_callback:
            try:
                if hasattr(self.log_callback, 'send_log_sync'):
                    self.log_callback.send_log_sync(message, log_type)
                else:
                    print(message)
            except:
                print(message)
        else:
            print(message)
    
    def analyze_brand_voice(self, captions: List[str]) -> Dict:
        """
        Analyze Instagram captions to extract brand voice.
        
        Args:
            captions: List of Instagram post captions
        
        Returns:
            Dictionary with brand voice data
        """
        if not captions:
            return {
                'tone': 'Not available',
                'style_guide': 'Not available',
                'examples': [],
                'personality_traits': []
            }
        
        # Combine all captions
        all_captions = "\n\n".join([f"Caption {i+1}: {caption}" for i, caption in enumerate(captions)])
        
        # Analyze tone
        tone_prompt = PromptLoader.load_prompt_from_agent_dir(
            "Brand_Voice_Agent",
            "tone",
            captions=all_captions
        )
        
        tone_response = self.llm.invoke(tone_prompt)
        tone = tone_response.content.strip()
        
        # Analyze style guide
        style_prompt = PromptLoader.load_prompt_from_agent_dir(
            "Brand_Voice_Agent",
            "style_guide",
            captions=all_captions
        )
        
        style_response = self.llm.invoke(style_prompt)
        style_guide = style_response.content.strip()
        
        # Use actual Instagram captions as examples (not AI-generated)
        examples = captions[:5]  # Use up to 5 captions as examples
        
        # Extract personality traits
        traits_prompt = PromptLoader.load_prompt_from_agent_dir(
            "Brand_Voice_Agent",
            "personality_traits",
            captions=all_captions
        )
        
        traits_response = self.llm.invoke(traits_prompt)
        try:
            personality_traits = json.loads(traits_response.content.strip())
        except:
            personality_traits = []
        
        return {
            'tone': tone,
            'style_guide': style_guide,
            'examples': examples,
            'personality_traits': personality_traits
        }

