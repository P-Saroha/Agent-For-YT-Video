"""
Simple YouTube Routes (No Complex RAG Setup)

Quick endpoints for simple video processing without setup steps.

Endpoints:
- POST /youtube/simple/summarize - Quick video summary
- POST /youtube/simple/ask - Quick Q&A about video
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
from typing import Dict, Any
from pydantic import BaseModel

# ==================== Data Models ====================
class SimpleSummarizeRequest(BaseModel):
    """Request to summarize a video"""
    video_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class SimpleAskRequest(BaseModel):
    """Request to ask a question about a video"""
    video_url: str
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "question": "What is this video about?"
            }
        }


# ==================== Create Router ====================
router = APIRouter(prefix="/youtube/simple", tags=["YouTube Simple"])


# ==================== Endpoints ====================

@router.post("/summarize")
async def simple_summarize_video(request: SimpleSummarizeRequest) -> Dict[str, Any]:
    """
    Quick video summary using direct AI (no setup needed).
    
    This is a simplified endpoint that:
    1. Gets the video transcript
    2. Sends it directly to AI for summarization
    3. Returns the summary
    
    No need to process first - just paste the URL!
    
    Args:
        video_url: YouTube URL
        
    Returns:
        Dictionary with the summary
    """
    try:
        print(f"📝 Quick summarizing video: {request.video_url}")
        start_time = time.time()

        # Get simple service
        from app.services.simple_ai_service import get_simple_service
        service = get_simple_service()

        # Get transcript
        video_id = service.extract_video_id(request.video_url)
        transcript = await service.get_transcript(video_id)

        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Could not get video transcript"
            )

        # Summarize
        result = await service.summarize_text(transcript, title=f"Video {video_id}")

        processing_time = time.time() - start_time

        return {
            "success": True,
            "video_url": request.video_url,
            "summary": result.get("summary", "Could not generate summary"),
            "processing_time": f"{processing_time:.2f}s",
            "method": "Direct AI (No Setup Required)"
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize video: {str(e)}"
        )


@router.post("/ask")
async def simple_ask_question(request: SimpleAskRequest) -> Dict[str, Any]:
    """
    Quick Q&A about a video using direct AI (no setup needed).
    
    This is a simplified endpoint that:
    1. Gets the video transcript
    2. Sends it directly to AI with your question
    3. Returns the answer
    
    No need to process first - just paste the URL and ask!
    
    Args:
        video_url: YouTube URL
        question: Your question
        
    Returns:
        Dictionary with the answer
    """
    try:
        print(f"❓ Quick Q&A: {request.question[:50]}...")
        
        # Validate input
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        start_time = time.time()

        # Get simple service
        from app.services.simple_ai_service import get_simple_service
        service = get_simple_service()

        # Get transcript
        video_id = service.extract_video_id(request.video_url)
        transcript = await service.get_transcript(video_id)

        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Could not get video transcript"
            )

        # Ask question
        result = await service.ask_about_video(request.video_url, request.question)

        processing_time = time.time() - start_time

        return {
            "success": result.get("success", True),
            "video_url": request.video_url,
            "question": request.question,
            "answer": result.get("answer", "Could not generate answer"),
            "processing_time": f"{processing_time:.2f}s",
            "method": "Direct AI (No Setup Required)"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check if the Simple YouTube service is running.
    
    Returns:
        Dictionary with health status
    """
    try:
        from app.services.simple_ai_service import get_simple_service
        service = get_simple_service()
        return {
            "status": "healthy",
            "service": "YouTube Simple",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
