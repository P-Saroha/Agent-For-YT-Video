"""
Web Content Analysis Routes

Endpoints:
- POST /web/process - Process a website for Q&A
- POST /web/ask-question - Ask a question about a website
- POST /web/summarize - Get a summary of a website
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
from typing import Dict, Any
from pydantic import BaseModel

# ==================== Data Models ====================
class ProcessWebRequest(BaseModel):
    """Request to process a website"""
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
            }
        }


class AskWebQuestionRequest(BaseModel):
    """Request to ask a question about a website"""
    url: str
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "question": "What is artificial intelligence?"
            }
        }


class SummarizeWebRequest(BaseModel):
    """Request to summarize a website"""
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
            }
        }


# ==================== Create Router ====================
router = APIRouter(prefix="/web", tags=["Web Content"])


# ==================== Helper Function ====================
def get_web_service():
    """Get Web RAG service instance."""
    from app.services.rag_web_service import get_web_service as _get_service
    return _get_service()


# ==================== Endpoints ====================

@router.post("/process")
async def process_website(request: ProcessWebRequest) -> Dict[str, Any]:
    """
    Process a website for question-answering.
    
    This endpoint:
    1. Fetches the webpage content
    2. Extracts main text (removes ads, navigation, etc.)
    3. Splits into chunks
    4. Converts to vectors
    5. Stores in a database
    
    After processing, you can ask questions about the page.
    
    Supports:
    - Regular websites (HTML scraping)
    - Wikipedia articles (uses official API)
    
    Args:
        url: URL of the website
        
    Returns:
        Dictionary with processing status and page info
    """
    try:
        print(f"🌐 Processing website: {request.url}")
        start_time = time.time()

        # Get the service
        service = get_web_service()

        # Process the webpage
        result = await service.process_webpage(request.url)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "url": request.url,
            "title": result.get("title", "Unknown"),
            "chunks": result.get("chunks", 0),
            "content_length": result.get("content_length", 0),
            "processing_time": f"{processing_time:.2f}s",
            "message": "Webpage processed successfully. You can now ask questions about it."
        }

    except Exception as e:
        print(f"❌ Error processing website: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process website: {str(e)}"
        )


@router.post("/ask-question")
async def ask_question(request: AskWebQuestionRequest) -> Dict[str, Any]:
    """
    Ask a question about a website.
    
    The website must be processed first using the /process endpoint.
    
    Args:
        url: URL of the website
        question: The question to ask
        
    Returns:
        Dictionary with the answer and metadata
    """
    try:
        print(f"❓ Question: {request.question[:50]}...")
        
        # Validate inputs
        if not request.url or not request.url.strip():
            raise HTTPException(status_code=400, detail="URL is required")
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        start_time = time.time()

        # Get the service
        service = get_web_service()

        # Ask the question
        result = await service.ask_question(request.url, request.question)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "url": request.url,
            "question": request.question,
            "answer": result.get("answer", "No answer generated"),
            "sources_used": result.get("sources_used", 0),
            "processing_time": f"{processing_time:.2f}s",
            "method": result.get("method", "RAG")
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error answering question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/summarize")
async def summarize_website(request: SummarizeWebRequest) -> Dict[str, Any]:
    """
    Generate a summary of a website.
    
    The website must be processed first using the /process endpoint.
    
    Args:
        url: URL of the website
        
    Returns:
        Dictionary with the summary
    """
    try:
        print(f"📝 Summarizing website: {request.url}")
        start_time = time.time()

        # Get the service
        service = get_web_service()

        # Generate summary
        result = await service.summarize_webpage(request.url)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "url": request.url,
            "title": result.get("title", "Unknown"),
            "summary": result.get("summary", "No summary generated"),
            "processing_time": f"{processing_time:.2f}s"
        }

    except Exception as e:
        print(f"❌ Error summarizing website: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize website: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check if the Web service is running.
    
    Returns:
        Dictionary with health status
    """
    try:
        service = get_web_service()
        return {
            "status": "healthy",
            "service": "Web RAG",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
