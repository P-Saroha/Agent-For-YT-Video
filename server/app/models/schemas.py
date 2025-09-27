from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class VideoProcessRequest(BaseModel):
    video_url: str

class VideoProcessResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    processed_at: datetime
    chunks_count: int
    status: str
    language: str

class QuestionRequest(BaseModel):
    video_url: str  # Change from video_id to video_url
    question: str

class QuestionResponse(BaseModel):
    answer: str
    video_id: str
    question: str
    processing_time: float
    answered_at: datetime
    confidence: float
    source_type: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
