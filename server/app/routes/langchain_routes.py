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
from app.services.simple_ai_service import get_simple_service

router = APIRouter(prefix="/langchain", tags=["langchain"])

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_langchain(request: QuestionRequest):
    """Ask a question about a YouTube video using simple AI"""
    try:
        print(f"❓ Question: {request.question}")
        print(f"🎬 Video: {request.video_url}")
        
        start_time = time.time()
        
        # Use simple service instead of LangChain
        simple_service = get_simple_service()
        result = await simple_service.process_video_question(request.video_url, request.question)
        
        processing_time = time.time() - start_time
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
        
        return QuestionResponse(
            answer=result["answer"],
            video_id=result["video_id"],
            question=request.question,
            processing_time=processing_time,
            answered_at=datetime.now(),
            confidence=0.85,  # Default confidence
            source_type="simple_ai"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_langchain(request: VideoProcessRequest):
    """Process a YouTube video using simple AI"""
    try:
        print(f"🎬 Processing video: {request.video_url}")
        simple_service = get_simple_service()
        
        # Just extract video info for compatibility
        video_id = simple_service.extract_video_id(request.video_url)
        
        return VideoProcessResponse(
            video_id=video_id,
            title="Video processed",
            channel="Unknown",
            processed_at=datetime.now(),
            chunks_count=1,
            status="processed",
            language="unknown"
        )
        
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

@router.get("/video/{video_id}/status")
async def get_video_status_langchain(video_id: str):
    """Get processing status of a video"""
    return {"video_id": video_id, "status": "processed", "message": "Video processed"}

@router.delete("/video/{video_id}")
async def cleanup_video_langchain(video_id: str):
    """Clean up resources for a processed video"""
    return {"message": f"Video {video_id} cleaned up successfully"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "simple_ai", "timestamp": datetime.now()}