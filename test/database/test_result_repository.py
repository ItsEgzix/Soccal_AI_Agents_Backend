"""
Repository for saving test results to database.

Provides a clean interface for storing test results, making it easy
to persist test outcomes for later analysis.
"""
import uuid
from typing import List, Dict, Any
from datetime import datetime
from psycopg2.extras import Json as PsycopgJson
from .connection import DatabaseConnection


class TestResultRepository:
    """
    Handles test result storage in database.
    
    Provides methods to save test results to the prompt_test_results table,
    allowing test history to be tracked and analyzed.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize test result repository.
        
        Args:
            db_connection: Database connection manager
        """
        self.db = db_connection
    
    def save_test_result(
        self,
        published_prompt_ids: List[str],
        draft_prompt_ids: List[str],
        test_variables: Dict[str, Any],
        results: Dict[str, Any],
        success: bool,
        admin_id: str = "system"
    ) -> str:
        """
        Save test result to database.
        
        Args:
            published_prompt_ids: List of published prompt UUIDs used in test
            draft_prompt_ids: List of draft prompt UUIDs used in test
            test_variables: Test input variables (website_url, instagram_account, etc.)
            results: Test results dictionary
            success: Whether the test succeeded
            admin_id: ID of admin who ran the test
            
        Returns:
            UUID of the created test result record
            
        Raises:
            psycopg2.Error: If database insert fails
        """
        test_result_id = str(uuid.uuid4())
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO prompt_test_results 
                (id, published_prompt_ids, draft_prompt_ids, test_variables, results, success, tested_by, tested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (
                    test_result_id,
                    published_prompt_ids,
                    draft_prompt_ids,
                    PsycopgJson(test_variables),
                    PsycopgJson(results),
                    success,
                    admin_id
                )
            )
            
            return cursor.fetchone()[0]
    
    def get_test_result(self, test_result_id: str) -> Dict[str, Any]:
        """
        Retrieve a test result by ID.
        
        Args:
            test_result_id: UUID of the test result
            
        Returns:
            Dictionary containing test result data
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM prompt_test_results WHERE id = %s",
                (test_result_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

