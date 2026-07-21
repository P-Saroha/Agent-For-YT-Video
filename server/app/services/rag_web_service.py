"""
Web Content Analysis Service using LangChain and Google Gemini.

How it works:
1. Fetch content from a website
2. Extract main text (remove ads, navigation, etc.)
3. Split into chunks
4. Convert to vectors
5. Answer questions about the content using RAG

Supports:
- Regular websites (HTML scraping)
- Wikipedia (uses official API for reliability)
"""

import asyncio
import aiohttp
import re
import tempfile
import os
from urllib.parse import urlparse
from typing import Dict, Any
from bs4 import BeautifulSoup

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


class WebRAGService:
    """
    Service to analyze web content using RAG.
    
    RAG = Get relevant information from website, then use AI to answer questions.
    """

    def __init__(self):
        """Initialize components for web content analysis."""
        print("🌐 Initializing Web Content Analysis Service...")

        self.session = None
        
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
            ("system", """You are a helpful AI assistant analyzing web content.

Here is information from the website:
{context}

Rules:
- Answer the question based ONLY on the content above
- Be clear and concise
- Use markdown formatting (headers, bold, lists) to make answers readable
- If the answer is not in the content, say "This information is not on the page"
- Sound natural and friendly, like a real person explaining something"""),
            ("human", "{input}")
        ])

        # ==================== Component 5: Memory/Cache ====================
        self.processed_content = {}    # Maps url_hash -> metadata
        self.vector_stores = {}         # Maps url_hash -> vector database
        self.temp_directories = {}      # Maps url_hash -> temporary folder path

        print("✅ Web Service ready!")

    async def get_session(self):
        """Get or create an HTTP session for fetching webpages."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            # Browser-like headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session

    async def _fetch_wikipedia_content(self, url: str) -> tuple:
        """
        Fetch Wikipedia content using the official API (more reliable).
        
        Returns: (title, content)
        """
        # Extract article title from URL
        # https://en.wikipedia.org/wiki/Article_Name -> Article_Name
        parts = url.split('/wiki/')
        if len(parts) < 2:
            raise Exception("Invalid Wikipedia URL")
        
        article_title = parts[1].split('#')[0].replace('_', ' ')
        
        # Detect language from URL (en.wikipedia.org -> en)
        lang = 'en'
        lang_match = re.search(r'//([a-z]{2})\.wikipedia\.org', url)
        if lang_match:
            lang = lang_match.group(1)
        
        # Call Wikipedia API
        api_url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'titles': article_title,
            'prop': 'extracts',
            'explaintext': '1',
            'exsectionformat': 'plain'
        }
        
        session = await self.get_session()
        async with session.get(api_url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Wikipedia API error: {response.status}")
            
            data = await response.json()
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                raise Exception("No content from Wikipedia")
            
            page = list(pages.values())[0]
            if 'missing' in page:
                raise Exception(f"Article not found: {article_title}")
            
            title = page.get('title', article_title)
            content = page.get('extract', '')
            
            return title, content

    async def _scrape_webpage_content(self, url: str) -> tuple:
        """
        Fetch and scrape a regular webpage.
        
        Returns: (title, content)
        """
        session = await self.get_session()
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.3)
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: Cannot fetch webpage")

            html_content = await response.text()

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements (scripts, ads, navigation, etc.)
        for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']:
            for element in soup.find_all(tag):
                element.decompose()

        # Extract title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Webpage"

        # Extract main content
        content = self._extract_main_text(soup, url)
        
        return title, content

    def _extract_main_text(self, soup, url: str) -> str:
        """Extract the main readable text from a webpage."""
        content_parts = []

        # For Wikipedia, use the main content div
        if 'wikipedia.org' in url.lower():
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                for p in content_div.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)
        else:
            # For regular websites, look for common content containers
            for tag in ['article', 'main', 'section']:
                for element in soup.find_all(tag):
                    for p in element.find_all(['p', 'h2', 'h3', 'li']):
                        text = p.get_text().strip()
                        if text and len(text) > 20:
                            content_parts.append(text)

            # Fallback: get all paragraphs if nothing found
            if not content_parts:
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)

        # Join all content
        content = "\n\n".join(content_parts)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        
        return content

    async def process_webpage(self, url: str) -> Dict[str, Any]:
        """
        Process a webpage so questions can be asked about it.
        
        Steps:
        1. Fetch webpage content
        2. Extract main text
        3. Split into chunks
        4. Convert to vectors
        5. Store in database
        """
        try:
            url_hash = hash(url)
            
            # Check if already processed
            if url_hash in self.processed_content:
                print(f"📦 URL already processed (using cached data)")
                return self.processed_content[url_hash]

            print(f"🌐 Processing: {url}")

            # Step 1: Fetch content
            print(f"   1️⃣ Fetching webpage...")
            if 'wikipedia.org' in url.lower():
                title, content = await self._fetch_wikipedia_content(url)
            else:
                title, content = await self._scrape_webpage_content(url)
            
            if len(content) < 100:
                raise Exception("Not enough content extracted from webpage")

            # Step 2: Create document
            doc = Document(
                page_content=content,
                metadata={
                    "url": url,
                    "title": title,
                    "domain": urlparse(url).netloc
                }
            )

            # Step 3: Split into chunks
            print(f"   2️⃣ Splitting into chunks...")
            chunks = self.text_splitter.split_documents([doc])
            print(f"      Created {len(chunks)} chunks")

            # Step 4: Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"web_{url_hash}_")

            # Step 5: Convert to vectors
            print(f"   3️⃣ Converting text to vectors...")
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )

            # Step 6: Create retriever and RAG chain
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 8}  # Return top 8 chunks
            )

            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.qa_prompt
            )
            rag_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=document_chain
            )

            # Store in memory
            self.processed_content[url_hash] = {
                "title": title,
                "chunks": len(chunks),
                "content_length": len(content),
                "status": "processed"
            }
            self.vector_stores[url_hash] = rag_chain
            self.temp_directories[url_hash] = temp_dir

            print(f"✅ URL processed successfully!")

            return self.processed_content[url_hash]

        except Exception as e:
            print(f"❌ Error processing webpage: {str(e)}")
            raise

    async def ask_question(self, url: str, question: str) -> Dict[str, Any]:
        """
        Ask a question about a processed webpage.
        
        Args:
            url: The webpage URL
            question: The question to ask
            
        Returns:
            Dictionary with the answer and metadata
        """
        try:
            url_hash = hash(url)

            # Make sure webpage is processed
            if url_hash not in self.vector_stores:
                await self.process_webpage(url)

            print(f"❓ Question: {question[:50]}...")

            # Get the RAG chain and ask
            rag_chain = self.vector_stores[url_hash]
            result = rag_chain.invoke({"input": question})

            answer = result["answer"]
            source_docs = result.get("context", [])

            print(f"✅ Generated answer using {len(source_docs)} relevant sections")

            return {
                "question": question,
                "answer": answer,
                "sources_used": len(source_docs),
                "method": "RAG"
            }

        except Exception as e:
            print(f"❌ Error answering question: {str(e)}")
            raise

    async def summarize_webpage(self, url: str) -> Dict[str, Any]:
        """
        Generate a summary of the entire webpage.
        
        Args:
            url: The webpage URL
            
        Returns:
            Dictionary with the summary
        """
        try:
            url_hash = hash(url)
            
            # Make sure webpage is processed
            if url_hash not in self.vector_stores:
                await self.process_webpage(url)

            # Ask for summary
            summary_question = """Create a clear, well-organized summary of this webpage.

