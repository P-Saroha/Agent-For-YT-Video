"""
YouTube Video Analysis Routes

Endpoints:
- POST /youtube/process - Process a YouTube video for Q&A
- POST /youtube/ask-question - Ask a question about a processed video
- POST /youtube/summarize - Get a summary of a video
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

# ==================== Data Models ====================
class ProcessVideoRequest(BaseModel):
    """Request to process a YouTube video"""
    video_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class AskQuestionRequest(BaseModel):
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


class SummarizeVideoRequest(BaseModel):
    """Request to summarize a video"""
    video_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


# ==================== Create Router ====================
router = APIRouter(prefix="/youtube", tags=["YouTube Videos"])


# ==================== Helper Function ====================
def get_youtube_service():
    """Get YouTube RAG service instance."""
    from app.services.langchain_service import get_youtube_service as _get_service
    return _get_service()


# ==================== Endpoints ====================

@router.post("/process")
async def process_video(request: ProcessVideoRequest) -> Dict[str, Any]:
    """
    Process a YouTube video for question-answering.
    
    This endpoint:
    1. Extracts the video transcript
    2. Splits it into chunks
    3. Converts to vectors
    4. Stores in a database
    
    After processing, you can ask questions about the video.
    
    Args:
        video_url: URL of the YouTube video
        
    Returns:
        Dictionary with processing status and video info
    """
    try:
        print(f"🎬 Processing video: {request.video_url}")
        start_time = time.time()

        # Get the service
        service = get_youtube_service()

        # Process the video
        result = await service.process_video(request.video_url)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "video_id": result.get("video_id", "Unknown"),
            "title": result.get("title", "Unknown"),
            "chunks": result.get("chunks", 0),
            "language": result.get("language", "unknown"),
            "processing_time": f"{processing_time:.2f}s",
            "message": "Video processed successfully. You can now ask questions about it."
        }

    except Exception as e:
        print(f"❌ Error processing video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )


@router.post("/ask-question")
async def ask_question(request: AskQuestionRequest) -> Dict[str, Any]:
    """
    Ask a question about a processed YouTube video.
    
    The video must be processed first using the /process endpoint.
    
    Args:
        video_url: URL of the YouTube video
        question: The question to ask
        
    Returns:
        Dictionary with the answer and metadata
    """
    try:
        print(f"❓ Question: {request.question[:50]}...")
        start_time = time.time()

        # Get the service
        service = get_youtube_service()

        # Ask the question
        result = await service.ask_question(request.video_url, request.question)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "question": request.question,
            "answer": result.get("answer", "No answer generated"),
            "sources_used": result.get("sources_used", 0),
            "processing_time": f"{processing_time:.2f}s",
            "method": result.get("method", "RAG")
        }

    except Exception as e:
        print(f"❌ Error answering question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/summarize")
async def summarize_video(request: SummarizeVideoRequest) -> Dict[str, Any]:
    """
    Generate a summary of a YouTube video.
    
    The video must be processed first using the /process endpoint.
    
    Args:
        video_url: URL of the YouTube video
        
    Returns:
        Dictionary with the summary
    """
    try:
        print(f"📝 Summarizing video: {request.video_url}")
        start_time = time.time()

        # Get the service
        service = get_youtube_service()

        # Generate summary
        result = await service.summarize_video(request.video_url)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "video_url": request.video_url,
            "summary": result.get("summary", "No summary generated"),
            "processing_time": f"{processing_time:.2f}s"
        }

    except Exception as e:
        print(f"❌ Error summarizing video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize video: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check if the YouTube service is running.
    
    Returns:
        Dictionary with health status
    """
    try:
        service = get_youtube_service()
        return {
            "status": "healthy",
            "service": "YouTube RAG",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
