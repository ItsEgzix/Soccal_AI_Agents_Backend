"""
Prompt Loader Utility
Loads prompts directly from Supabase database. No fallbacks.
"""

import os
import psycopg2
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PromptLoader:
    """Utility class for loading and formatting prompts from database or files."""
    
    # Database configuration - support both connection string and individual parameters
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_USER = os.getenv("DB_USER") or os.getenv("user")
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("password")
    DB_HOST = os.getenv("DB_HOST") or os.getenv("host")
    DB_PORT = os.getenv("DB_PORT") or os.getenv("port")
    DB_NAME = os.getenv("DB_NAME") or os.getenv("dbname")
    
    USE_DATABASE = os.getenv("USE_PROMPT_DATABASE", "true").lower() == "true"
    
    # Cache for prompts to avoid repeated database calls
    _prompt_cache: dict[str, str] = {}
    _db_connection = None
    
    @staticmethod
    def _get_connection():
        """Get or create database connection."""
        if PromptLoader._db_connection is None or PromptLoader._db_connection.closed:
            # Try connection string first, then individual parameters
            if PromptLoader.DATABASE_URL:
                try:
                    PromptLoader._db_connection = psycopg2.connect(
                        PromptLoader.DATABASE_URL,
                        connect_timeout=10
                    )
                except Exception as e:
                    raise Exception(f"Failed to connect to database: {str(e)}")
            elif PromptLoader.DB_HOST and PromptLoader.DB_USER and PromptLoader.DB_PASSWORD:
                # Use individual parameters
                try:
                    PromptLoader._db_connection = psycopg2.connect(
                        user=PromptLoader.DB_USER,
                        password=PromptLoader.DB_PASSWORD,
                        host=PromptLoader.DB_HOST,
                        port=PromptLoader.DB_PORT or 5432,
                        dbname=PromptLoader.DB_NAME or "postgres",
                        connect_timeout=10
                    )
                except Exception as e:
                    raise Exception(f"Failed to connect to database: {str(e)}")
            else:
                raise Exception("Database connection not configured. Set either DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME in .env")
        
        return PromptLoader._db_connection
    
    @staticmethod
    def load_prompt_from_database(prompt_name: str, **kwargs) -> str:
        """
        Fetch prompt directly from Supabase database and format it with variables.
        
        Args:
            prompt_name: Name of the prompt (e.g., "basic_info", "tone")
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        
        Raises:
            Exception: If database query fails
        """
        # Check cache first
        cache_key = prompt_name
        if cache_key in PromptLoader._prompt_cache:
            prompt_template = PromptLoader._prompt_cache[cache_key]
            # Format with provided variables (only if kwargs provided)
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            return prompt_template
        
        try:
            conn = PromptLoader._get_connection()
            cursor = conn.cursor()
            
            # Query the published_prompts table
            cursor.execute(
                "SELECT content FROM published_prompts WHERE name = %s",
                (prompt_name,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                raise Exception(f"Prompt '{prompt_name}' not found in database")
            
            prompt_template = result[0]
            
            if not prompt_template:
                raise Exception(f"Prompt '{prompt_name}' has empty content in database")
            
            # Cache the template
            PromptLoader._prompt_cache[cache_key] = prompt_template
            
            # Format with provided variables (only if kwargs provided)
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            
            return prompt_template
            
        except psycopg2.Error as e:
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading prompt from database: {str(e)}")
    
    @staticmethod
    def load_prompt_from_database_by_id(prompt_id: str, **kwargs) -> str:
        """
        Fetch prompt directly from Supabase database by ID and format it with variables.
        
        Args:
            prompt_id: ID of the prompt
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        
        Raises:
            Exception: If database query fails
        """
        # Check cache first
        cache_key = f"id:{prompt_id}"
        if cache_key in PromptLoader._prompt_cache:
            prompt_template = PromptLoader._prompt_cache[cache_key]
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            return prompt_template
        
        try:
            conn = PromptLoader._get_connection()
            cursor = conn.cursor()
            
            # Query the published_prompts table by ID
            cursor.execute(
                "SELECT content FROM published_prompts WHERE id = %s",
                (prompt_id,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                raise Exception(f"Prompt with ID '{prompt_id}' not found in database")
            
            prompt_template = result[0]
            
            if not prompt_template:
                raise Exception(f"Prompt with ID '{prompt_id}' has empty content in database")
            
            # Cache the template
            PromptLoader._prompt_cache[cache_key] = prompt_template
            
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            
            return prompt_template
            
        except psycopg2.Error as e:
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading prompt from database: {str(e)}")
    
    @staticmethod
    def load_draft_prompt_from_database_by_id(prompt_id: str, **kwargs) -> str:
        """
        Fetch draft prompt directly from Supabase database by ID and format it with variables.
        
        Args:
            prompt_id: ID of the draft prompt
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        
        Raises:
            Exception: If database query fails
        """
        # Check cache first
        cache_key = f"draft_id:{prompt_id}"
        if cache_key in PromptLoader._prompt_cache:
            prompt_template = PromptLoader._prompt_cache[cache_key]
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            return prompt_template
        
        try:
            conn = PromptLoader._get_connection()
            cursor = conn.cursor()
            
            # Query the draft_prompts table by ID
            cursor.execute(
                "SELECT content FROM draft_prompts WHERE id = %s",
                (prompt_id,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                raise Exception(f"Draft prompt with ID '{prompt_id}' not found in database")
            
            prompt_template = result[0]
            
            if not prompt_template:
                raise Exception(f"Draft prompt with ID '{prompt_id}' has empty content in database")
            
            # Cache the template
            PromptLoader._prompt_cache[cache_key] = prompt_template
            
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            
            return prompt_template
            
        except psycopg2.Error as e:
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading draft prompt from database: {str(e)}")
    
    @staticmethod
    def load_draft_prompt_from_database(prompt_name: str, **kwargs) -> str:
        """
        Fetch draft prompt directly from Supabase database and format it with variables.
        
        Args:
            prompt_name: Name of the prompt (e.g., "basic_info", "tone")
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        
        Raises:
            Exception: If database query fails
        """
        # Check cache first (use different cache key for drafts)
        cache_key = f"draft:{prompt_name}"
        if cache_key in PromptLoader._prompt_cache:
            prompt_template = PromptLoader._prompt_cache[cache_key]
            # Format with provided variables (only if kwargs provided)
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            return prompt_template
        
        try:
            conn = PromptLoader._get_connection()
            cursor = conn.cursor()
            
            # Query the draft_prompts table (get the most recent draft for this prompt name)
            cursor.execute(
                """
                SELECT content FROM draft_prompts 
                WHERE name = %s 
                ORDER BY updated_at DESC, created_at DESC 
                LIMIT 1
                """,
                (prompt_name,)
            )
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                raise Exception(f"Draft prompt '{prompt_name}' not found in database")
            
            prompt_template = result[0]
            
            if not prompt_template:
                raise Exception(f"Draft prompt '{prompt_name}' has empty content in database")
            
            # Cache the template
            PromptLoader._prompt_cache[cache_key] = prompt_template
            
            # Format with provided variables (only if kwargs provided)
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as ke:
                    missing_var = str(ke).strip("'\"")
                    raise Exception(f"Missing required placeholder variable: '{missing_var}'. Provided variables: {list(kwargs.keys())}")
            
            return prompt_template
            
        except psycopg2.Error as e:
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading draft prompt from database: {str(e)}")
    
    @staticmethod
    def load_prompt(prompt_file: str, **kwargs) -> str:
        """
        Load a prompt from a file and format it with variables.
        
        Args:
            prompt_file: Path to prompt file
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Format with provided variables
            if kwargs:
                return prompt_template.format(**kwargs)
            return prompt_template
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        except KeyError as ke:
            missing_var = str(ke).strip("'\"")
            raise Exception(f"Missing required placeholder variable: '{missing_var}'")
        except Exception as e:
            raise Exception(f"Error loading prompt: {str(e)}")
    
    @staticmethod
    def load_prompt_from_agent_dir(agent_dir: str, prompt_name: str, **kwargs) -> str:
        """
        Load a prompt directly from Supabase database. No fallbacks.
        
        Args:
            agent_dir: Directory of the agent (e.g., "Brand_Voice_Agent") - kept for compatibility, not used
            prompt_name: Name of the prompt in the database
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string
        
        Raises:
            Exception: If database is unavailable or prompt not found
        """
        # Check if database is configured
        has_connection_string = bool(PromptLoader.DATABASE_URL)
        has_individual_params = bool(PromptLoader.DB_HOST and PromptLoader.DB_USER and PromptLoader.DB_PASSWORD)
        
        if not has_connection_string and not has_individual_params:
            raise Exception("Database connection not configured. Set either DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME in .env")
        
        if not PromptLoader.USE_DATABASE:
            raise Exception("Database prompt loading is disabled. Set USE_PROMPT_DATABASE=true in .env")
        
        # Load directly from database - no fallback
        return PromptLoader.load_prompt_from_database(prompt_name, **kwargs)
    
    @staticmethod
    def clear_cache():
        """Clear the prompt cache. Useful for testing or when prompts are updated."""
        PromptLoader._prompt_cache.clear()
    
    @staticmethod
    def close_connection():
        """Close the database connection."""
        if PromptLoader._db_connection and not PromptLoader._db_connection.closed:
            PromptLoader._db_connection.close()
            PromptLoader._db_connection = None
