"""
Main Entry Point for Adaptive LLM Tutor.
Imports and runs the unified FastAPI application with backwards compatibility.
"""

import uvicorn
from src.api.server import app

# Backwards compatible alias for deployment runners looking for api or app
api = app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
