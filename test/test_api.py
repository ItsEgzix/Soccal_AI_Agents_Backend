"""
FastAPI endpoint for testing agents with draft/published prompts.

This module is designed to work in two modes:
- Standalone: `python -m test.test_api` (uses `app` defined below)
- Integrated: imported into the main AI backend and mounted via the `router`

The new modular structure makes it easy to:
- Understand what each component does
- Test components independently
- Extend functionality without modifying existing code
- Onboard new developers quickly
"""
from fastapi import FastAPI
import uvicorn
from .api.routes import router

# FastAPI app for standalone usage
app = FastAPI(title="Agent Test API", version="2.0.0")

# Include router
app.include_router(router)


if __name__ == "__main__":
    import os
    port = int(os.getenv("TEST_API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
