"""
Simple YouTube AI routes for basic video processing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.simple_ai_service import SimpleYouTubeAIService

router = APIRouter(tags=["simple-youtube"])

# Simple request models
class VideoSummaryRequest(BaseModel):
    video_url: str

class VideoQuestionRequest(BaseModel):
    video_url: str
    question: str

class SimpleResponse(BaseModel):
    summary: Optional[str] = None
    answer: Optional[str] = None
    video_url: str
    status: str = "success"

# Initialize service
simple_service = SimpleYouTubeAIService()

@router.post("/summarize", response_model=SimpleResponse)
async def summarize_video(request: VideoSummaryRequest):
    """Get a summary of a YouTube video"""
    try:
        # Use the simple AI service to get video summary
        result = await simple_service.process_video_question(
            video_url=request.video_url,
            question="Please provide a comprehensive summary of this video. Use clear headings, bullet points, bold text for key concepts, and proper paragraph breaks. Include main topics, key points, important details, and conclusions. Format with Markdown for easy reading."
        )
        
        return SimpleResponse(
            summary=result.get("answer", "Unable to generate summary"),
            video_url=request.video_url,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize video: {str(e)}"
        )

@router.post("/ask", response_model=SimpleResponse)
async def ask_video_question(request: VideoQuestionRequest):
    """Ask a question about a YouTube video"""
    try:
        result = await simple_service.process_video_question(
            video_url=request.video_url,
            question=request.question
        )
        
        return SimpleResponse(
            answer=result.get("answer", "Unable to get answer"),
            video_url=request.video_url,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )