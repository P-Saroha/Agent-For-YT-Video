"""
Optimized RAG-based Web Content Analysis Service using Modern LangChain LCEL
Following best practices: LCEL, create_retrieval_chain, ChatPromptTemplate, batch processing
"""
import asyncio
import aiohttp
import re
import time
import tempfile
import os
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

# Modern LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


class OptimizedRAGWebContentService:
    """Web content analysis using Modern LangChain LCEL"""

    def __init__(self):
        self.session = None

        print(" Initializing Optimized RAG Web Content Service with LCEL...")

        # Configure text splitter with optimal settings (matching PDF service)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ": ", " ", ""]
        )

        # Use multilingual embeddings for better content understanding
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={
                'device': 'cpu',
            },
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32
            }
        )

        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0
        )

        #  Modern: ChatPromptTemplate with enhanced formatting
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant analyzing web content. Answer questions naturally and conversationally, like ChatGPT or Claude.

Context from web content:
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

        #  Modern: Separate caches for better organization
        self.content_cache = {}  # Processed content metadata
        self.vectorstore_cache = {}  # Vector stores

        print(" Optimized RAG Web Content Service initialized with LCEL")

    def _strip_formatting(self, text: str) -> str:
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

    def clean_text_encoding(self, text: str) -> str:
        """Simple text cleaning"""
        if not text:
            return ""

        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        return text

    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session

    async def _extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract main content from parsed HTML"""
        content_parts = []

        # Wikipedia-specific extraction
        if 'wikipedia.org' in url.lower():
            # Get main content div
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                # Get all paragraphs
                paragraphs = content_div.find_all('p', recursive=True)
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)
        else:
            # Generic extraction
            for tag in ['article', 'main', 'div[role="main"]', 'section']:
                elements = soup.select(tag)
                for element in elements:
                    paragraphs = element.find_all(['p', 'h1', 'h2', 'h3', 'li'])
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if text and len(text) > 20:
                            content_parts.append(text)

            # Fallback: get all paragraphs
            if not content_parts:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)

        # Join content
        content = "\n\n".join(content_parts)

        # Clean up
        content = self.clean_text_encoding(content)

        return content

    async def process_web_content_with_rag(self, url: str) -> Dict[str, Any]:
        """
        Modern RAG approach with LCEL:
        1. Extract and clean web content
        2. Divide into structured chunks
        3. Create embeddings with batch processing
        4. Store in vector database with metadata
        """
        try:
            print(f" Extracting content from: {url}")
            start_time = time.time()

            #  Check cache first
            url_hash = hash(url)
            if url_hash in self.content_cache:
                print(f" Using cached content (took {time.time() - start_time:.2f}s)")
                return self.content_cache[url_hash]

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

            content = await self._extract_main_content(soup, url)

            if len(content) < 100:
                raise Exception("Insufficient content extracted from webpage")

            extraction_time = time.time() - start_time
            print(f" Extracted {len(content)} characters (took {extraction_time:.2f}s)")

            # Step 2: Create document and divide into chunks
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

            chunks = self.text_splitter.split_documents([document])
            chunking_time = time.time() - chunking_start
            print(f" Divided into {len(chunks)} chunks (took {chunking_time:.2f}s)")

            # Step 3-4: Create embeddings and store in vector database
            temp_dir = tempfile.mkdtemp(prefix=f"web_content_{url_hash}_")

            embedding_start = time.time()
            print(f" Creating vector embeddings (batch_size=32)...")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
            embedding_time = time.time() - embedding_start
            print(f" Vector embeddings created (took {embedding_time:.2f}s)")

            #  Modern: Use create_retrieval_chain with optimized retrieval
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 8  # Return top 8 most relevant documents
                }
            )

            #  Modern LCEL: Create document chain and retrieval chain
            doc_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.qa_prompt
            )

            rag_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=doc_chain
            )

            total_time = time.time() - start_time
            print(f" Content processed (total: {total_time:.2f}s)")

            # Store in caches
            result = {
                "url": url,
                "title": title,
                "chunks_count": len(chunks),
                "content_length": len(content),
                "processing_time": total_time,
                "status": "processed"
            }

            self.content_cache[url_hash] = result
            self.vectorstore_cache[url_hash] = {
                "rag_chain": rag_chain,
                "vectorstore": vectorstore,
                "temp_dir": temp_dir,
                "title": title
            }

            return result

        except Exception as e:
            print(f" Error processing web content: {e}")
            raise e

    async def ask_question_about_web_content(self, url: str, question: str) -> Dict[str, Any]:
        """
        Step 5-6 of Modern RAG approach with LCEL:
        5. Retrieve relevant chunks using similarity search
        6. Generate context-aware answer using LLM
        """
        try:
            url_hash = hash(url)

            # Check if content is processed
            if url_hash not in self.vectorstore_cache:
                # Process first if not already done
                await self.process_web_content_with_rag(url)

            chain_data = self.vectorstore_cache[url_hash]
            rag_chain = chain_data["rag_chain"]

            print(f" Processing question: {question}")

            query_start = time.time()

            #  Modern LCEL: Use invoke with "input" key (not "query")
            result = rag_chain.invoke({"input": question})

            query_time = time.time() - query_start

            #  Modern LCEL: Answer is in "answer" key (not "result")
            answer = result["answer"]
            source_docs = result.get("context", [])  # Retrieved documents

            # Keep the answer as-is from AI (don't strip formatting like PDF service does)
            # The AI is already instructed to format properly via the prompt

            # Calculate confidence
            confidence = min(len(source_docs) * 0.12, 1.0) if source_docs else 0.3

            # Get title from cache
            title = chain_data.get("title", "Unknown")
            
            # Calculate word count
            word_count = len(answer.split())

            print(f" Generated answer with {len(source_docs)} sources (took {query_time:.2f}s)")

            return {
                "success": True,
                "url": url,
                "title": title,
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "source_type": "rag_vector_search",
                "word_count": word_count,
                "sources": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    } for doc in source_docs[:5]  # Limit to top 5 sources
                ],
                "processing_time": query_time,
                "method": "rag_lcel"
            }

        except Exception as e:
            print(f" Error answering question: {e}")
            raise e

    async def summarize_web_content(self, url: str) -> Dict[str, Any]:
        """Generate comprehensive summary using Modern LCEL"""
        try:
            # Ensure content is processed
            url_hash = hash(url)
            if url_hash not in self.vectorstore_cache:
                await self.process_web_content_with_rag(url)

            chain_data = self.vectorstore_cache[url_hash]

            # Ask for summary using enhanced question format
            summary_question = """Provide a comprehensive, well-formatted summary of this web content.

