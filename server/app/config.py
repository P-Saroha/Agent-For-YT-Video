import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "YouTube AI Assistant API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Google Gemini Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-2.5-flash"
    
    # YouTube Configuration
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # Embeddings Configuration
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Caching Configuration (TTL only, no disk cache)
    cache_ttl: int = 3600  # 1 hour
    
    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

@lru_cache()
def get_settings():
    return Settings()
