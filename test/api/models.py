"""
API request/response models.

Defines Pydantic models for API requests and responses,
providing validation and type safety.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class TestRequest(BaseModel):
    """Request model for single agent test."""
    agentName: str
    publishedPromptIds: List[str] = []
    draftPromptIds: List[str] = []
    testVariables: Dict[str, Any] = {}


class CompareRequest(BaseModel):
    """
    Request model for agent comparison.
    
    Tests an agent with both draft and published prompts,
    returning side-by-side comparison.
    """
    agentName: str
    publishedPromptIds: List[str] = []
    draftPromptIds: List[str] = []
    testVariables: Dict[str, Any] = {}
    adminId: Optional[str] = "system"

