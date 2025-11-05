"""
Document Processing Routes - PDF and Text Analysis
Endpoints for uploading PDFs, submitting text, and asking questions
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
import time
from typing import Dict, Any

from app.models.schemas import (
    TextDocumentRequest,
    DocumentQuestionRequest,
    DocumentResponse,
    PDFUploadResponse,
    ErrorResponse
)

router = APIRouter(prefix="/document", tags=["document-processing"])

# Initialize document service lazily
_document_service = None

def get_document_service():
    """Get document service with lazy initialization"""
    global _document_service
    if _document_service is None:
        try:
            print("Initializing Document AI service...")
            from app.services.document_service import DocumentAIService
            _document_service = DocumentAIService()
            print(" Document AI service initialized successfully")
        except Exception as e:
            print(f" Failed to initialize Document service: {e}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    return _document_service


@router.post("/pdf/upload", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and extract text from PDF file
    Returns extraction metadata
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        print(f" Received PDF upload: {file.filename}")

        # Read file content
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty PDF file")

        print(f" File size: {len(file_content) / 1024:.2f} KB")

        # Get service and extract text
        service = get_document_service()
        extraction_result = await service.extract_text_from_pdf(file_content)

        return PDFUploadResponse(
            success=True,
            message=f"Successfully extracted text from {extraction_result['page_count']} pages",
            page_count=extraction_result['page_count'],
            char_count=extraction_result['char_count'],
            title=extraction_result['title'],
            extraction_time=extraction_result['extraction_time']
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


@router.post("/pdf/ask-question", response_model=DocumentResponse)
async def ask_pdf_question(
    file: UploadFile = File(...),
    question: str = Form(...)
):
    """
    Upload PDF and ask a question about it
    Uses RAG approach: PDF extraction → chunking → embeddings → vector search → LLM
    """
    try:
        # Validate inputs
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        print(f" Processing PDF question: {file.filename}")
        print(f" Question: {question}")

        start_time = time.time()

        # Read PDF
        file_content = await file.read()

        # Get service
        service = get_document_service()

        # Extract text from PDF
        extraction_result = await service.extract_text_from_pdf(file_content)
        text_content = extraction_result['text']
        document_title = extraction_result.get('title', file.filename)

        # Ask question using RAG
        result = await service.ask_question_about_document(
            text_content=text_content,
            question=question,
            document_title=document_title,
            document_type="pdf"
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process question"))

        processing_time = time.time() - start_time

        return DocumentResponse(
            answer=result["answer"],
            document_title=result["document_title"],
            document_type=result["document_type"],
            question=question,
            char_count=result["char_count"],
            chunks_count=result["total_chunks"],
            chunks_used=result["chunks_used"],
            confidence=result["confidence"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Error processing PDF question: {e}")
        raise HTTPException(status_code=500, detail=f"PDF question processing failed: {str(e)}")


@router.post("/text/ask-question", response_model=DocumentResponse)
async def ask_text_question(request: DocumentQuestionRequest):
    """
    Submit text and ask a question about it
    Uses RAG approach: text → chunking → embeddings → vector search → LLM
    """
    try:
        # Validate inputs
        if not request.text_content or not request.text_content.strip():
            raise HTTPException(status_code=400, detail="Text content is required")

        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question is required")

        print(f" Processing text question")
        print(f" Text length: {len(request.text_content)} characters")
        print(f" Question: {request.question}")

        start_time = time.time()

        # Get service
        service = get_document_service()

        # Ask question using RAG
        result = await service.ask_question_about_document(
            text_content=request.text_content,
            question=request.question,
            document_title=request.document_title,
            document_type="text"
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process question"))

        processing_time = time.time() - start_time

        return DocumentResponse(
            answer=result["answer"],
            document_title=result["document_title"],
            document_type=result["document_type"],
            question=request.question,
            char_count=result["char_count"],
            chunks_count=result["total_chunks"],
            chunks_used=result["chunks_used"],
            confidence=result["confidence"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Error processing text question: {e}")
        raise HTTPException(status_code=500, detail=f"Text question processing failed: {str(e)}")


@router.post("/text/summarize", response_model=DocumentResponse)
async def summarize_text(request: TextDocumentRequest):
    """
    Submit text and get a comprehensive summary
    Uses RAG approach for intelligent summarization
    """
    try:
        # Validate input
        if not request.text_content or not request.text_content.strip():
            raise HTTPException(status_code=400, detail="Text content is required")

        print(f" Generating summary for text document")
        print(f" Text length: {len(request.text_content)} characters")

        start_time = time.time()

        # Get service
        service = get_document_service()

        # Generate summary
        result = await service.summarize_document(
            text_content=request.text_content,
            document_title=request.document_title,
            document_type="text"
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate summary"))

        processing_time = time.time() - start_time

        return DocumentResponse(
            answer=result["answer"],
            document_title=result["document_title"],
            document_type=result["document_type"],
            question="Summary",
            char_count=result["char_count"],
            chunks_count=result["total_chunks"],
            chunks_used=result["chunks_used"],
            confidence=result["confidence"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/pdf/summarize", response_model=DocumentResponse)
async def summarize_pdf(file: UploadFile = File(...)):
    """
    Upload PDF and get a comprehensive summary
    Uses RAG approach for intelligent summarization
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        print(f" Generating summary for PDF: {file.filename}")

        start_time = time.time()

        # Read PDF
        file_content = await file.read()

        # Get service
        service = get_document_service()

        # Extract text from PDF
        extraction_result = await service.extract_text_from_pdf(file_content)
        text_content = extraction_result['text']
        document_title = extraction_result.get('title', file.filename)

        # Generate summary
        result = await service.summarize_document(
            text_content=text_content,
            document_title=document_title,
            document_type="pdf"
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate summary"))

        processing_time = time.time() - start_time

        return DocumentResponse(
            answer=result["answer"],
            document_title=result["document_title"],
            document_type=result["document_type"],
            question="Summary",
            char_count=result["char_count"],
            chunks_count=result["total_chunks"],
            chunks_used=result["chunks_used"],
            confidence=result["confidence"],
            processing_time=processing_time,
            answered_at=datetime.now(),
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f" Error generating PDF summary: {e}")
        raise HTTPException(status_code=500, detail=f"PDF summary generation failed: {str(e)}")


@router.get("/health")
async def document_service_health():
    """Check if document processing service is working"""
    try:
        service = get_document_service()
        return {
            "status": "healthy",
            "service": "document-processing",
            "features": ["pdf-upload", "text-input", "question-answering", "summarization"],
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
