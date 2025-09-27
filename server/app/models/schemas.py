from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class VideoProcessRequest(BaseModel):
    video_url: str

class VideoProcessResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    duration: Optional[str] = None
    processed_at: datetime
    chunks_count: int
    status: str = "success"

class QuestionRequest(BaseModel):
    video_id: str
    question: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    response_time: float

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
