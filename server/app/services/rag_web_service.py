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
        print("🔧 Initializing RAG components for web content...")
        
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
            temperature=0.7
        )
        
        # Improved prompt template for RAG - cleaner formatting
        self.prompt_template = PromptTemplate(
            template="""Based on the following context, provide a clear and well-structured answer to the question.

Context: {context}

Question: {question}

Instructions:
- Answer directly and concisely
- Use clear headers (##) for main sections
- Use simple dashes (-) for bullet points, NOT asterisks (*)
- Keep paragraphs short and readable
- Focus on the most relevant information
- Structure your response clearly with proper spacing
- Do NOT use asterisks (*) for formatting - use markdown headers (##) and dashes (-) only

Answer:""",
            input_variables=["context", "question"]
        )
        
        # Cache for processed content
        self.processed_content = {}
        
        print("✅ RAG Web Content Service initialized")
    
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
                
                return {
                    "title": title_text,
                    "content": main_content,
                    "url": url,
                    "word_count": len(main_content.split()),
                    "char_count": len(main_content)
                }
                
        except Exception as e:
            return {
                "error": f"Error extracting content: {str(e)}",
                "url": url
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
            print(f"🌐 Extracting content from: {url}")
            start_time = time.time()
            
            # Check if already processed
            url_hash = hash(url)
            if url_hash in self.processed_content:
                print(f"♻️ Using cached content (took {time.time() - start_time:.2f}s)")
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
            print(f"📄 Extracted {len(content)} characters of content (took {extraction_time:.2f}s)")
            
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
            print(f"📊 Divided content into {len(chunks)} structured chunks (took {chunking_time:.2f}s)")
            
            # Step 3-4: Create embeddings and store in vector database
            temp_dir = tempfile.mkdtemp(prefix=f"web_content_{url_hash}_")
            
            embedding_start = time.time()
            print(f"🔢 Creating vector embeddings using transformer model...")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
            embedding_time = time.time() - embedding_start
            print(f"⚡ Vector embeddings created (took {embedding_time:.2f}s)")
            
            # Create retrieval QA chain (optimized for speed)
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}  # Retrieve top 3 similar chunks (faster)
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
            print(f"✅ Content processed and stored in vector database (total: {total_time:.2f}s)")
            
            return self.processed_content[url_hash]
            
        except Exception as e:
            print(f"❌ Error processing web content: {e}")
            raise Exception(f"Failed to process web content: {str(e)}")
    
    async def ask_question_with_rag(self, url: str, question: str) -> Dict[str, Any]:
        """
        Step 5-6 of RAG approach:
        5. Embed query and compute cosine similarity with stored embeddings
        6. Retrieve top-matching chunks and pass to LLM for context-aware answer
        """
        try:
            print(f"❓ Processing question: {question}")
            
            # Process content if not already done
            content_data = await self.process_web_content_with_rag(url)
            
            # Step 5-6: Query embedding, similarity search, and LLM generation
            print(f"🔍 Embedding query and computing cosine similarity...")
            print(f"📚 Retrieving top-matching chunks from {content_data['chunks_count']} total chunks...")
            
            qa_chain = content_data["qa_chain"]
            result = qa_chain.invoke({"query": question})
            
            answer = result.get("result", "Unable to generate answer")
            source_docs = result.get("source_documents", [])
            
            print(f"✅ Generated context-aware answer using {len(source_docs)} retrieved chunks")
            
            return {
                "success": True,
                "answer": answer,
                "url": url,
                "title": content_data["title"],
                "question": question,
                "confidence": min(0.9, 0.5 + (len(source_docs) * 0.1)),  # Simple confidence based on chunks used
                "source_type": "web_rag",
                "word_count": len(answer.split()),
                "chunks_used": len(source_docs),
                "total_chunks": content_data["chunks_count"],
                "metadata": content_data["metadata"]
            }
            
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def summarize_with_rag(self, url: str) -> str:
        """Generate summary using RAG approach"""
        result = await self.ask_question_with_rag(
            url, 
            "Provide a comprehensive summary of this web content. Include main topics, key points, and important details in a well-structured format."
        )
        
        if result.get("success"):
            return result["answer"]
        else:
            return f"Failed to generate summary: {result.get('error', 'Unknown error')}"
    
    async def _extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract main content with site-specific optimizations"""
        content = ""
        
        # Wikipedia-specific extraction
        if 'wikipedia.org' in url:
            wikipedia_content = soup.select_one('#mw-content-text .mw-parser-output')
            if wikipedia_content:
                # Remove metadata elements
                for unwanted in wikipedia_content.select('.infobox, .navbox, .metadata, .hatnote, .dablink, .ambox'):
                    unwanted.decompose()
                
                paragraphs = wikipedia_content.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 50 and not text.startswith('Coordinates:'):
                        content += text + "\n\n"
                
                if len(content) > 500:
                    return content
        
        # COMPREHENSIVE content extraction with expanded selectors
        selectors = [
            'main', 'article', '.content', '#content', '.post-content', '.entry-content',
            '.blog-post', '.post', '.single-post', '.page-content', '.article-content',
            '.elementor-widget-container', '.elementor-text-editor', '.wp-content',
            '.blog-content', '.article-body', '.post-body'
        ]
        
        print(f"🔍 Trying {len(selectors)} content selectors...")
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(separator='\n', strip=True)
                if len(text) > 100:  # Lower threshold for more content
                    content += text + "\n\n"
                    print(f"✅ Found content with selector '{selector}': {len(text)} chars")
            if len(content) > 1000:  # Continue until we get substantial content
                break
        
        # Enhanced fallback - get ALL meaningful elements
        if len(content) < 1000:
            print("🔄 Using enhanced fallback extraction...")
            for tag in ['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span']:
                elements = soup.find_all(tag)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if len(text) > 20 and text not in content:  # Avoid duplicates
                        content += text + "\n"
        
        # Clean content
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\[\d+\]', '', content)  # Remove citation numbers
        
        return content.strip()
    
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