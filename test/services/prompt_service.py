"""
Service for prompt loading and overriding.

Handles the complex logic of overriding PromptLoader methods
to inject test prompts during agent execution.
"""
from typing import Dict, Optional
from ..config.paths import PathManager


class PromptService:
    """
    Manages prompt loading and overriding for testing.
    
    Provides methods to temporarily override PromptLoader to use
    test prompts instead of fetching from database during agent execution.
    """
    
    def __init__(self):
        """Initialize prompt service."""
        self._original_method = None
        self._is_overridden = False
    
    def _get_prompt_loader(self):
        """Get PromptLoader class (lazy import)."""
        utils_path = PathManager.get_utils_path()
        PathManager.add_to_sys_path(utils_path)
        
        from prompt_loader import PromptLoader
        return PromptLoader
    
    def override_with_prompts(
        self,
        prompt_map: Dict[str, str],
        use_draft: bool = False
    ) -> None:
        """
        Override PromptLoader to use provided prompts.
        
        Args:
            prompt_map: Dictionary mapping prompt name to content
            use_draft: Whether to use draft prompts (for fallback)
        """
        PromptLoader = self._get_prompt_loader()
        
        # Save original method if not already saved
        if self._original_method is None:
            self._original_method = PromptLoader.load_prompt_from_agent_dir
        
        # Create override function
        def override_load_prompt(agent_dir: str, prompt_name: str, **kwargs) -> str:
            """
            Override to use prompts from prompt_map.
            
            If prompt not in map, falls back to database lookup.
            """
            if prompt_name in prompt_map:
                prompt_template = prompt_map[prompt_name]
                # Format with provided variables
                if kwargs:
                    try:
                        return prompt_template.format(**kwargs)
                    except KeyError as ke:
                        missing_var = str(ke).strip("'\"")
                        raise Exception(
                            f"Missing required placeholder variable: '{missing_var}'. "
                            f"Provided variables: {list(kwargs.keys())}"
                        )
                return prompt_template
            else:
                # Fallback to database lookup by name
                if use_draft:
                    return PromptLoader.load_draft_prompt_from_database(prompt_name, **kwargs)
                else:
                    return PromptLoader.load_prompt_from_database(prompt_name, **kwargs)
        
        # Apply override
        PromptLoader.load_prompt_from_agent_dir = staticmethod(override_load_prompt)
        self._is_overridden = True
    
    def restore_original(self) -> None:
        """Restore original PromptLoader method."""
        if self._is_overridden and self._original_method is not None:
            PromptLoader = self._get_prompt_loader()
            PromptLoader.load_prompt_from_agent_dir = self._original_method
            self._is_overridden = False

