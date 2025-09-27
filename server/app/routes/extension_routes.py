from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import time
from typing import Dict, Any

from app.models.schemas import (
    VideoProcessRequest, 
    VideoProcessResponse, 
    QuestionRequest, 
    QuestionResponse,
    ErrorResponse
)
from app.services.optimized_youtube_service import OptimizedYouTubeService

router = APIRouter(prefix="/extension", tags=["extension"])

# Initialize optimized service lazily
_extension_service = None

def get_extension_service():
    """Get extension service with lazy initialization"""
    global _extension_service
    if _extension_service is None:
        print("Initializing optimized YouTube service for extensions...")
        _extension_service = OptimizedYouTubeService(
            max_cache_size=5,  # Only keep 5 videos in memory for extension
            max_chunk_size=800  # Smaller chunks for faster processing
        )
        print("Optimized YouTube service initialized")
    return _extension_service

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_for_extension(request: VideoProcessRequest):
    """Process a YouTube video optimized for Chrome extension"""
    try:
        print(f"Processing video (extension): {request.video_url}")
        extension_service = get_extension_service()
        
        result = await extension_service.process_video_smart(request.video_url)
        
        return VideoProcessResponse(
            video_id=result["video_id"],
            title=result["title"],
            channel=result["channel"],
            processed_at=datetime.now(),
            chunks_count=result["chunks_count"],
            status=result["status"],
            language=result.get("language", "unknown")
        )
        
    except Exception as e:
        print(f"Error processing video (extension): {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_for_extension(request: QuestionRequest):
    """Ask a question optimized for Chrome extension"""
    try:
        print(f"Question for video {request.video_id} (extension): {request.question}")
        start_time = time.time()
        
        extension_service = get_extension_service()
        result = await extension_service.ask_question_optimized(request.video_id, request.question)
        
        response_time = time.time() - start_time
        
        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result.get("sources", []),
            response_time=response_time
        )
        
    except Exception as e:
        print(f"Error answering question (extension): {e}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")

@router.get("/health")
async def extension_health():
    """Health check for extension service"""
    return {
        "status": "healthy",
        "service": "extension_youtube_ai",
        "timestamp": datetime.now()
    }