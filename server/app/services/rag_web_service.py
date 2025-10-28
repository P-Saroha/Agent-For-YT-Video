"""
RAG-based web content analysis service
Following proper approach: chunking → embeddings → vector store → similarity search → LLM
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import time
import tempfile
import unicodedata
from typing import Optional, Dict, Any

# RAG components
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import os

class RAGWebContentService:
    """Web content analysis using proper RAG approach"""
    
    def __init__(self):
        self.session = None
        
        # RAG Components - Following your exact specification
        print("Initializing RAG components for web content...")
        
        # Text splitter for chunking into structured units
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Transformer-based embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        
        # LLM for generating context-aware answers
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY", "AIzaSyDvhlqz_tSdNpkG6OZyryXyp5qUYjwDGcc"),
            temperature=0.0  # Most deterministic
        )
        
        # Minimal prompt - force simple answers
        self.prompt_template = PromptTemplate(
            template="""Context: {context}

Question: {question}

Provide a clear, well-structured answer:
- Start with a brief overview (2-3 sentences)
- Use bullet points for lists or key facts
- Keep paragraphs short (2-3 sentences maximum)
- Use section breaks for different topics
- Be concise but complete

Answer:""",
            input_variables=["context", "question"]
        )
        
        # Cache for processed content
        self.processed_content = {}
        
        print("RAG Web Content Service initialized")
    
    def clean_text_encoding(self, text: str) -> str:
        """Simple text cleaning"""
        if not text:
            return ""
        
        # Basic cleanup only
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _strip_formatting(self, text: str) -> str:
        """Aggressively remove ALL formatting from AI response"""
        if not text:
            return ""
        
        # Remove ALL markdown formatting
        text = re.sub(r'#+\s*', '', text)  # Remove headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic
        text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
        
        # Remove ALL emojis and special symbols
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII
        text = re.sub(r'[📋🔍✨🎯⭐★☆💫⚡🔥💡🚀📊📝📌📍🎪🎭🎨🎬🎥🎞️🧩🌐]', '', text)
        
        # Remove bullet points and replace with simple dashes
        text = re.sub(r'^[•·●○◦▪▫]', '-', text, flags=re.MULTILINE)
        
        # Clean up excessive spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """Extract and clean content from URL for basic content extraction"""
        try:
            session = await self.get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "error": f"Failed to fetch URL. Status: {response.status}",
                        "status_code": response.status
                    }
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else "No Title"
                
                # Extract main content
                main_content = await self._extract_main_content(soup, url)
                
                # Check if content was extracted
                if not main_content or len(main_content.strip()) < 100:
                    return {
                        "error": f"Insufficient content extracted from URL (only {len(main_content)} chars). The page may require JavaScript or have anti-scraping protection.",
                        "url": url
                    }
                
                return {
                    "title": title_text,
                    "content": main_content,
                    "url": url,
                    "word_count": len(main_content.split()),
                    "char_count": len(main_content)
                }
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in extract_content_from_url: {error_details}")
            return {
                "error": f"Error extracting content: {str(e)}",
                "url": url,
                "details": error_details
            }
    
    async def process_web_content_with_rag(self, url: str) -> Dict[str, Any]:
        """
        Step 1-4 of RAG approach:
        1. Extract and clean web content
        2. Divide into structured chunks (paragraphs, sections)
        3. Create embeddings using transformer model
        4. Store in vector database (Chroma) with metadata
        """
        try:
            print(f"Extracting content from: {url}")
            start_time = time.time()
            
            # Check if already processed
            url_hash = hash(url)
            if url_hash in self.processed_content:
                print(f"Using cached content (took {time.time() - start_time:.2f}s)")
                return self.processed_content[url_hash]
            
            # Step 1: Extract and clean content
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: Unable to access webpage")
                
                html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Extract title and content
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "No title"
            
            # Extract main content with Wikipedia-specific handling
            content = await self._extract_main_content(soup, url)
            
            if len(content) < 100:
                raise Exception("Insufficient content extracted from webpage")
            
            extraction_time = time.time() - start_time
            print(f"Extracted {len(content)} characters of content (took {extraction_time:.2f}s)")
            
            # Step 2: Create document and divide into structured chunks
            chunking_start = time.time()
            document = Document(
                page_content=content,
                metadata={
                    "url": url,
                    "title": title,
                    "domain": urlparse(url).netloc,
                    "content_length": len(content)
                }
            )
            
            # Divide into structured chunks
            chunks = self.text_splitter.split_documents([document])
            chunking_time = time.time() - chunking_start
            print(f"Divided content into {len(chunks)} structured chunks (took {chunking_time:.2f}s)")
            
            # Step 3-4: Create embeddings and store in vector database
            temp_dir = tempfile.mkdtemp(prefix=f"web_content_{url_hash}_")
            
            embedding_start = time.time()
            print(f"Creating vector embeddings using transformer model...")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
            embedding_time = time.time() - embedding_start
            print(f"Vector embeddings created (took {embedding_time:.2f}s)")
            
            # Create retrieval QA chain with more chunks for comprehensive answers
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 8}  # Increased from 3 to 8 for more comprehensive answers
                ),
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            
            # Cache the processed content
            self.processed_content[url_hash] = {
                "url": url,
                "title": title,
                "chunks_count": len(chunks),
                "qa_chain": qa_chain,
                "vectorstore": vectorstore,
                "temp_dir": temp_dir,
                "metadata": {
                    "domain": urlparse(url).netloc,
                    "content_length": len(content),
                    "processed_at": time.time()
                }
            }
            
            total_time = time.time() - start_time
            print(f"Content processed and stored in vector database (total: {total_time:.2f}s)")
            
            return self.processed_content[url_hash]
            
        except Exception as e:
            print(f"Error processing web content: {e}")
            raise Exception(f"Failed to process web content: {str(e)}")
    
    async def ask_question_with_rag(self, url: str, question: str) -> Dict[str, Any]:
        """
        Step 5-6 of RAG approach:
        5. Embed query and compute cosine similarity with stored embeddings
        6. Retrieve top-matching chunks and pass to LLM for context-aware answer
        """
        try:
            print(f"Processing question: {question}")
            
            # Process content if not already done
            content_data = await self.process_web_content_with_rag(url)
            
            # Step 5-6: Query embedding, similarity search, and LLM generation
            print(f"Embedding query and computing cosine similarity...")
            print(f"Retrieving top-matching chunks from {content_data['chunks_count']} total chunks...")
            
            qa_chain = content_data["qa_chain"]
            result = qa_chain.invoke({"query": question})
            
            answer = result.get("result", "Unable to generate answer")
            source_docs = result.get("source_documents", [])
            
            # AGGRESSIVELY remove all formatting from answer
            answer = self._strip_formatting(answer)
            
            print(f"Generated context-aware answer using {len(source_docs)} retrieved chunks")
            
            return {
                "success": True,
                "answer": answer,
                "url": url,
                "title": content_data["title"],
                "question": question,
                "confidence": 0.8,  # Simple fixed confidence
                "source_type": "web_rag",
                "word_count": len(answer.split()),
                "chunks_used": len(source_docs),
                "total_chunks": content_data["chunks_count"],
                "metadata": content_data["metadata"]
            }
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def summarize_with_rag(self, url: str) -> str:
        """Generate simple summary using RAG approach"""
        result = await self.ask_question_with_rag(url, "Provide a simple summary of this content.")
        
        if result.get("success"):
            return result["answer"]
        else:
            return f"Failed to generate summary: {result.get('error', 'Unknown error')}"
    
    async def _extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract main content with site-specific optimizations"""
        content = ""
        
        # Simple Wikipedia extraction
        if 'wikipedia.org' in url:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                if len(text) > 50:
                    content += text + "\n\n"
            if len(content) > 500:
                return content
        
        # Simple content extraction with more selectors
        selectors = ['main', 'article', '.content', '#content', '.post-content', '.entry-content', 
                     '.article-content', '.page-content', '[role="main"]']
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    content += text + "\n\n"
            if len(content) > 500:
                break
        
        # Simple fallback
        if len(content) < 500:
            for tag in ['p', 'div']:
                elements = soup.find_all(tag)
                for elem in elements:
                    text = elem.get_text(separator=' ', strip=True)
                    if len(text) > 20:
                        content += text + "\n"
        
        # Basic cleanup only
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'\[\d+\]', '', content)  # Remove citation numbers
        content = self.clean_text_encoding(content)
        
        return content
    
    async def close(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global instance
_rag_web_service = None

def get_rag_web_service():
    """Get or create RAG web service instance"""
    global _rag_web_service
    if _rag_web_service is None:
        _rag_web_service = RAGWebContentService()
    return _rag_web_service