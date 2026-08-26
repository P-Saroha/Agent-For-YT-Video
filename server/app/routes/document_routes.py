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
import hashlib
from typing import Dict, Any
from pydantic import BaseModel

# In-memory PDF storage (filename -> content mapping)
PDF_STORAGE: Dict[str, bytes] = {}

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
    """
    try:
        print(f"Uploading PDF: {file.filename}")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files supported")

        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")

        file_content = await file.read()
        
        # Store PDF in memory for later questions
        PDF_STORAGE[file.filename] = file_content
        
        service = get_document_service()
        
        # Extract text from PDF
        pdf_text = service._extract_text_from_pdf(file_content)
        
        # Process the document
        result = await service.process_document(pdf_text, doc_title=file.filename)

        return {
            "success": True,
            "file_name": file.filename,
            "file_size": len(file_content),
            "chunks": result.get("chunks", 0),
            "message": "PDF uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")


@router.post("/pdf/ask")
async def ask_pdf_question(request: AskPDFQuestionRequest) -> Dict[str, Any]:
    """
    Ask a question about a PDF document.
    
    Args:
        file_name: Name of the uploaded PDF file
        question: The question to ask
        
    Returns:
        Dictionary with the answer and metadata
    """
    try:
        print(f"Question about document: {request.question[:50]}...")

        # Validate inputs
        if not request.file_name or not request.file_name.strip():
            raise HTTPException(status_code=400, detail="File name is required")
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        # Check if PDF was uploaded
        if request.file_name not in PDF_STORAGE:
            raise HTTPException(status_code=404, detail="PDF not found. Please upload it first.")

        start_time = time.time()

        # Get the service
        service = get_document_service()
        
        # Get stored PDF content
        pdf_content = PDF_STORAGE[request.file_name]
        
        # Extract text
        pdf_text = service._extract_text_from_pdf(pdf_content)

        # Ask question about the document
        result = await service.ask_question(
            pdf_text,
            request.question,
            doc_title=request.file_name
        )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "document": request.file_name,
            "question": request.question,
            "answer": result.get("answer", "No answer generated"),
            "sources_used": result.get("sources_used", 0),
            "processing_time": f"{processing_time:.2f}s"
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"Error answering PDF question: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {error_msg}"
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
