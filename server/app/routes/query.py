from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import time
import asyncio
from typing import Dict, Any

from app.models.schemas import (
    VideoProcessRequest, 
    VideoProcessResponse, 
    QuestionRequest, 
    QuestionResponse,
    ErrorResponse
)
from app.services.transcript import TranscriptService
from app.services.simple_embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.gemini_qa import GeminiQuestionAnsweringService
from app.services.chunking import ChunkingService

router = APIRouter(tags=["query"])

# Initialize services
transcript_service = TranscriptService()
embedding_service = EmbeddingService()
vectorstore_service = VectorStoreService()
qa_service = GeminiQuestionAnsweringService()
chunking_service = ChunkingService()

# Store processed videos (in production, use a database)
processed_videos: Dict[str, Dict[str, Any]] = {}

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    """Process a YouTube video for Q&A"""
    try:
        # Extract video ID
        video_id = extract_video_id(request.video_url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Check if already processed
        if video_id in processed_videos:
            video_data = processed_videos[video_id]
            return VideoProcessResponse(
                video_id=video_id,
                title=video_data["title"],
                channel=video_data["channel"],
                duration=video_data.get("duration"),
                processed_at=video_data["processed_at"],
                chunks_count=video_data["chunks_count"],
                status="already_processed"
            )
        
        # Process video in background
        background_tasks.add_task(process_video_background, video_id, request.video_url)
        
        # Return immediate response (in production, you might want to implement polling)
        return VideoProcessResponse(
            video_id=video_id,
            title="Processing...",
            channel="",
            processed_at=datetime.now(),
            chunks_count=0,
            status="processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_background(video_id: str, video_url: str):
    """Background task to process video"""
    try:
        print(f"Starting to process video: {video_id}")
        
        # Get transcript
        transcript_data = await transcript_service.get_transcript(video_id)
        
        # Chunk the transcript
        chunks = chunking_service.chunk_transcript(transcript_data["transcript"])
        
        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings([chunk["text"] for chunk in chunks])
        
        # Store in vector database
        await vectorstore_service.store_video_chunks(video_id, chunks, embeddings)
        
        # Store processed video info
        processed_videos[video_id] = {
            "title": transcript_data.get("title", "Unknown Title"),
            "channel": transcript_data.get("channel", "Unknown Channel"),
            "duration": transcript_data.get("duration"),
            "processed_at": datetime.now(),
            "chunks_count": len(chunks),
            "video_url": video_url
        }
        
        print(f"Successfully processed video: {video_id}")
        
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        # Store error status
        processed_videos[video_id] = {
            "title": "Processing Failed",
            "channel": "",
            "processed_at": datetime.now(),
            "chunks_count": 0,
            "error": str(e)
        }

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about a processed video"""
    try:
        start_time = time.time()
        
        # Check if video is processed
        if request.video_id not in processed_videos:
            raise HTTPException(status_code=404, detail="Video not found or not processed")
        
        video_data = processed_videos[request.video_id]
        if "error" in video_data:
            raise HTTPException(status_code=400, detail=f"Video processing failed: {video_data['error']}")
        
        # Get relevant chunks from vector store
        relevant_chunks = await vectorstore_service.search_similar_chunks(
            request.video_id, 
            request.question, 
            top_k=5
        )
        
        # Generate answer using QA service
        answer_data = await qa_service.generate_answer(request.question, relevant_chunks)
        
        response_time = time.time() - start_time
        
        return QuestionResponse(
            question=request.question,
            answer=answer_data["answer"],
            confidence=answer_data["confidence"],
            sources=relevant_chunks,
            response_time=response_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/{video_id}/status")
async def get_video_status(video_id: str):
    """Get processing status of a video"""
    if video_id not in processed_videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return processed_videos[video_id]

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    import re
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None
