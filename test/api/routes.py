"""
FastAPI routes for test API.

Defines API endpoints, keeping route definitions separate from
business logic for better organization.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from .models import CompareRequest
from .handlers import TestHandler
from concurrent.futures import ThreadPoolExecutor
from ..config.settings import TestConfig

# Create router
router = APIRouter()

# Create shared handler and executor
test_config = TestConfig.from_env()
executor = ThreadPoolExecutor(max_workers=test_config.max_workers)
handler = TestHandler(executor)


@router.post("/test-agent-compare")
async def test_agent_compare(request: CompareRequest) -> Dict[str, Any]:
    """
    Test an agent with both draft and published prompts.
    
    Returns side-by-side comparison of results.
    
    Args:
        request: Comparison request with agent name, prompt IDs, and test variables
    
    Returns:
        Comparison results from both runs
        
    Raises:
        HTTPException: If request is invalid or test fails
    """
    try:
        return await handler.compare_agents(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = f"Error comparing agents: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

