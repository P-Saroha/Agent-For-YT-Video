from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
from typing import Dict, Any

from app.models.schemas import (
    WebContentRequest,
    WebContentResponse,
    WebQuestionRequest,
    WebQuestionResponse,
    ErrorResponse
)

router = APIRouter(prefix="/web", tags=["web-content"])

# Initialize web service lazily
_web_service = None

def get_web_service():
    """Get web scraping service with lazy initialization"""
    global _web_service
    if _web_service is None:
        try:
            print("Initializing web scraping service...")
            from app.services.web_scraping_service import get_web_service
            _web_service = get_web_service()
            print("Web scraping service initialized successfully")
        except Exception as e:
            print(f"Failed to initialize web service: {e}")
            raise HTTPException(status_code=500, detail="Web service initialization failed")
    return _web_service

@router.post("/extract-content", response_model=WebContentResponse)
async def extract_web_content(request: WebContentRequest):
    """Extract and summarize content from any website URL"""
    try:
        print(f"Extracting content from URL: {request.url}")
        
        start_time = time.time()
        
        # Get web service
        service = get_web_service()
        
        # Extract content
        content_data = await service.extract_content_from_url(request.url)
        
        processing_time = time.time() - start_time
        
        return WebContentResponse(
            url=content_data["url"],
            title=content_data["title"],
            content_preview=content_data["content"][:500] + "..." if len(content_data["content"]) > 500 else content_data["content"],
            word_count=content_data["word_count"],
            extracted_at=datetime.now(),
            metadata=content_data["metadata"],
            status="success"
        )
        
    except Exception as e:
        print(f"Error extracting web content: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask-question", response_model=WebQuestionResponse)
async def ask_question_about_web_content(request: WebQuestionRequest):
    """Ask a question about content from any website URL"""
    try:
        print(f"Processing question about web content")
        print(f"URL: {request.url}")
        print(f"Question: {request.question}")
        
        start_time = time.time()
        
        # Get web service
        service = get_web_service()
        
        # Process question
        result = await service.ask_question_about_url(request.url, request.question)
        
        processing_time = time.time() - start_time
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return WebQuestionResponse(
            answer=result["answer"],
            url=result["url"],
            title=result["title"],
            question=result["question"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            confidence=result["confidence"],
            source_type=result["source_type"],
            word_count=result["word_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing web question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def web_service_health():
    """Check if web scraping service is working"""
    try:
        service = get_web_service()
        return {
            "status": "healthy",
            "service": "web-scraping",
            "timestamp": datetime.now()
        }
    except Exception as e:
        print(f"Web service health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Web service unavailable")