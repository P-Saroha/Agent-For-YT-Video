"""
Main FastAPI application setup.
This file creates the API server and configures all routes.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
import pathlib

# Load environment variables from .env file FIRST
# This is done before importing routes that need these variables
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import all route handlers
from app.routes import health, langchain_routes, web_routes, simple_routes, document_routes


# ==================== Create FastAPI Application ====================
app = FastAPI(
    title="AI Content Analysis API",
    description="Analyze YouTube videos, websites, and PDFs with AI",
    version="1.0.0"
)


# ==================== Configure CORS (Allow requests from any domain) ====================
# CORS = Cross-Origin Resource Sharing (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Allow requests from any domain (for development)
    allow_credentials=True,           # Allow cookies and credentials
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],              # Allow all headers
)


# ==================== Mount Static Files ====================
# Serve frontend HTML/CSS/JS files from the "static" directory
static_dir = pathlib.Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==================== Register All API Routes ====================
# Each router handles a specific feature (health checks, YouTube, web, documents, etc.)
app.include_router(health.router)              # GET /health
app.include_router(langchain_routes.router)    # YouTube API endpoints
app.include_router(web_routes.router)          # Web content endpoints
app.include_router(simple_routes.router)       # Simple AI endpoints
app.include_router(document_routes.router)     # PDF/document endpoints


# ==================== Root Endpoints ====================

@app.get("/")
async def root():
    """
    Home page - redirect to the main web interface.
    When you visit http://localhost:8000/ it goes to the web interface.
    """
    return RedirectResponse(url="/static/index.html")


@app.get("/app")
async def app_ui():
    """
    Alternative URL to access the web interface.
    You can visit http://localhost:8000/app instead of http://localhost:8000/
    """
    return RedirectResponse(url="/static/index.html")


@app.get("/api")
async def api_info():
    """
    Show information about this API.
    Useful for checking if the server is running and what features are available.
    """
    return {
        "name": "AI Content Analysis API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "YouTube Video Analysis",
            "Web Content Processing",
            "PDF Document Analysis",
            "Text Document Processing"
        ],
        "docs": "http://localhost:8000/docs",      # Swagger UI
        "web_interface": "http://localhost:8000/"  # Main web interface
    }


# ==================== Start Server ====================
if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    # host="0.0.0.0" = accessible from any IP address
    # port=8000 = use port 8000
    # reload=True = restart when code changes (for development)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
