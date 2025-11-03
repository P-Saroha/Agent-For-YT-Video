"""
OPTIMIZED RAG-based Document Analysis Service
Following LangChain Best Practices with LCEL (LangChain Expression Language)
Supports: PDFs, Plain Text - Efficient, Modern, Scalable
"""
import os
import re
import tempfile
import time
import hashlib
from typing import Dict, Any, List
from io import BytesIO

# PDF processing
from PyPDF2 import PdfReader

# Modern LangChain imports (LCEL)
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


class OptimizedDocumentAIService:
    """
    Optimized AI Assistant for PDF and Text Documents
    Using Modern LangChain Patterns (LCEL) for Maximum Efficiency
    """
    
    def __init__(self):
        print("🚀 Initializing Optimized Document AI Service with LCEL...")
        
        # Configure text splitter with optimal settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""]
        )
        
        # Use multilingual embeddings with caching
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={
                'device': 'cpu',
                'trust_remote_code': False
            },
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32  # Optimize batch processing
            },
            show_progress=False
        )
        
        # Initialize Gemini LLM with optimal settings
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            convert_system_message_to_human=True,
            max_output_tokens=2048,
            top_p=0.95
        )
        
        # Modern ChatPromptTemplate - Simple and natural like ChatGPT/Claude
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant analyzing documents (PDFs, text files). Answer questions naturally and conversationally, like ChatGPT or Claude.

Context:
{context}

Instructions:
- Write in a natural, conversational tone
- Use markdown for formatting (headers, bold, lists) when helpful
- Break long responses into clear paragraphs
- Use **bold** to emphasize important points
- Use bullet points or numbered lists when listing items
- Keep your language simple and easy to understand
- Only include information from the context provided
- If something isn't in the context, say so

Respond naturally and helpfully, as if you're having a conversation."""),
            ("human", "{input}")
        ])
        
        # Document cache for reuse
        self.document_cache = {}
        self.vectorstore_cache = {}
        
        print("✅ Optimized Document AI Service initialized successfully")
    
    def _clean_text(self, text: str) -> str:
        """Improve and clean AI response formatting (KEEP markdown)"""
        if not text:
            return ""
        
        # Keep markdown but fix common issues
        # Fix header spacing
        text = re.sub(r'(#{1,6})\s*([^\n]+)', r'\1 \2', text)  # Ensure space after #
        text = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', text)  # Add line before headers
        text = re.sub(r'(#{1,6}[^\n]+)\n([^\n#])', r'\1\n\n\2', text)  # Add line after headers
        
        # Fix list formatting
        text = re.sub(r'\n([•\-\*]\s)', r'\n\1', text)  # Ensure spacing before lists
        
        # Fix bold/italic spacing
        text = re.sub(r'(\*\*[^*]+\*\*)\s*(\*\*)', r'\1 \2', text)  # Space between bold items
        
        # Clean up excessive spacing
        text = re.sub(r'\n{4,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' {2,}', ' ', text)  # Remove multiple spaces
        text = re.sub(r'\t+', ' ', text)  # Replace tabs with space
        
        # Fix paragraph spacing
        text = re.sub(r'([.!?])\n([A-Z])', r'\1\n\n\2', text)  # Add space between sentences
        
        return text.strip()
    
    async def extract_text_from_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """
        Optimized PDF text extraction with metadata
        """
        try:
            print("📄 Extracting text from PDF...")
            start_time = time.time()
            
            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            page_count = len(pdf_reader.pages)
            metadata = pdf_reader.metadata or {}
            
            # Parallel-like extraction (list comprehension is faster than loop)
            pages_text = [
                f"\n--- Page {i+1} ---\n{page.extract_text()}"
                for i, page in enumerate(pdf_reader.pages)
                if page.extract_text()
            ]
            
            text_content = "".join(pages_text)
            text_content = self._clean_text(text_content)
            
            extraction_time = time.time() - start_time
            
            print(f"✅ Extracted {len(text_content)} characters from {page_count} pages ({extraction_time:.2f}s)")
            
            return {
                "text": text_content,
                "page_count": page_count,
                "char_count": len(text_content),
                "title": metadata.get("/Title", "Untitled"),
                "author": metadata.get("/Author", "Unknown"),
                "extraction_time": extraction_time
            }
            
        except Exception as e:
            print(f"❌ Error extracting PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _create_vectorstore(
        self,
        chunks: List[Document],
        doc_hash: str
    ) -> Chroma:
        """
        Optimized vectorstore creation with proper configuration
        """
        temp_dir = tempfile.mkdtemp(prefix=f"doc_{doc_hash[:8]}_")
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=temp_dir,
            collection_name=f"doc_{doc_hash[:12]}"
        )
        
        return vectorstore
    
    async def process_document_with_rag(
        self,
        text_content: str,
        document_title: str = "Document",
        document_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Optimized RAG processing using modern LangChain patterns
        """
        try:
            print(f"📊 Processing {document_type} with optimized RAG...")
            start_time = time.time()
            
            doc_hash = hashlib.md5(text_content.encode()).hexdigest()
            
            # Check cache first
            if doc_hash in self.document_cache:
                print(f"✅ Using cached document ({time.time() - start_time:.2f}s)")
                return self.document_cache[doc_hash]
            
            # Create document with metadata
            document = Document(
                page_content=text_content,
                metadata={
                    "title": document_title,
                    "type": document_type,
                    "char_count": len(text_content),
                    "doc_hash": doc_hash
                }
            )
            
            # Chunk documents
            chunking_start = time.time()
            chunks = self.text_splitter.split_documents([document])
            print(f"📝 Created {len(chunks)} chunks ({time.time() - chunking_start:.2f}s)")
            
            # Create vectorstore
            embedding_start = time.time()
            print(f"🔢 Creating vector embeddings...")
            vectorstore = self._create_vectorstore(chunks, doc_hash)
            print(f"✅ Embeddings created ({time.time() - embedding_start:.2f}s)")
            
            # Create optimized retriever
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 8  # Top 8 most relevant chunks
                }
            )
            
            # Modern LCEL chain composition
            # This is the proper way to build chains in modern LangChain
            question_answer_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.qa_prompt
            )
            
            # Create retrieval chain using the new API
            rag_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=question_answer_chain
            )
            
            # Cache everything for reuse
            self.document_cache[doc_hash] = {
                "doc_hash": doc_hash,
                "title": document_title,
                "type": document_type,
                "chunks_count": len(chunks),
                "char_count": len(text_content),
                "rag_chain": rag_chain,
                "retriever": retriever,
                "vectorstore": vectorstore,
                "metadata": document.metadata
            }
            
            print(f"✅ Document processed ({time.time() - start_time:.2f}s)")
            
            return self.document_cache[doc_hash]
            
        except Exception as e:
            print(f"❌ Error processing document: {e}")
            raise Exception(f"Failed to process document: {str(e)}")
    
    async def ask_question_about_document(
        self,
        text_content: str,
        question: str,
        document_title: str = "Document",
        document_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Answer questions using optimized LCEL chain
        """
        try:
            print(f"❓ Processing question: {question}")
            
            # Process or retrieve cached document
            doc_data = await self.process_document_with_rag(
                text_content=text_content,
                document_title=document_title,
                document_type=document_type
            )
            
            print(f"🔍 Querying vector database with {doc_data['chunks_count']} chunks...")
            
            # Use the modern LCEL chain
            rag_chain = doc_data["rag_chain"]
            
            # Invoke chain with proper input format
            result = rag_chain.invoke({"input": question})
            
            # Extract answer and source documents
            answer = result.get("answer", "Unable to generate answer")
            context_docs = result.get("context", [])
            
            # Clean answer
            answer = self._clean_text(answer)
            
            print(f"✅ Generated answer using {len(context_docs)} chunks")
            
            return {
                "success": True,
                "answer": answer,
                "question": question,
                "document_title": doc_data["title"],
                "document_type": doc_data["type"],
                "confidence": 0.85,
                "chunks_used": len(context_docs),
                "total_chunks": doc_data["chunks_count"],
                "char_count": doc_data["char_count"],
                "metadata": doc_data["metadata"]
            }
            
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def summarize_document(
        self,
        text_content: str,
        document_title: str = "Document",
        document_type: str = "text"
    ) -> Dict[str, Any]:
        """Generate comprehensive summary"""
        summary_question = (
            "Provide a comprehensive summary of this document with proper formatting.\n\n"
            "Format your response as follows:\n\n"
            "# Document Summary\n\n"
            "## Overview\n"
            "[Brief 2-3 sentence overview]\n\n"
            "## Main Topics\n"
            "- **Topic 1:** [description]\n"
            "- **Topic 2:** [description]\n\n"
            "## Key Points\n"
            "1. [First important point with details]\n"
            "2. [Second important point with details]\n\n"
            "## Important Details\n"
            "- [Detail 1]\n"
            "- [Detail 2]\n\n"
            "Use clear headings, bullet points, and proper spacing for readability."
        )
        
        return await self.ask_question_about_document(
            text_content=text_content,
            question=summary_question,
            document_title=document_title,
            document_type=document_type
        )
    
    async def close(self):
        """Cleanup resources efficiently"""
        import shutil
        
        for doc_data in self.document_cache.values():
            vectorstore = doc_data.get("vectorstore")
            if vectorstore and hasattr(vectorstore, '_persist_directory'):
                persist_dir = vectorstore._persist_directory
                if persist_dir and os.path.exists(persist_dir):
                    shutil.rmtree(persist_dir, ignore_errors=True)
        
        self.document_cache.clear()
        self.vectorstore_cache.clear()
        print("✅ Document service cleanup complete")


# Singleton pattern for efficiency
_document_service = None

def get_document_service():
    """Get or create document service instance (optimized with LCEL)"""
    global _document_service
    if _document_service is None:
        _document_service = OptimizedDocumentAIService()
    return _document_service

# Backward compatibility aliases
def get_optimized_document_service():
    """Legacy name - use get_document_service() instead"""
    return get_document_service()

# Class name backward compatibility
DocumentAIService = OptimizedDocumentAIService
