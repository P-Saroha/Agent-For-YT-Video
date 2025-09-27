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
    gemini_api_key: str = "AIzaSyBMBY7KhVxHZy4j66tBoiT9r0Bk4IQznq8"
    gemini_model: str = "gemini-pro"
    
    # YouTube Configuration
    youtube_api_key: str = ""
    
    # Vector Store Configuration
    vector_store_path: str = "store/faiss"
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Caching Configuration
    cache_dir: str = "store/cache"
    cache_ttl: int = 3600  # 1 hour
    
    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()
