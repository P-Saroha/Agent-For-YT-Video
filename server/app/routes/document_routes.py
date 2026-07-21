"""
Document Analysis Routes

Endpoints:
- POST /documents/pdf/upload - Upload a PDF for analysis
- POST /documents/pdf/ask - Ask a question about a PDF
- POST /documents/text/ask - Ask a question about plain text
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from datetime import datetime
import time
from typing import Dict, Any
from pydantic import BaseModel

# ==================== Data Models ====================
class AskPDFQuestionRequest(BaseModel):
    """Request to ask a question about a PDF"""
    file_name: str
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "document.pdf",
                "question": "What is the main topic?"
            }
        }


class AskTextQuestionRequest(BaseModel):
    """Request to ask a question about plain text"""
    text_content: str
    question: str
    doc_title: str = "Document"
    
    class Config:
        json_schema_extra = {
            "example": {
                "text_content": "This is a sample document...",
                "question": "What is the main topic?",
                "doc_title": "Sample"
            }
        }


class SummarizeTextRequest(BaseModel):
    """Request to summarize plain text"""
    text_content: str
    doc_title: str = "Document"
    
    class Config:
        json_schema_extra = {
            "example": {
                "text_content": "This is a sample document...",
                "doc_title": "Sample"
            }
        }


# ==================== Create Router ====================
router = APIRouter(prefix="/documents", tags=["Documents"])


# ==================== Helper Function ====================
def get_document_service():
    """Get Document RAG service instance."""
    from app.services.document_service import get_document_service as _get_service
    return _get_service()


# ==================== Endpoints ====================

@router.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a PDF file for analysis.
    
    This endpoint:
    1. Accepts a PDF file
    2. Extracts text from all pages
    3. Splits into chunks
    4. Converts to vectors
    5. Stores in a database
    
    After uploading, you can ask questions about the PDF.
    
    Args:
        file: The PDF file to upload
        
    Returns:
        Dictionary with upload status and file info
    """
    try:
        print(f"📄 Uploading PDF: {file.filename}")
        start_time = time.time()

        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=413,
                detail="File too large (max 50MB)"
            )

        # Read file content
        file_content = await file.read()

        # Get the service
        service = get_document_service()

        # Extract text from PDF
        pdf_data = await service.extract_text_from_pdf(file_content)

        # Process the document
        result = await service.process_document(
            pdf_data["text"],
            doc_title=file.filename
        )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "file_name": file.filename,
            "file_size": len(file_content),
            "pages": pdf_data.get("page_count", 0),
            "chunks": result.get("chunks", 0),
            "processing_time": f"{processing_time:.2f}s",
            "message": "PDF uploaded successfully. You can now ask questions about it."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload PDF: {str(e)}"
        )


@router.post("/pdf/ask")
async def ask_pdf_question(request: AskPDFQuestionRequest) -> Dict[str, Any]:
    """
    Ask a question about a previously uploaded PDF.
    
    Args:
        file_name: Name of the uploaded PDF file
        question: The question to ask
        
    Returns:
        Dictionary with the answer and metadata
    """
    try:
        print(f"❓ Question about PDF: {request.question[:50]}...")

        # Validate inputs
        if not request.file_name or not request.file_name.strip():
            raise HTTPException(status_code=400, detail="File name is required")
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        raise HTTPException(
            status_code=501,
            detail="PDF question answering requires file storage. Please upload the PDF again with your question, or use the /text/ask endpoint."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error answering PDF question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/text/ask")
async def ask_text_question(request: AskTextQuestionRequest) -> Dict[str, Any]:
    """
    Ask a question about plain text content.
    
    You can paste any text here (article, book chapter, etc.) 
    and ask questions about it.
    
    Args:
        text_content: The text to analyze
        question: The question to ask
        doc_title: Optional title of the document
        
    Returns:
        Dictionary with the answer and metadata
    """
    try:
        print(f"❓ Question: {request.question[:50]}...")
        
        # Validate inputs
        if not request.text_content or not request.text_content.strip():
            raise HTTPException(status_code=400, detail="Text content is required")
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        start_time = time.time()

        # Get the service
        service = get_document_service()

        # Ask the question
        result = await service.ask_question(
            request.text_content,
            request.question,
            doc_title=request.doc_title
        )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "document": request.doc_title,
            "question": request.question,
            "answer": result.get("answer", "No answer generated"),
            "sources_used": result.get("sources_used", 0),
            "processing_time": f"{processing_time:.2f}s",
            "method": result.get("method", "RAG")
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error answering question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/text/summarize")
async def summarize_text(request: SummarizeTextRequest) -> Dict[str, Any]:
    """
    Generate a summary of plain text content.
    
    Args:
        text_content: The text to summarize
        doc_title: Optional title of the document
        
    Returns:
        Dictionary with the summary
    """
    try:
        print(f"📝 Summarizing text...")
        
        # Validate input
        if not request.text_content or not request.text_content.strip():
            raise HTTPException(status_code=400, detail="Text content is required")

        start_time = time.time()

        # Get the service
        service = get_document_service()

        # Generate summary
        result = await service.summarize_document(
            request.text_content,
            doc_title=request.doc_title
        )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "document": request.doc_title,
            "summary": result.get("summary", "No summary generated"),
            "processing_time": f"{processing_time:.2f}s"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error summarizing text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check if the Document service is running.
    
    Returns:
        Dictionary with health status
    """
    try:
        service = get_document_service()
        return {
            "status": "healthy",
            "service": "Document RAG",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
