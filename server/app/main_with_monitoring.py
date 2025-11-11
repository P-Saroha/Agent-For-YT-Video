"""
Enhanced main.py with monitoring and observability
Add this to server/app/main.py after testing locally
"""

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
import logging
from pythonjsonlogger import jsonlogger

# Load environment variables BEFORE importing routes
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Setup JSON logging for production
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s',
    rename_fields={'levelname': 'severity', 'asctime': 'timestamp'}
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

from app.routes import health, langchain_routes, web_routes, simple_routes, document_routes
from app.config import get_settings

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Universal AI Assistant API",
    description="AI-powered assistant for YouTube videos, websites, PDFs, and text documents with monitoring",
    version="2.1.0"
)

# Add Prometheus monitoring (optional - install with: pip install prometheus-fastapi-instrumentator)
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    
    # Initialize metrics
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="fastapi_inprogress",
        inprogress_labels=True,
    )
    
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)
    logger.info("Prometheus metrics enabled at /metrics")
except ImportError:
    logger.warning("prometheus-fastapi-instrumentator not installed. Metrics disabled.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = pathlib.Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(health.router)
app.include_router(langchain_routes.router)
app.include_router(web_routes.router)
app.include_router(simple_routes.router)
app.include_router(document_routes.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Application starting up", extra={
        "version": "2.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    })

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down")

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
    """API information endpoint with monitoring links."""
    return {
        "message": "Universal AI Assistant API",
        "version": "2.1.0",
        "status": "running",
        "features": [
            "YouTube Video Analysis",
            "Web Content Processing",
            "PDF Document Analysis",
            "Text Document Processing"
        ],
        "documentation": "/docs",
        "web_interface": "/",
        "health_check": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom JSON logging
    )
