from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from typing import Optional
import os
from dotenv import load_dotenv

from app.routes import health, langchain_routes, web_routes, simple_routes
from app.config import get_settings

# Load environment variables
load_dotenv()

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="YouTube AI Assistant API",
    description="AI-powered assistant for YouTube video content analysis",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {
        "message": "YouTube AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "web_interface": "http://127.0.0.1:8000/static/youtube-ai-web.html",
        "test_ui": "http://127.0.0.1:8000/static/test.html"
    }

@app.get("/test")
async def test_ui():
    """Redirect to test interface"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/test.html")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
