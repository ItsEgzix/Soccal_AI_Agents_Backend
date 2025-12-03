"""
FastAPI Application for MarketingOS AI Backend
Main entry point for the API server.
"""

# Load environment variables FIRST (before any other imports)
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import asyncio
import json

# Import WebSocket manager
sys.path.insert(0, os.path.dirname(__file__))
from utils.websocket_manager import ConnectionManager

# Global connection manager
manager = ConnectionManager()

# Initialize FastAPI app first
app = FastAPI(
    title="MarketingOS AI Backend",
    description="AI-powered social media content generation system",
    version="1.0.0",
)

# Include test API routes (for agent testing) from test/api/routes.py
try:
    from test.api.routes import router as test_router

    app.include_router(test_router)
except Exception as e:
    # Avoid crashing the main app if test API import fails;
    # log to stderr so it can be diagnosed in development.
    print(f"Warning: Failed to include test API routes: {e}", file=sys.stderr)

# Lazy import function to avoid circular import issues
def get_process_company_context():
    """Lazy import of process_company_context to avoid circular imports."""
    agents_path = os.path.join(os.path.dirname(__file__), 'Agents')
    sys.path.insert(0, agents_path)
    
    from teams.company_context.main import process_company_context
    return process_company_context

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "message": "MarketingOS AI Backend API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Request/Response Models
class CompanyContextRequest(BaseModel):
    """Request model for company context extraction."""
    company_name: str
    website_url: str
    instagram_account: str


class CompanyContextResponse(BaseModel):
    """Response model for company context."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@app.websocket("/ws/company-context")
async def websocket_company_context(websocket: WebSocket):
    """
    WebSocket endpoint for company context extraction with real-time logs.
    
    Client sends:
    {
        "company_name": "Example Company",
        "website_url": "https://example.com",
        "instagram_account": "example"
    }
    
    Server streams:
    - Log messages: {"type": "log", "log_type": "info|success|error|warning", "message": "..."}
    - Final result: {"type": "result", "data": {...}}
    - Errors: {"type": "error", "message": "..."}
    """
    await manager.connect(websocket)
    
    try:
        # Receive initial request
        data = await websocket.receive_json()
        
        company_name = data.get("company_name")
        website_url = data.get("website_url")
        instagram_account = data.get("instagram_account")
        
        if not all([company_name, website_url, instagram_account]):
            await manager.send_error("Missing required fields: company_name, website_url, instagram_account")
            return
        
        # Import orchestrator
        agents_path = os.path.join(os.path.dirname(__file__), 'Agents')
        sys.path.insert(0, agents_path)
        
        from teams.company_context.orchestrator import OrchestratorAgent
        
        # Create orchestrator with log callback (use sync method for queue-based)
        orchestrator = OrchestratorAgent()
        orchestrator.set_log_callback(manager)  # Pass manager object, not method
        
        # Start log processor if not running
        if not manager._log_processor_running:
            manager._log_processor_running = True
            manager._log_processor_task = asyncio.create_task(manager._process_log_queue())
        
        # Process in background task
        async def process():
            try:
                # Run processing in thread pool to avoid blocking WebSocket
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    orchestrator.process,
                    company_name,
                    website_url,
                    instagram_account
                )
                # Wait a bit for any remaining logs to be processed
                await asyncio.sleep(0.5)
                await manager.send_result(result)
            except Exception as e:
                await manager.send_error(f"Error processing company context: {str(e)}")
            finally:
                # Stop log processor
                manager._log_processor_running = False
                if manager._log_processor_task:
                    manager._log_processor_task.cancel()
                    try:
                        await manager._log_processor_task
                    except asyncio.CancelledError:
                        pass
        
        # Run processing
        await process()
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await manager.send_error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


@app.post("/api/company-context", response_model=CompanyContextResponse)
async def extract_company_context(request: CompanyContextRequest):
    """
    Extract company context from website and Instagram (REST endpoint).
    For real-time logs, use WebSocket endpoint: /ws/company-context
    """
    try:
        # Lazy load the function
        process_company_context = get_process_company_context()
        
        result = process_company_context(
            company_name=request.company_name,
            website_url=request.website_url,
            instagram_account=request.instagram_account
        )
        
        return CompanyContextResponse(
            success=True,
            data=result
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing company context: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

