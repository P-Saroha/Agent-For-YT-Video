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

# Initialize optimized service for extension
extension_service = OptimizedYouTubeService(
    max_cache_size=5,  # Only keep 5 videos in memory for extension
    max_chunk_size=800  # Smaller chunks for faster processing
)

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_for_extension(request: VideoProcessRequest):
    """Process a YouTube video optimized for Chrome extension"""
    try:
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
        print(f"Error processing video for extension: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_for_extension(request: QuestionRequest):
    """Ask a question about a processed video - optimized for extension"""
    try:
        start_time = time.time()
        
        result = await extension_service.ask_question_optimized(request.video_id, request.question)
        
        response_time = time.time() - start_time
        
        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result.get("sources", []),
            response_time=response_time,
            method=result.get("method", "optimized"),
            language=result.get("language", "unknown")
        )
        
    except Exception as e:
        print(f"Error answering question for extension: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/{video_id}/status")
async def get_video_status_for_extension(video_id: str):
    """Get processing status of a video - extension optimized"""
    try:
        status = extension_service.get_video_status(video_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for extension monitoring"""
    try:
        stats = extension_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/cleanup")
async def cleanup_cache():
    """Clean up old cache entries"""
    try:
        extension_service.cleanup_old_cache(days_old=3)  # Clean up after 3 days for extension
        return {"message": "Cache cleaned up successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/video/{video_id}")
async def cleanup_video_for_extension(video_id: str):
    """Clean up resources for a processed video"""
    try:
        extension_service.cleanup_video(video_id)
        return {"message": f"Video {video_id} cleaned up successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def extension_health():
    """Health check for extension service"""
    try:
        stats = extension_service.get_cache_stats()
        return {
            "status": "healthy",
            "service": "optimized_youtube_extension",
            "timestamp": datetime.now(),
            "cache_stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "optimized_youtube_extension", 
            "error": str(e),
            "timestamp": datetime.now()
        }