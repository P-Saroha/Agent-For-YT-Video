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
from app.services.langchain_service import LangChainYouTubeService

router = APIRouter(prefix="/langchain", tags=["langchain"])

# Initialize LangChain service lazily
_langchain_service = None

def get_langchain_service():
    """Get LangChain service with lazy initialization"""
    global _langchain_service
    if _langchain_service is None:
        print("🔧 Initializing LangChain YouTube service...")
        _langchain_service = LangChainYouTubeService()
        print("✅ LangChain YouTube service initialized")
    return _langchain_service

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_langchain(request: VideoProcessRequest):
    """Process a YouTube video using LangChain"""
    try:
        print(f"🎬 Processing video: {request.video_url}")
        langchain_service = get_langchain_service()
        
        result = await langchain_service.process_video(request.video_url)
        
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
        print(f"❌ Error processing video: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_langchain(request: QuestionRequest):
    """Ask a question about a processed video using LangChain"""
    try:
        print(f"❓ Question for video {request.video_id}: {request.question}")
        start_time = time.time()
        
        langchain_service = get_langchain_service()
        result = await langchain_service.ask_question(request.video_id, request.question)
        
        response_time = time.time() - start_time
        
        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result.get("sources", []),
            response_time=response_time
        )
        
    except Exception as e:
        print(f"❌ Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")

@router.get("/video/{video_id}/status")
async def get_video_status_langchain(video_id: str):
    """Get processing status of a video (TEST VERSION)"""
    return {"video_id": video_id, "status": "processed", "message": "Test video status"}

@router.delete("/video/{video_id}")
async def cleanup_video_langchain(video_id: str):
    """Clean up resources for a processed video (TEST VERSION)"""
    return {"message": f"Video {video_id} cleaned up successfully (test mode)"}

@router.get("/health")
async def langchain_health():
    """Health check for LangChain service"""
    return {
        "status": "healthy",
        "service": "langchain_youtube_ai",
        "timestamp": datetime.now()
    }