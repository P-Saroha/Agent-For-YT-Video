"""
Document Analysis Service using LangChain and Google Gemini.

How it works:
1. Extract text from PDF or plain text file
2. Split text into chunks
3. Convert chunks to vectors
4. Answer questions about the document using RAG

Supports:
- PDF files
- Plain text files
"""

import os
import re
import tempfile
import hashlib
from typing import Dict, Any, List
from io import BytesIO

from PyPDF2 import PdfReader

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


class DocumentRAGService:
    """
    Service to analyze documents (PDF, text) using RAG.
    
    RAG = Get relevant information from document, then use AI to answer questions.
    """

    def __init__(self):
        """Initialize components for document analysis."""
        print("📄 Initializing Document Analysis Service...")

        # ==================== Component 1: Text-to-Vector Converter ====================
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32  # Process 32 texts at once (faster)
            }
        )

        # ==================== Component 2: Text Splitter ====================
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,           # Each chunk is 1000 characters
            chunk_overlap=200,         # 200 character overlap between chunks
            separators=["\n\n", "\n", ".", "!", "?", " "]  # Split at these first
        )

        # ==================== Component 3: AI Model (Gemini) ====================
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            convert_system_message_to_human=True
        )

        # ==================== Component 4: Question-Answer Prompt ====================
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant analyzing documents (PDFs, text files).

Here is information from the document:
{context}

Rules:
- Answer the question based ONLY on the document content above
- Be clear and concise
- Use markdown formatting (headers, bold, lists) to make answers readable
- If the answer is not in the document, say "This information is not in the document"
- Sound natural and friendly, like a real person explaining something"""),
            ("human", "{input}")
        ])

        # ==================== Component 5: Memory/Cache ====================
        self.processed_docs = {}       # Maps doc_hash -> metadata
        self.vector_stores = {}         # Maps doc_hash -> vector database

        print("✅ Document Service ready!")

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_content: The PDF file as bytes
            
        Returns:
            Extracted text content
        """
        try:
            print("   Extracting text from PDF...")
            
            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)

            # Extract text from all pages
            pages_text = []
            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"\n--- Page {i+1} ---\n{text}")

            # Combine all pages
            full_text = "".join(pages_text)
            
            # Clean up whitespace
            full_text = re.sub(r'\s+', ' ', full_text)
            
            return full_text

        except Exception as e:
            print(f"   ❌ Error extracting PDF: {str(e)}")
            raise

    async def process_document(
        self, 
        content: str,
        doc_title: str = "Document"
    ) -> Dict[str, Any]:
        """
        Process a document so questions can be asked about it.
        
        Steps:
        1. Split into chunks
        2. Convert to vectors
        3. Store in database
        
        Args:
            content: The document text content
            doc_title: Title of the document
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Create a hash of the content for caching
            doc_hash = hashlib.md5(content.encode()).hexdigest()[:12]
            
            # Check if already processed
            if doc_hash in self.processed_docs:
                print(f"📦 Document already processed (using cached data)")
                return self.processed_docs[doc_hash]

            print(f"📄 Processing document: {doc_title}")

            if len(content) < 100:
                raise Exception("Document content too short")

            # Step 1: Create document
            doc = Document(
                page_content=content,
                metadata={
                    "title": doc_title,
                    "char_count": len(content)
                }
            )

            # Step 2: Split into chunks
            print(f"   1️⃣ Splitting into chunks...")
            chunks = self.text_splitter.split_documents([doc])
            print(f"      Created {len(chunks)} chunks")

            # Step 3: Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"doc_{doc_hash}_")

            # Step 4: Convert to vectors
            print(f"   2️⃣ Converting text to vectors...")
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )

            # Step 5: Create retriever
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 8}  # Return top 8 chunks
            )

            # Step 6: Create RAG chain
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.qa_prompt
            )
            rag_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=document_chain
            )

            # Store in memory
            self.processed_docs[doc_hash] = {
                "title": doc_title,
                "chunks": len(chunks),
                "char_count": len(content),
                "status": "processed"
            }
            self.vector_stores[doc_hash] = {
                "rag_chain": rag_chain,
                "vector_store": vector_store,
                "temp_dir": temp_dir,
                "title": doc_title
            }

            print(f"✅ Document processed successfully!")

            return self.processed_docs[doc_hash]

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            raise

    async def ask_question(
        self,
        content: str,
        question: str,
        doc_title: str = "Document"
    ) -> Dict[str, Any]:
        """
        Ask a question about a document.
        
        Args:
            content: The document text content
            question: The question to ask
            doc_title: Title of the document
            
        Returns:
            Dictionary with the answer and metadata
        """
        try:
            doc_hash = hashlib.md5(content.encode()).hexdigest()[:12]

            # Make sure document is processed
            if doc_hash not in self.vector_stores:
                await self.process_document(content, doc_title)

            print(f"❓ Question: {question[:50]}...")

            # Get the RAG chain
            chain_data = self.vector_stores[doc_hash]
            rag_chain = chain_data["rag_chain"]

            # Ask the question
            result = rag_chain.invoke({"input": question})

            answer = result["answer"]
            source_docs = result.get("context", [])

            print(f"✅ Generated answer using {len(source_docs)} relevant sections")

            return {
                "question": question,
                "answer": answer,
                "sources_used": len(source_docs),
                "document_title": doc_title,
                "method": "RAG"
            }

        except Exception as e:
            print(f"❌ Error answering question: {str(e)}")
            raise

    async def summarize_document(
        self,
        content: str,
        doc_title: str = "Document"
    ) -> Dict[str, Any]:
        """
        Generate a summary of the entire document.
        
        Args:
            content: The document text content
            doc_title: Title of the document
            
        Returns:
            Dictionary with the summary
        """
        try:
            # Ask for summary
            summary_question = """Create a clear, well-organized summary of this document.

Format your response as:

## 📝 Overview
[2-3 sentences about what this document covers]

## 🎯 Main Topics
- Topic 1: [Explanation]
- Topic 2: [Explanation]
- Topic 3: [Explanation]

## 💡 Key Points
1. [Important point 1]
2. [Important point 2]
3. [Important point 3]

## 📌 Summary
[Final summary paragraph]"""

            result = await self.ask_question(content, summary_question, doc_title)
            
            return {
                "document_title": doc_title,
                "summary": result["answer"]
            }

        except Exception as e:
            print(f"❌ Error summarizing document: {str(e)}")
            raise

    async def cleanup_document(self, doc_hash: str):
        """Clean up resources for a specific document."""
        try:
            if doc_hash in self.vector_stores:
                chain_data = self.vector_stores[doc_hash]
                temp_dir = chain_data["temp_dir"]
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)

            # Remove from memory
            if doc_hash in self.processed_docs:
                del self.processed_docs[doc_hash]
            if doc_hash in self.vector_stores:
                del self.vector_stores[doc_hash]

            print(f"🧹 Cleaned up document")
        except Exception as e:
            print(f"⚠️ Error cleaning up: {str(e)}")


def get_document_service() -> DocumentRAGService:
    """
    Get an instance of the Document RAG service.
    
    Usage:
        service = get_document_service()
        await service.process_document(content, "My Document")
        result = await service.ask_question(content, "What is this about?")
    """
    return DocumentRAGService()
