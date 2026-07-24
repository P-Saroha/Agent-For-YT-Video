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
        print("Initializing Web Content Analysis Service...")

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

        print("Web Service ready!")

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
        Fetch and scrape a regular webpage with multiple fallback strategies.
        
        Tries:
        1. Direct HTTP GET
        2. Different User-Agents if blocked
        3. Selenium/JavaScript rendering (if available)
        4. Alternative parsing methods
        
        Returns: (title, content)
        """
        session = await self.get_session()
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.3)
        
        # Try with multiple user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
        ]
        
        html_content = None
        for user_agent in user_agents:
            try:
                headers = {'User-Agent': user_agent}
                async with session.get(
                    url, 
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers=headers,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        print(f"      Successfully fetched with User-Agent: {user_agent[:40]}...")
                        break
                    elif response.status == 403:
                        print(f"      Blocked (403). Trying different User-Agent...")
                        continue
                    elif response.status == 429:
                        print(f"      Rate limited (429). Waiting and retrying...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f"      HTTP {response.status}")
                        
            except Exception as e:
                print(f"      Failed with User-Agent {user_agent[:40]}: {str(e)[:50]}")
                continue
        
        if not html_content:
            raise Exception(f"Could not fetch webpage. Website may be blocking scrapers or temporarily unavailable.")

        # Parse HTML
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            raise Exception(f"Failed to parse webpage HTML: {str(e)}")

        # Remove unwanted elements (scripts, ads, navigation, etc.)
        for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']:
            for element in soup.find_all(tag):
                try:
                    element.decompose()
                except:
                    pass

        # Extract title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Webpage"

        # Extract main content
        content = self._extract_main_text(soup, url)
        
        if not content or len(content) < 50:
            print(f"      Warning: Very little content extracted. Site may require JavaScript.")
            raise Exception(f"Not enough content extracted. Website may require JavaScript rendering.")
        
        return title, content

    def _extract_main_text(self, soup, url: str) -> str:
        """Extract the main readable text from a webpage with multiple strategies."""
        content_parts = []

        # Strategy 1: For Wikipedia, use the main content div
        if 'wikipedia.org' in url.lower():
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                for p in content_div.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_parts.append(text)
        
        # Strategy 2: Look for common content containers
        if not content_parts:
            for tag in ['article', 'main', 'section', 'div[class*="content"]']:
                for element in soup.find_all(tag if tag.startswith('div') else tag):
                    for p in element.find_all(['p', 'h2', 'h3', 'h4', 'li']):
                        text = p.get_text().strip()
                        if text and len(text) > 20:
                            content_parts.append(text)
                    if content_parts:
                        break
                if content_parts:
                    break
        
        # Strategy 3: Get all paragraphs if nothing found
        if not content_parts:
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text and len(text) > 20 and not any(skip in text.lower() for skip in ['cookie', 'advertisement', 'subscribe']):
                    content_parts.append(text)
        
        # Strategy 4: If still nothing, get text from body
        if not content_parts:
            body = soup.find('body')
            if body:
                text = body.get_text().strip()
                # Remove common noise
                text = re.sub(r'(?i)(cookie|subscribe|advertisement|sign up|log in).{0,100}', '', text)
                content_parts = [text[:5000]]  # Take first 5000 chars

        # Join all content
        content = "\n\n".join(content_parts)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()

    async def process_webpage(self, url: str) -> Dict[str, Any]:
        """
        Process a webpage with comprehensive error handling and fallbacks.
        
        Steps:
        1. Validate URL
        2. Fetch webpage content (with retries)
        3. Extract main text
        4. Split into chunks
        5. Convert to vectors
        6. Store in database
        """
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            url_hash = hash(url)
            
            # Check if already processed
            if url_hash in self.processed_content:
                print(f"URL already processed (using cached data)")
                return self.processed_content[url_hash]

            print(f"Processing: {url}")

            # Step 1: Fetch content with fallback strategies
            print(f"   1. Fetching webpage...")
            title = None
            content = None
            
            try:
                # Try regular scraping first
                if 'wikipedia.org' in url.lower():
                    title, content = await self._fetch_wikipedia_content(url)
                else:
                    title, content = await self._scrape_webpage_content(url)
                    
            except Exception as scrape_error:
                print(f"      Scraping failed: {str(scrape_error)[:60]}")
                print(f"   1b. Trying fallback extraction method...")
                
                try:
                    # Fallback: Use simple extraction
                    session = await self.get_session()
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=20), ssl=False) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            title = soup.title.string if soup.title else url
                            content = soup.get_text()[:10000]  # First 10k chars
                            print(f"      Fallback successful: Extracted {len(content)} chars")
                        else:
                            raise Exception(f"HTTP {resp.status}")
                except Exception as fallback_error:
                    print(f"      Fallback also failed: {str(fallback_error)}")
                    raise Exception(f"Could not access webpage: {url}. Website may be down, blocking scrapers, or require authentication.")
            
            if not content or len(content) < 100:
                raise Exception(f"Not enough content extracted ({len(content) if content else 0} chars). Website may require JavaScript or be too minimal.")

            print(f"      Extracted {len(content)} characters")

            # Step 2: Create document
            doc = Document(
                page_content=content,
                metadata={
                    "url": url,
                    "title": title or "Webpage",
                    "domain": urlparse(url).netloc,
                    "content_length": len(content)
                }
            )

            # Step 3: Split into chunks
            print(f"   2. Splitting into chunks...")
            chunks = self.text_splitter.split_documents([doc])
            print(f"      Created {len(chunks)} chunks")

            # Step 4: Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"web_{url_hash}_")

            # Step 5: Convert to vectors
            print(f"   3. Converting text to vectors...")
            try:
                vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory=temp_dir
                )
            except Exception as vector_error:
                print(f"      Vector store creation failed: {str(vector_error)}")
                raise Exception(f"Failed to create vector database: {str(vector_error)}")

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
                "title": title or "Webpage",
                "chunks": len(chunks),
                "content_length": len(content),
                "status": "processed"
            }
            self.vector_stores[url_hash] = rag_chain
            self.temp_directories[url_hash] = temp_dir

            print(f"   URL processed successfully!")

            return self.processed_content[url_hash]

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing webpage: {error_msg}")
            
            # Provide helpful error messages
            if "403" in error_msg or "blocking" in error_msg.lower():
                raise Exception(f"Website is blocking automated access. Try a different URL or manually copy-paste content.")
            elif "timeout" in error_msg.lower():
                raise Exception(f"Website took too long to respond. It may be slow or unreachable. Try again later.")
            elif "connection" in error_msg.lower():
                raise Exception(f"Could not connect to website. Check internet connection and URL.")
            elif "javascript" in error_msg.lower():
                raise Exception(f"Website requires JavaScript rendering which isn't supported. Try a different site.")
            else:
                raise Exception(f"Failed to process webpage: {error_msg}")
                "content_length": len(content),
                "status": "processed"
            }
            self.vector_stores[url_hash] = rag_chain
            self.temp_directories[url_hash] = temp_dir

            print(f"URL processed successfully!")

            return self.processed_content[url_hash]

        except Exception as e:
            print(f"Error processing webpage: {str(e)}")
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

            print(f"Question: {question[:50]}...")

            # Get the RAG chain and ask
            rag_chain = self.vector_stores[url_hash]
            result = rag_chain.invoke({"input": question})

            answer = result["answer"]
            source_docs = result.get("context", [])

            print(f"Generated answer using {len(source_docs)} relevant sections")

            return {
                "question": question,
                "answer": answer,
                "sources_used": len(source_docs),
                "method": "RAG"
            }

        except Exception as e:
            print(f"Error answering question: {str(e)}")
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

## Overview
[2-3 sentences about what this page covers]

## Main Topics
- Topic 1: [Explanation]
- Topic 2: [Explanation]
- Topic 3: [Explanation]

## Key Points
1. [Important point 1]
2. [Important point 2]
3. [Important point 3]

## Summary
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
            print(f"Error summarizing webpage: {str(e)}")
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

            print(f"Cleaned up URL")
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

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
