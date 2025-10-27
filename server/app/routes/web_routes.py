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

# Initialize web service lazily - using fast service for better performance
_web_service = None

def get_web_service():
    """Get RAG web service for comprehensive content extraction and analysis"""
    global _web_service
    if _web_service is None:
        try:
            print("Initializing RAG web content service...")
            from app.services.rag_web_service import RAGWebContentService
            _web_service = RAGWebContentService()
            print("RAG web content service initialized successfully")
        except Exception as e:
            print(f"Failed to initialize RAG web service: {e}")
            # Fallback to fast service if RAG fails
            print("Falling back to fast web service...")
            from app.services.fast_web_service import get_fast_web_service
            _web_service = get_fast_web_service()
            print("Fast web content service initialized as fallback")
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
        
        if "error" in content_data:
            raise HTTPException(status_code=500, detail=content_data["error"])
        
        # Use the extracted content directly for faster response
        return WebContentResponse(
            url=content_data["url"],
            title=content_data["title"],
            content_preview=content_data["content"],  # Return full content instead of truncated
            word_count=content_data["word_count"],
            char_count=content_data.get("char_count", len(content_data["content"])),  # Add char count
            extracted_at=datetime.now(),
            metadata={"processing_time": processing_time, "method": "fast_extraction"},
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
        print(f"Request received: {request}")
        print(f"URL: {request.url}")
        print(f"Question: {request.question}")
        
        # Validate inputs
        if not request.url or not request.url.strip():
            raise HTTPException(status_code=400, detail="URL is required")
        
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")
        
        start_time = time.time()
        
        # Get web service
        service = get_web_service()
        
        # Try RAG approach first, fallback to simple search
        if hasattr(service, 'ask_question_with_rag'):
            print(f"🔍 Processing question with RAG approach (full vector search)")
            result = await service.ask_question_with_rag(request.url, request.question)
        else:
            print(f"🔍 Processing question with simple search approach")
            result = await service.ask_question_with_simple_search(request.url, request.question)
        
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