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

router = APIRouter(prefix="/langchain", tags=["langchain"])

# Initialize LangChain service lazily to avoid startup issues
_langchain_service = None

def get_langchain_service():
    """Get LangChain service with lazy initialization"""
    global _langchain_service
    if _langchain_service is None:
        try:
            print("Initializing LangChain YouTube service...")
            from app.services.langchain_service import LangChainYouTubeService
            _langchain_service = LangChainYouTubeService()
            print("LangChain YouTube service initialized successfully")
        except Exception as e:
            print(f"Failed to initialize LangChain service: {e}")
            # Fallback to simple service if LangChain fails
            from app.services.simple_ai_service import get_simple_service
            _langchain_service = get_simple_service()
            print("Using simple AI service as fallback")
    return _langchain_service

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question_langchain(request: QuestionRequest):
    """Ask a question about a YouTube video using LangChain RAG"""
    try:
        print(f"Question: {request.question}")
        print(f"Video ID: {request.video_id}")
        
        start_time = time.time()
        
        # Get LangChain service (with fallback)
        service = get_langchain_service()
        
        # Convert video_id back to URL for the service
        video_url = f"https://www.youtube.com/watch?v={request.video_id}"
        
        # Use appropriate method based on service type
        if hasattr(service, 'process_video_question'):
            # Simple AI service fallback
            result = await service.process_video_question(video_url, request.question)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
            
            processing_time = time.time() - start_time
            return QuestionResponse(
                answer=result["answer"],
                video_id=result["video_id"],
                question=request.question,
                processing_time=processing_time,
                answered_at=datetime.now(),
                confidence=0.85,
                source_type="simple_ai_fallback"
            )
        else:
            # Full LangChain service
            # Ask question directly with video_id
            answer_result = await service.ask_question(request.video_id, request.question)
            
            processing_time = time.time() - start_time
            
            return QuestionResponse(
                answer=answer_result["answer"],
                video_id=request.video_id,
                question=request.question,
                processing_time=processing_time,
                answered_at=datetime.now(),
                confidence=answer_result.get("confidence", 0.85),
                source_type="langchain_rag"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video_langchain(request: VideoProcessRequest):
    """Process a YouTube video using LangChain with embeddings and vector storage"""
    try:
        print(f"Processing video with LangChain: {request.video_url}")
        service = get_langchain_service()
        
        if hasattr(service, 'process_video'):
            # Full LangChain service
            result = await service.process_video(request.video_url)
            
            return VideoProcessResponse(
                video_id=result["video_id"],
                title=result.get("title", "Video processed"),
                channel=result.get("channel", "Unknown"),
                processed_at=datetime.now(),
                chunks_count=result.get("chunks_count", 1),
                status=result["status"],
                language=result.get("language", "unknown")
            )
        else:
            # Simple fallback
            video_id = service.extract_video_id(request.video_url)
            return VideoProcessResponse(
                video_id=video_id,
                title="Video processed (fallback)",
                channel="Unknown",
                processed_at=datetime.now(),
                chunks_count=1,
                status="processed",
                language="unknown"
            )
        
    except Exception as e:
        print(f"Error processing video (RAG): {e}")
        # Fallback: try to at least fetch a transcript via simple service and return a minimal processed response
        try:
            from app.services.simple_ai_service import get_simple_service
            simple = get_simple_service()
            vid = simple.extract_video_id(request.video_url)
            transcript = await simple.get_transcript(vid)
            approx_chunks = max(1, len(transcript) // 800) if transcript else 0
            return VideoProcessResponse(
                video_id=vid,
                title=f"YouTube Video {vid}",
                channel="Unknown",
                processed_at=datetime.now(),
                chunks_count=approx_chunks,
                status="processed_fallback",
                language="unknown"
            )
        except Exception as fe:
            print(f"Fallback (simple) failed: {fe}")
            raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)} | Fallback error: {str(fe)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "langchain_with_fallback", "timestamp": datetime.now()}