Format your response as:

## 📝 Overview
[2-3 sentences about what this page covers]

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

            result = await self.ask_question(url, summary_question)
            
            # Get title from cache
            metadata = self.processed_content[url_hash]
            
            return {
                "url": url,
                "title": metadata["title"],
                "summary": result["answer"]
            }

        except Exception as e:
            print(f"❌ Error summarizing webpage: {str(e)}")
            raise

    def cleanup_url(self, url: str):
        """Clean up resources for a specific URL."""
        try:
            url_hash = hash(url)
            if url_hash in self.temp_directories:
                temp_dir = self.temp_directories[url_hash]
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)

            # Remove from memory
            if url_hash in self.processed_content:
                del self.processed_content[url_hash]
            if url_hash in self.vector_stores:
                del self.vector_stores[url_hash]
            if url_hash in self.temp_directories:
                del self.temp_directories[url_hash]

            print(f"🧹 Cleaned up URL")
        except Exception as e:
            print(f"⚠️ Error cleaning up: {str(e)}")

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Clean up all resources when the service is destroyed."""
        try:
            if hasattr(self, 'session') and self.session and not self.session.closed:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.session.close())
                except:
                    pass

            if hasattr(self, 'temp_directories'):
                for temp_dir in self.temp_directories.values():
                    if os.path.exists(temp_dir):
                        import shutil
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
        except:
            pass


def get_web_service() -> WebRAGService:
    """
    Get an instance of the Web RAG service.
    
    Usage:
        service = get_web_service()
        await service.process_webpage("https://example.com")
        result = await service.ask_question(url, "What is this about?")
    """
    return WebRAGService()
