from fastapi import APIRouter, HTTPException
from datetime import datetime
import time
from typing import Dict, Any

from app.models.schemas import (
    WebContentRequest,
    WebContentResponse,
    WebQuestionRequest,
    WebQuestionResponse,
    ErrorResponse
)

router = APIRouter(prefix="/web", tags=["enhanced-web-content"])

# Initialize enhanced web service lazily
_enhanced_web_service = None

def get_enhanced_web_service():
    """Get enhanced web scraping service with lazy initialization"""
    global _enhanced_web_service
    if _enhanced_web_service is None:
        try:
            print("Initializing enhanced web scraping service...")
            from app.services.enhanced_web_scraping_service import get_enhanced_web_service
            _enhanced_web_service = get_enhanced_web_service()
            print("Enhanced web scraping service initialized successfully")
        except Exception as e:
            print(f"Failed to initialize enhanced web service: {e}")
            # Fallback to original service
            try:
                print("Falling back to original web service...")
                from app.services.web_scraping_service import get_web_service
                _enhanced_web_service = get_web_service()
                print("Original web service loaded as fallback")
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                raise HTTPException(status_code=500, detail="Web service initialization failed")
    return _enhanced_web_service

@router.post("/extract-content", response_model=WebContentResponse)
async def extract_web_content(request: WebContentRequest):
    """Extract and summarize content from any website URL using enhanced scraping"""
    try:
        print(f"Enhanced extraction from URL: {request.url}")
        
        start_time = time.time()
        
        # Get enhanced web service
        service = get_enhanced_web_service()
        
        # Extract content with enhanced capabilities
        content_data = await service.extract_content_from_url(request.url)
        
        processing_time = time.time() - start_time
        
        # Enhanced response with more metadata
        metadata = content_data.get("metadata", {})
        metadata.update({
            "processing_time": processing_time,
            "extraction_method": content_data.get("extraction_method", "enhanced"),
            "content_preview_length": min(len(content_data["content"]), 500)
        })
        
        return WebContentResponse(
            url=content_data["url"],
            title=content_data["title"],
            content_preview=content_data["content"][:500] + "..." if len(content_data["content"]) > 500 else content_data["content"],
            word_count=content_data["word_count"],
            extracted_at=datetime.now(),
            metadata=metadata,
            status="success"
        )
        
    except Exception as e:
        print(f"Error in enhanced web content extraction: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Provide more detailed error information
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "url": request.url,
            "timestamp": datetime.now().isoformat()
        }
        
        raise HTTPException(
            status_code=500, 
            detail=f"Enhanced web scraping failed: {str(e)}"
        )

@router.post("/ask-question", response_model=WebQuestionResponse)
async def ask_question_about_web_content(request: WebQuestionRequest):
    """Ask a question about content from any website URL using enhanced analysis"""
    try:
        print(f"Enhanced web content question processing")
        print(f"URL: {request.url}")
        print(f"Question: {request.question}")
        
        start_time = time.time()
        
        # Get enhanced web service
        service = get_enhanced_web_service()
        
        # Process question with enhanced capabilities
        result = await service.ask_question_about_url(request.url, request.question)
        
        processing_time = time.time() - start_time
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error occurred")
            print(f"Enhanced web question processing failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Enhanced response with additional metadata
        return WebQuestionResponse(
            answer=result["answer"],
            url=result["url"],
            title=result["title"],
            question=result["question"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            confidence=result.get("confidence", 0.8),
            source_type=result.get("source_type", "enhanced_web_content"),
            word_count=result["word_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in enhanced web question processing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced web analysis failed: {str(e)}")

@router.get("/health")
async def enhanced_web_service_health():
    """Check if enhanced web scraping service is working"""
    try:
        service = get_enhanced_web_service()
        
        # Quick test with a simple, reliable site
        test_url = "https://example.com"
        test_result = await service.extract_content_from_url(test_url)
        
        return {
            "status": "healthy",
            "service": "enhanced-web-scraping",
            "test_extraction": {
                "url": test_url,
                "success": len(test_result.get("content", "")) > 0,
                "content_length": len(test_result.get("content", "")),
                "title": test_result.get("title", "N/A")
            },
            "timestamp": datetime.now(),
            "capabilities": [
                "enhanced_content_extraction",
                "anti_bot_bypass",
                "retry_logic",
                "multiple_extraction_strategies",
                "improved_metadata_extraction"
            ]
        }
    except Exception as e:
        print(f"Enhanced web service health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Enhanced web service unavailable: {str(e)}"
        )

@router.get("/test-sites")
async def test_multiple_sites():
    """Test the enhanced service with multiple different types of sites"""
    try:
        service = get_enhanced_web_service()
        
        test_sites = [
            ("Simple", "https://example.com"),
            ("Wikipedia", "https://en.wikipedia.org/wiki/Web_scraping"),
            ("News", "https://www.bbc.com/news"),
        ]
        
        results = []
        
        for name, url in test_sites:
            try:
                start_time = time.time()
                result = await service.extract_content_from_url(url)
                processing_time = time.time() - start_time
                
                results.append({
                    "site_type": name,
                    "url": url,
                    "status": "success",
                    "content_length": len(result.get("content", "")),
                    "title": result.get("title", "N/A"),
                    "processing_time": processing_time,
                    "word_count": result.get("word_count", 0)
                })
            except Exception as e:
                results.append({
                    "site_type": name,
                    "url": url,
                    "status": "failed",
                    "error": str(e),
                    "processing_time": 0
                })
        
        success_count = sum(1 for r in results if r["status"] == "success")
        
        return {
            "service": "enhanced-web-scraping",
            "test_summary": {
                "total_sites": len(test_sites),
                "successful": success_count,
                "success_rate": f"{success_count/len(test_sites)*100:.1f}%"
            },
            "detailed_results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        print(f"Multi-site test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-site test failed: {str(e)}"
        )