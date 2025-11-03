from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from typing import Optional
import os
from dotenv import load_dotenv
import pathlib

# Load environment variables BEFORE importing routes (which initialize services)
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.routes import health, langchain_routes, web_routes, simple_routes, document_routes
from app.config import get_settings

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Universal AI Assistant API",
    description="AI-powered assistant for YouTube videos, websites, PDFs, and text documents",
    version="2.0.0"
)

# Add CORS middleware - Allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - use the correct path relative to server directory
import pathlib
static_dir = pathlib.Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(health.router)
app.include_router(langchain_routes.router)
app.include_router(web_routes.router)
app.include_router(simple_routes.router)
app.include_router(document_routes.router)

@app.get("/")
async def root():
    """Redirect to main app interface."""
    return RedirectResponse(url="/static/index.html")

@app.get("/app")
async def app_ui():
    """Alternative clean URL for the main UI."""
    return RedirectResponse(url="/static/index.html")

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Universal AI Assistant API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "YouTube Video Analysis",
            "Web Content Processing",
            "PDF Document Analysis",
            "Text Document Processing"
        ],
        "documentation": "/docs",
        "web_interface": "/"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
