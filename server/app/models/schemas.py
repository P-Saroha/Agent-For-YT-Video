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
    video_id: str
    question: str

class QuestionResponse(BaseModel):
    answer: str
    video_id: str
    question: str
    processing_time: float
    answered_at: datetime
    confidence: float
    source_type: str

# New schemas for web content processing
class WebContentRequest(BaseModel):
    url: str

class WebContentResponse(BaseModel):
    url: str
    title: str
    content_preview: str  # First 500 chars
    word_count: int
    extracted_at: datetime
    metadata: Dict[str, Any]
    status: str

class WebQuestionRequest(BaseModel):
    url: str
    question: str

class WebQuestionResponse(BaseModel):
    answer: str
    url: str
    title: str
    question: str
    processing_time: float
    answered_at: datetime
    confidence: float
    source_type: str
    word_count: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
