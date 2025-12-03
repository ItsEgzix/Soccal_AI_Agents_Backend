"""
Database connection management.

Provides a clean interface for database connections with proper
resource management and error handling.
"""
import psycopg2
from contextlib import contextmanager
from typing import Generator
from ..config.settings import DatabaseConfig


class DatabaseConnection:
    """
    Manages database connections with proper cleanup.
    
    Uses context managers to ensure connections are always properly
    closed, even in case of errors.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connection manager.
        
        Args:
            config: Database configuration
        """
        self.config = config
        
        if not config.is_configured():
            raise ValueError(
                "Database connection not configured. "
                "Set either DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME in .env"
            )
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get a database connection with automatic cleanup.
        
        Usage:
            with db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
                # Connection automatically committed and closed
        
        Yields:
            psycopg2 connection object
            
        Raises:
            ValueError: If database is not configured
            psycopg2.Error: If connection fails
        """
        conn = None
        try:
            if self.config.url:
                conn = psycopg2.connect(self.config.url, connect_timeout=10)
            elif self.config.host and self.config.user:
                conn = psycopg2.connect(
                    user=self.config.user,
                    password=self.config.password,
                    host=self.config.host,
                    port=self.config.port,
                    dbname=self.config.name,
                    connect_timeout=10
                )
            else:
                raise ValueError("Database connection not configured")
            
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

