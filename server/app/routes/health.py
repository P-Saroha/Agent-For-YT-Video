"""
Health Check Routes

Endpoint:
- GET /health - Check if the API is running
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check() -> Dict[str, any]:
    """
    Health check endpoint.
    
    Use this to verify the API server is running.
    
    Returns:
        Dictionary with health status and timestamp
    """
    return {
        "status": "healthy",
        "service": "AI Content Analysis API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
