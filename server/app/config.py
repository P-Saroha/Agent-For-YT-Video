"""
Configuration settings for the AI Content Analysis application.
Loads all settings from environment variables or .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    Example in .env:
        GEMINI_API_KEY=your_key_here
        YOUTUBE_API_KEY=your_key_here
    """
    
    # ==================== Server Configuration ====================
    host: str = "0.0.0.0"           # Server host (accessible on all IPs)
    port: int = 8000                # Server port
    debug: bool = False              # Debug mode
    
    # ==================== API Keys (from .env file) ====================
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # ==================== AI Model Configuration ====================
    gemini_model: str = "gemini-2.5-flash"  # Google's free, fast LLM
    
    # ==================== Embeddings Configuration ====================
    # HuggingFace model for converting text to vectors
    embeddings_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # ==================== Text Chunking Configuration ====================
    # How to split documents into smaller pieces for better processing
    chunk_size: int = 1000           # Size of each text chunk
    chunk_overlap: int = 200         # Overlap between chunks to maintain context
    
    # ==================== Caching Configuration ====================
    cache_ttl: int = 3600            # Cache time-to-live: 1 hour (3600 seconds)
    
    # ==================== Pydantic Configuration ====================
    class Config:
        env_file = ".env"                    # Load from .env file
        env_file_encoding = "utf-8"          # Use UTF-8 encoding
        extra = "ignore"                     # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached for performance).
    
    This function is cached so the settings are only loaded once
    when the app starts, not on every request.
    
    Returns:
        Settings: Application configuration object
    """
    return Settings()
