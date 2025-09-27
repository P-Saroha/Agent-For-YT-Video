from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any

from app.models.schemas import (
    VideoProcessRequest, 
    VideoProcessResponse, 
    QuestionRequest, 
    QuestionResponse,
    ErrorResponse
)

router = APIRouter(prefix="/extension", tags=["extension"])

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_for_extension(request: VideoProcessRequest):
    """Process a YouTube video optimized for Chrome extension (TEST VERSION)"""
    return VideoProcessResponse(
        video_id="test_extension_video_id",
        title="Test Extension Video",
        channel="Test Extension Channel", 
        processed_at=datetime.now(),
        chunks_count=5,
        status="processed",
        language="en"
    )

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_for_extension(request: QuestionRequest):
    """Ask a question optimized for Chrome extension (TEST VERSION)"""
    return QuestionResponse(
        video_id=request.video_id,
        question=request.question,
        answer="Test extension answer for CORS testing",
        confidence_score=0.98,
        response_time=0.05,
        sources_used=1,
        processing_method="extension_test"
    )

@router.get("/health")
async def extension_health():
    """Health check for extension service"""
    return {
        "status": "healthy",
        "service": "extension_youtube_ai",
        "timestamp": datetime.now()
    }