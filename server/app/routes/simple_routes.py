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

# Initialize LangChain service that follows proper RAG approach
from app.services.langchain_service import LangChainYouTubeService
langchain_service = LangChainYouTubeService()
simple_service = SimpleYouTubeAIService()

@router.post("/summarize", response_model=SimpleResponse)
async def summarize_video(request: VideoSummaryRequest):
    """Generate summary using proper RAG approach: chunking → embeddings → vector store → similarity search → LLM"""
    try:
        # Step 1: Process video with RAG approach (chunking, embeddings, vector store)
        print(f"Processing video with RAG approach: {request.video_url}")
        process_result = await langchain_service.process_video(request.video_url)

        if not process_result.get("video_id"):
            raise HTTPException(status_code=400, detail="Failed to process video")

        print(f"Created {process_result.get('chunks_count', 0)} chunks and stored in vector database")

        # Step 2: Use vector similarity search to retrieve relevant chunks and generate answer
        result = await langchain_service.ask_question(
            video_id=process_result["video_id"],
            question="Please provide a comprehensive summary of this video. Use clear headings, bullet points, bold text for key concepts, and proper paragraph breaks. Include main topics, key points, important details, and conclusions. Format with Markdown for easy reading."
        )

        return SimpleResponse(
            summary=result.get("answer", "Unable to generate summary"),
            video_url=request.video_url,
            status="success"
        )

    except Exception as e:
        # Fallback to simple service with yt-dlp transcript path
        try:
            print(f"RAG summarize failed ({e}); falling back to simple service with yt-dlp…")
            fallback_question = (
                "Please provide a comprehensive summary of this video. Use clear headings, "
                "short paragraphs, and make it readable."
            )
            result = await simple_service.process_video_question(request.video_url, fallback_question)
            if result.get("success"):
                return SimpleResponse(
                    summary=result.get("answer", "Unable to generate summary"),
                    video_url=request.video_url,
                    status="success"
                )
            else:
                raise Exception(result.get("error", "Fallback failed"))
        except Exception as fe:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to summarize video: {str(e)} | Fallback error: {str(fe)}"
            )

@router.post("/ask", response_model=SimpleResponse)
async def ask_video_question(request: VideoQuestionRequest):
    """Answer questions using RAG: query embedding → cosine similarity → retrieve chunks → context-aware LLM response"""
    try:
        # Step 1: Process video with RAG approach if not already processed
        print(f"Processing video with RAG approach: {request.video_url}")
        process_result = await langchain_service.process_video(request.video_url)

        if not process_result.get("video_id"):
            raise HTTPException(status_code=400, detail="Failed to process video")

        print(f"Using vector database with {process_result.get('chunks_count', 0)} embedded chunks")

        # Step 2: Embed query, compute similarity, retrieve top chunks, pass to LLM
        print(f"Query: {request.question}")
        result = await langchain_service.ask_question(
            video_id=process_result["video_id"],
            question=request.question
        )

        print(f"Generated context-aware answer using retrieved chunks")

        return SimpleResponse(
            answer=result.get("answer", "Unable to get answer"),
            video_url=request.video_url,
            status="success"
        )

    except Exception as e:
        # Fallback to simple service with yt-dlp transcript path
        try:
            print(f"RAG ask failed ({e}); falling back to simple service with yt-dlp…")
            result = await simple_service.process_video_question(request.video_url, request.question)
            if result.get("success"):
                return SimpleResponse(
                    answer=result.get("answer", "Unable to get answer"),
                    video_url=request.video_url,
                    status="success"
                )
            else:
                raise Exception(result.get("error", "Fallback failed"))
        except Exception as fe:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process question: {str(e)} | Fallback error: {str(fe)}"
            )
