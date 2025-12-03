"""
Centralized configuration management.

This module provides a single source of truth for all configuration,
making it easy to manage environment variables and settings.
"""
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import os


@dataclass
class DatabaseConfig:
    """
    Database connection configuration.
    
    Supports both connection string (DATABASE_URL) and individual parameters.
    """
    url: str = None
    user: str = None
    password: str = None
    host: str = None
    port: int = 5432
    name: str = "postgres"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """
        Load database configuration from environment variables.
        
        Looks for:
        - DATABASE_URL (full connection string)
        - OR individual: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
        - OR legacy: user, password, host, port, dbname
        
        Returns:
            DatabaseConfig instance with loaded values
        """
        # Load .env file
        env_path = find_dotenv()
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            # Fallback: try AI_Backend directory
            env_path = Path(__file__).parent.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
        
        return cls(
            url=os.getenv("DATABASE_URL"),
            user=os.getenv("DB_USER") or os.getenv("user"),
            password=os.getenv("DB_PASSWORD") or os.getenv("password"),
            host=os.getenv("DB_HOST") or os.getenv("host"),
            port=int(os.getenv("DB_PORT") or os.getenv("port") or "5432"),
            name=os.getenv("DB_NAME") or os.getenv("dbname") or "postgres"
        )
    
    def is_configured(self) -> bool:
        """Check if database configuration is valid."""
        return bool(self.url or (self.host and self.user and self.password))


@dataclass
class TestConfig:
    """
    Test-specific configuration.
    
    Controls test execution behavior like timeouts, concurrency, and logging.
    """
    max_workers: int = 2
    timeout: int = 300  # 5 minutes
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """Load test configuration from environment variables."""
        return cls(
            max_workers=int(os.getenv("TEST_MAX_WORKERS", "2")),
            timeout=int(os.getenv("TEST_TIMEOUT", "300")),
            log_level=os.getenv("TEST_LOG_LEVEL", "INFO")
        )

