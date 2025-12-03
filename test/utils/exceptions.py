"""
Custom exceptions for test framework.

Provides specific exception types for better error handling
and debugging.
"""


class TestError(Exception):
    """Base exception for test-related errors."""
    pass


class ConfigurationError(TestError):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(TestError):
    """Raised when database operations fail."""
    pass


class PromptError(TestError):
    """Raised when prompt operations fail."""
    pass


class AgentError(TestError):
    """Raised when agent execution fails."""
    pass

