"""
Brand Voice Agent

Analyzes Instagram captions to extract brand voice characteristics.
Migrated to use BaseAgent and AgentPathManager.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Any
import json
import sys
from pathlib import Path

# Import core infrastructure
_agents_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_agents_root))
from core.base_agent import BaseAgent
from core.path_manager import AgentPathManager

# Setup imports for this agent
AgentPathManager.setup_imports("company_context", "brand_voice")

# Import team-specific utilities
_team_utils = _agents_root / "teams" / "company_context" / "utils"
sys.path.insert(0, str(_team_utils))
from prompt_loader import PromptLoader


class BrandVoiceAgent(BaseAgent):
    """
    Agent that analyzes brand voice from Instagram captions.
    
    Inherits from BaseAgent for consistent initialization and logging.
    """
    
    @staticmethod
    def _clean_json_response(content: str) -> str:
        """Remove markdown code blocks from LLM response."""
        content = content.strip()
        if content.startswith('```'):
            first_newline = content.find('\n')
            if first_newline != -1:
                content = content[first_newline + 1:]
            if content.endswith('```'):
                content = content[:-3]
        return content.strip()
    
    @staticmethod
    def _parse_json_list(content: str) -> list:
        """Parse JSON list from LLM response, handling markdown code blocks."""
        cleaned = BrandVoiceAgent._clean_json_response(content)
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            return [result] if result else []
        except json.JSONDecodeError:
            lines = cleaned.split('\n')
            items = []
            for line in lines:
                line = line.strip()
                if not line or line in ['[', ']', '{', '}']:
                    continue
                line = line.strip('",').strip("'")
                if line and not line.startswith('```'):
                    items.append(line)
            return items
    
    def __init__(self, llm=None, log_callback=None, token_tracker=None):
        """
        Initialize Brand Voice Agent.
        
        Args:
            llm: LangChain LLM instance (default: from LLMConfig via BaseAgent)
            log_callback: Function to send logs (for WebSocket streaming)
            token_tracker: TokenUsageTracker instance for tracking token usage
        """
        # Initialize base class (handles LLM setup)
        super().__init__(llm=llm, log_callback=log_callback, token_tracker=token_tracker)
    
    def execute(self, captions: List[str], **kwargs) -> Dict[str, Any]:
        """
        Execute agent logic (required by BaseAgent).
        
        Args:
            captions: List of Instagram post captions
            **kwargs: Additional parameters (currently unused)
        
        Returns:
            Dictionary with brand voice data
        """
        return self.analyze_brand_voice(captions)
    
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
        personality_traits = self._parse_json_list(traits_response.content.strip())
        
        return {
            'tone': tone,
            'style_guide': style_guide,
            'examples': examples,
            'personality_traits': personality_traits
        }

