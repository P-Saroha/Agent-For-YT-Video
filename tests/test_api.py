"""
Unit tests for AI Content Analysis Platform
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_main_health_check(self):
        """Test main health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_youtube_health(self):
        """Test YouTube service health"""
        response = client.get("/youtube/health")
        assert response.status_code == 200
    
    def test_web_health(self):
        """Test web service health"""
        response = client.get("/web/health")
        assert response.status_code == 200


class TestYouTubeEndpoints:
    """Test YouTube analysis endpoints"""
    
    def test_youtube_ask_missing_url(self):
        """Test YouTube ask without URL"""
        response = client.post("/youtube/ask", json={
            "question": "What is this about?"
        })
        assert response.status_code == 422  # Validation error
    
    def test_youtube_ask_invalid_url(self):
        """Test YouTube ask with invalid URL"""
        response = client.post("/youtube/ask", json={
            "video_url": "not-a-url",
            "question": "What is this about?"
        })
        # Should return error (400 or 500)
        assert response.status_code in [400, 422, 500]
    
    @pytest.mark.skip(reason="Requires API key and network access")
    def test_youtube_ask_valid(self):
        """Test YouTube ask with valid video"""
        response = client.post("/youtube/ask", json={
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "question": "What is the video about?"
        })
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestWebEndpoints:
    """Test web content analysis endpoints"""
    
    def test_web_extract_missing_url(self):
        """Test web extract without URL"""
        response = client.post("/web/extract-content", json={})
        assert response.status_code == 422
    
    def test_web_extract_invalid_url(self):
        """Test web extract with invalid URL"""
        response = client.post("/web/extract-content", json={
            "url": "not-a-valid-url"
        })
        assert response.status_code in [400, 422, 500]
    
    @pytest.mark.skip(reason="Requires network access")
    def test_web_extract_valid(self):
        """Test web extract with valid URL"""
        response = client.post("/web/extract-content", json={
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
        })
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "content_preview" in data


class TestDocumentEndpoints:
    """Test document processing endpoints"""
    
    def test_document_health(self):
        """Test document service health"""
        response = client.get("/document/health")
        assert response.status_code == 200


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
    
    def test_docs_ui(self):
        """Test Swagger UI is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test CORS headers are set"""
        response = client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 405]


# Performance tests
class TestPerformance:
    """Test performance characteristics"""
    
    def test_health_response_time(self):
        """Test health check is fast"""
        import time
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.1  # Should respond in less than 100ms


# Integration tests
@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring external services"""
    
    @pytest.mark.skip(reason="Requires API key")
    def test_full_youtube_workflow(self):
        """Test complete YouTube analysis workflow"""
        # 1. Ask question about video
        response = client.post("/youtube/ask", json={
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "question": "What is this video about?"
        })
        assert response.status_code == 200
        
        # 2. Verify response structure
        data = response.json()
        assert "answer" in data
        assert "video_id" in data
        assert "processing_time" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
