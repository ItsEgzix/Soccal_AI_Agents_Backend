"""
Repository for fetching prompts from database.

Provides a clean abstraction for prompt-related database operations,
making it easy to fetch prompts by ID and manage prompt data.
"""
from typing import List, Dict, Optional
from .connection import DatabaseConnection


class PromptRepository:
    """
    Handles all prompt-related database operations.
    
    Provides methods to fetch prompts from both draft_prompts and
    published_prompts tables, returning them in a convenient format.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize prompt repository.
        
        Args:
            db_connection: Database connection manager
        """
        self.db = db_connection
    
    def fetch_prompts_by_ids(
        self, 
        prompt_ids: List[str], 
        use_draft: bool = False
    ) -> Dict[str, str]:
        """
        Fetch prompts by IDs and return name->content mapping.
        
        Args:
            prompt_ids: List of prompt UUIDs to fetch
            use_draft: If True, fetch from draft_prompts table, else published_prompts
            
        Returns:
            Dictionary mapping prompt name to content string
            Example: {'basic_info': 'Prompt content here...', ...}
            
        Raises:
            ValueError: If prompt_ids is empty
            psycopg2.Error: If database query fails
        """
        if not prompt_ids:
            return {}
        
        table = "draft_prompts" if use_draft else "published_prompts"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, name, content FROM {table} WHERE id = ANY(%s::uuid[])",
                (prompt_ids,)
            )
            
            prompt_map = {}
            for row in cursor.fetchall():
                prompt_map[row[1]] = row[2]  # name -> content
            
            return prompt_map
    
    def fetch_prompt_by_name(
        self,
        prompt_name: str,
        use_draft: bool = False
    ) -> Optional[str]:
        """
        Fetch a single prompt by name.
        
        Args:
            prompt_name: Name of the prompt to fetch
            use_draft: If True, fetch from draft_prompts, else published_prompts
            
        Returns:
            Prompt content string, or None if not found
        """
        table = "draft_prompts" if use_draft else "published_prompts"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT content FROM {table} WHERE name = %s LIMIT 1",
                (prompt_name,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