Use this structure:

##  Overview
[2-3 sentence high-level summary of what this content is about]

##  Main Topics Covered
**Topic 1**: [Description with key details]
**Topic 2**: [Description with key details]
**Topic 3**: [Description with key details]

##  Key Points & Insights
1. **[Important Point 1]**: [Detailed explanation]
2. **[Important Point 2]**: [Detailed explanation]
3. **[Important Point 3]**: [Detailed explanation]

##  Important Details
• [Notable detail or fact 1]
• [Notable detail or fact 2]
• [Notable detail or fact 3]

##  Key Takeaways
> [Most important conclusion or lesson from this content]

Use clear formatting, bold for emphasis, and organize information logically."""

            result = await self.ask_question_about_web_content(url, summary_question)

            return {
                "url": url,
                "title": chain_data["title"],
                "summary": result["answer"],
                "confidence": result["confidence"],
                "method": "rag_lcel_summary"
            }

        except Exception as e:
            print(f" Error generating summary: {e}")
            raise e

    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """Extract and clean content from URL (basic extraction without RAG)"""
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

                if not main_content or len(main_content.strip()) < 100:
                    return {
                        "error": f"Insufficient content extracted from URL (only {len(main_content)} chars)",
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
            print(f" Error extracting content: {e}")
            return {
                "error": f"Error extracting content: {str(e)}",
                "url": url
            }

    def cleanup_url(self, url: str):
        """Clean up resources for a processed URL"""
        try:
            url_hash = hash(url)
            if url_hash in self.vectorstore_cache:
                chain_data = self.vectorstore_cache[url_hash]
                temp_dir = chain_data["temp_dir"]

                # Clean up temp directory
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)

                # Remove from caches
                del self.vectorstore_cache[url_hash]
                del self.content_cache[url_hash]

                print(f" Cleaned up resources for {url}")
        except Exception as e:
            print(f"  Error cleaning up {url}: {e}")

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup all resources on deletion"""
        try:
            # Close session
            if hasattr(self, 'session') and self.session and not self.session.closed:
                try:
                    asyncio.get_event_loop().run_until_complete(self.session.close())
                except:
                    pass

            # Clean up all cached content
            if hasattr(self, 'vectorstore_cache'):
                for url_hash in list(self.vectorstore_cache.keys()):
                    try:
                        chain_data = self.vectorstore_cache[url_hash]
                        temp_dir = chain_data["temp_dir"]
                        if os.path.exists(temp_dir):
                            import shutil
                            shutil.rmtree(temp_dir)
                    except:
                        pass
        except Exception:
            # Silently handle cleanup errors during destruction
            pass


# Factory function for easy import
def get_rag_web_service() -> OptimizedRAGWebContentService:
    """Get RAG web content service instance (optimized with LCEL)"""
    return OptimizedRAGWebContentService()

# Backward compatibility
RAGWebContentService = OptimizedRAGWebContentService

def get_optimized_rag_web_service() -> OptimizedRAGWebContentService:
    """Legacy name - use get_rag_web_service() instead"""
    return get_rag_web_service()
