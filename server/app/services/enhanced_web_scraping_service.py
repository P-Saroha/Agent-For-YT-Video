import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
from typing import Optional, Dict, Any, List
import os
import random
import json

class EnhancedWebScrapingService:
    def __init__(self):
        self.session = None
        self.ai_service = None
        print("Enhanced web scraping service initialized")
        
        # Rotating user agents for better anti-bot bypass
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
    
    async def get_session(self):
        """Get or create aiohttp session with enhanced headers"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=45, connect=15)
            
            # Randomize user agent
            user_agent = random.choice(self.user_agents)
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Create connector with SSL context and compression handling
            connector = aiohttp.TCPConnector(
                ssl=False,  # Disable SSL verification for problematic sites
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True
            )
            
            # Remove compression headers that might cause issues
            headers.pop('Accept-Encoding', None)  # Let aiohttp handle compression automatically
            
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                headers=headers,
                connector=connector
            )
        return self.session
    
    def get_ai_service(self):
        """Get AI service for content analysis"""
        if self.ai_service is None:
            try:
                from app.services.simple_ai_service import SimpleYouTubeAIService
                self.ai_service = SimpleYouTubeAIService()
                print("AI service loaded for web content analysis")
            except Exception as e:
                print(f"Error loading AI service: {e}")
                raise
        return self.ai_service
    
    async def extract_content_from_url(self, url: str, retry_count: int = 3) -> Dict[str, Any]:
        """Extract content from any website URL with enhanced retry logic"""
        last_error = None
        
        for attempt in range(retry_count):
            try:
                print(f"Extracting content from: {url} (attempt {attempt + 1})")
                
                # Validate URL
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL format")
                
                session = await self.get_session()
                
                # Add random delay for rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    print(f"Waiting {delay:.1f} seconds before retry...")
                    await asyncio.sleep(delay)
                
                async with session.get(url, allow_redirects=True) as response:
                    print(f"Response status: {response.status}")
                    
                    if response.status == 403:
                        # Try with different headers for 403 errors
                        headers = {
                            'Referer': 'https://www.google.com/',
                            'Origin': 'https://www.google.com'
                        }
                        async with session.get(url, headers=headers, allow_redirects=True) as retry_response:
                            if retry_response.status != 200:
                                raise Exception(f"HTTP {retry_response.status}: Access denied even with Google referer")
                            html_content = await retry_response.text()
                    elif response.status == 429:
                        # Rate limited - wait longer
                        wait_time = 5 + (attempt * 2)
                        print(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status != 200:
                        raise Exception(f"HTTP {response.status}: Failed to fetch URL")
                    else:
                        html_content = await response.text()
                
                # Parse HTML content
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract content using multiple strategies
                result = await self._extract_content_comprehensive(soup, url, html_content)
                
                if result["content"] and len(result["content"].strip()) >= 50:
                    print(f"Successfully extracted {len(result['content'])} characters from {url}")
                    return result
                else:
                    raise Exception("Insufficient content extracted")
                    
            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == retry_count - 1:
                    print(f"All {retry_count} attempts failed for {url}")
                    break
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # If all attempts failed, raise the last error
        raise Exception(f"Failed to extract content after {retry_count} attempts: {str(last_error)}")
    
    async def _extract_content_comprehensive(self, soup: BeautifulSoup, url: str, html_content: str) -> Dict[str, Any]:
        """Comprehensive content extraction using multiple strategies"""
        
        # Strategy 1: Try structured content extraction
        content = self._extract_main_content_enhanced(soup)
        
        # Strategy 2: If insufficient content, try JSON-LD extraction
        if len(content.strip()) < 100:
            json_content = self._extract_json_ld_content(soup)
            if json_content:
                content += " " + json_content
        
        # Strategy 3: If still insufficient, try aggressive text extraction
        if len(content.strip()) < 100:
            aggressive_content = self._extract_aggressive_text(soup)
            if aggressive_content:
                content = aggressive_content
        
        # Strategy 4: Last resort - extract all visible text
        if len(content.strip()) < 50:
            all_text = soup.get_text(separator=' ', strip=True)
            content = self._clean_content(all_text)
        
        # Extract other metadata
        title = self._extract_title_enhanced(soup, url)
        metadata = self._extract_metadata_enhanced(soup, url)
        
        # Clean and process content
        cleaned_content = self._clean_content(content)
        
        # Detect if content looks like it needs JavaScript
        js_indicators = ['Loading...', 'Please enable JavaScript', 'This site requires JavaScript', 'window.', 'document.']
        needs_js = any(indicator.lower() in cleaned_content.lower() for indicator in js_indicators)
        
        if needs_js and len(cleaned_content.strip()) < 200:
            print(f"⚠️  Site appears to require JavaScript: {url}")
            metadata["requires_javascript"] = True
        
        if not cleaned_content.strip() or len(cleaned_content.strip()) < 50:
            raise Exception("No readable content found on the webpage")
        
        return {
            "url": url,
            "title": title,
            "content": cleaned_content,
            "metadata": metadata,
            "word_count": len(cleaned_content.split()),
            "extracted_at": time.time(),
            "extraction_method": "enhanced_scraping"
        }
    
    def _extract_main_content_enhanced(self, soup: BeautifulSoup) -> str:
        """Enhanced main content extraction with better selectors"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                            'advertisement', 'iframe', 'noscript', 'form', 'button',
                            '.cookie', '.popup', '.modal', '.ad', '.advertisement',
                            '[class*="cookie"]', '[class*="popup"]', '[class*="ad"]']):
            element.decompose()
        
        # Enhanced main content selectors
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.story-body',
            '.article-content',
            '.post-body',
            '.content-body',
            '.page-content',
            '.single-content',
            '.entry-text',
            '.text-content',
            '[class*="content"][class*="main"]',
            '[id*="content"]',
            '[class*="article"]',
            '[id*="article"]',
            '.container .content',
            '.wrapper .content'
        ]
        
        content_text = ""
        
        # Try main content selectors
        for selector in main_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.get_text(separator=' ', strip=True)
                        if len(text) > 100:
                            content_text += text + " "
                    if len(content_text.strip()) > 300:
                        break
            except:
                continue
        
        # If still no good content, try paragraphs with context
        if len(content_text.strip()) < 300:
            content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            for element in content_elements:
                text = element.get_text(strip=True)
                if len(text) > 30 and not self._is_noise_text(text):
                    content_text += text + " "
        
        return content_text
    
    def _extract_json_ld_content(self, soup: BeautifulSoup) -> str:
        """Extract content from JSON-LD structured data"""
        content = ""
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}
                
                # Extract text from various JSON-LD properties
                text_fields = ['articleBody', 'text', 'description', 'content', 'about']
                for field in text_fields:
                    if field in data and isinstance(data[field], str):
                        content += data[field] + " "
            except:
                continue
        
        return content
    
    def _extract_aggressive_text(self, soup: BeautifulSoup) -> str:
        """Aggressive text extraction for difficult sites"""
        text_content = ""
        
        # Look for divs with substantial text
        divs = soup.find_all('div')
        for div in divs:
            text = div.get_text(separator=' ', strip=True)
            # Only include divs with substantial, non-repetitive content
            if len(text) > 100 and not self._is_noise_text(text):
                # Check if this div contains mostly unique content
                words = text.split()
                unique_words = set(words)
                if len(unique_words) > len(words) * 0.3:  # At least 30% unique words
                    text_content += text + " "
        
        return text_content
    
    def _extract_title_enhanced(self, soup: BeautifulSoup, url: str) -> str:
        """Enhanced title extraction"""
        title_sources = [
            soup.find('title'),
            soup.find('meta', attrs={'property': 'og:title'}),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('h1'),
            soup.find('meta', attrs={'name': 'title'}),
            soup.find('[class*="title"]'),
            soup.find('[id*="title"]')
        ]
        
        for source in title_sources:
            if source:
                title = source.get('content') if source.name == 'meta' else source.get_text()
                if title and title.strip() and len(title.strip()) > 3:
                    return title.strip()
        
        # Fallback to URL
        return urlparse(url).netloc
    
    def _extract_metadata_enhanced(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Enhanced metadata extraction"""
        metadata = {
            "domain": urlparse(url).netloc,
            "url": url
        }
        
        # Extract various meta tags
        meta_mappings = {
            'description': ['name="description"', 'property="og:description"', 'name="twitter:description"'],
            'author': ['name="author"', 'property="og:author"', 'name="twitter:creator"'],
            'keywords': ['name="keywords"'],
            'published_time': ['property="article:published_time"', 'name="pubdate"'],
            'site_name': ['property="og:site_name"'],
            'type': ['property="og:type"']
        }
        
        for key, selectors in meta_mappings.items():
            for selector in selectors:
                meta = soup.find('meta', attrs=dict([selector.split('=')]))
                if meta:
                    content = meta.get('content', '').strip()
                    if content:
                        metadata[key] = content
                        break
        
        return metadata
    
    def _is_noise_text(self, text: str) -> bool:
        """Check if text is likely noise/boilerplate"""
        text_lower = text.lower()
        noise_indicators = [
            'cookie', 'privacy policy', 'terms of service', 'subscribe',
            'newsletter', 'advertisement', 'click here', 'read more',
            'follow us', 'social media', 'share this', 'all rights reserved',
            'copyright', '© 2024', '© 2025', 'loading', 'please wait'
        ]
        
        # Check if text is mostly noise
        noise_count = sum(1 for indicator in noise_indicators if indicator in text_lower)
        words = text.split()
        
        # Consider it noise if:
        # 1. High ratio of noise indicators
        # 2. Very short text
        # 3. Mostly repetitive
        if noise_count > len(words) * 0.2 or len(words) < 5:
            return True
        
        # Check for repetitive content
        unique_words = set(words)
        if len(unique_words) < len(words) * 0.4:  # Less than 40% unique words
            return True
        
        return False
    
    def _clean_content(self, content: str) -> str:
        """Enhanced content cleaning"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common webpage noise patterns
        noise_patterns = [
            r'cookie.*?policy',
            r'terms.*?service',
            r'privacy.*?policy',
            r'subscribe.*?newsletter',
            r'follow.*?social',
            r'share.*?story',
            r'all rights reserved.*?\d{4}',
            r'copyright.*?\d{4}',
            r'loading\.\.\.+',
            r'please enable javascript',
            r'this site requires javascript'
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        content = re.sub(r'[-]{3,}', '---', content)
        
        return content.strip()
    
    async def ask_question_about_url(self, url: str, question: str) -> Dict[str, Any]:
        """Enhanced question answering about URL content"""
        try:
            print(f"Processing question about URL: {url}")
            print(f"Question: {question}")
            
            # Extract content from URL with retry
            content_data = await self.extract_content_from_url(url, retry_count=3)
            
            # Get AI service
            ai_service = self.get_ai_service()
            
            # Create enhanced context for AI
            context = f"""
Website Analysis Request:
Title: {content_data['title']}
URL: {content_data['url']}
Domain: {content_data['metadata'].get('domain', 'Unknown')}
Word Count: {content_data['word_count']} words
Extraction Method: {content_data.get('extraction_method', 'standard')}

Content:
{content_data['content'][:5000]}  # Increased context limit

User Question: {question}

Please provide a comprehensive answer based on the above website content. Focus on accuracy and cite specific information from the content when possible.
"""
            
            # Get AI response
            ai_response = await ai_service.ask_question_simple(context, question)
            
            return {
                "success": True,
                "answer": ai_response["response"],
                "url": url,
                "title": content_data["title"],
                "question": question,
                "word_count": content_data["word_count"],
                "confidence": ai_response.get("confidence", 0.8),
                "source_type": "enhanced_web_content",
                "metadata": content_data["metadata"]
            }
            
        except Exception as e:
            print(f"Error processing question about URL {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "question": question
            }
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global service instance
_enhanced_web_service = None

def get_enhanced_web_service():
    """Get enhanced web scraping service instance"""
    global _enhanced_web_service
    if _enhanced_web_service is None:
        _enhanced_web_service = EnhancedWebScrapingService()
    return _enhanced_web_service