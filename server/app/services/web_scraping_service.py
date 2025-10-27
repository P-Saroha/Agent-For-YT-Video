import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
from typing import Optional, Dict, Any
import os

class WebScrapingService:
    def __init__(self):
        self.session = None
        self.ai_service = None
        print("Web scraping service initialized")
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
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
    
    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """Extract content from any website URL"""
        try:
            print(f"Extracting content from: {url}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            session = await self.get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: Failed to fetch URL")
                
                html_content = await response.text()
                
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup, url)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Clean and process content
            print(f"Raw content length before cleaning: {len(content)} characters")
            cleaned_content = self._clean_content(content)
            print(f"Cleaned content length: {len(cleaned_content)} characters")
            print(f"First 200 chars of cleaned content: {repr(cleaned_content[:200])}")
            
            if not cleaned_content.strip() or len(cleaned_content.strip()) < 50:
                # Last resort: try to get any readable text
                all_text = soup.get_text(separator=' ', strip=True)
                cleaned_content = self._clean_content(all_text)
                
                if not cleaned_content.strip() or len(cleaned_content.strip()) < 50:
                    # Check if this looks like a JavaScript-heavy site
                    script_tags = len(soup.find_all('script'))
                    total_html_length = len(html_content)
                    
                    if script_tags > 5 and total_html_length > 20000:
                        # Likely a JavaScript-rendered site
                        domain = urlparse(url).netloc.lower()
                        if 'msn.com' in domain:
                            raise Exception(f"MSN articles use advanced loading technology that requires a browser to view. Please try a different news source like BBC News, Reuters, or Wikipedia instead.")
                        else:
                            raise Exception(f"This website ({domain}) uses advanced loading technology. Please try simpler sites like Wikipedia, BBC News, or documentation pages.")
                    else:
                        raise Exception("No readable content found on the webpage")
            
            print(f"Successfully extracted {len(cleaned_content)} characters from {url}")
            
            return {
                "url": url,
                "title": title,
                "content": cleaned_content,
                "metadata": metadata,
                "word_count": len(cleaned_content.split()),
                "extracted_at": time.time()
            }
            
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            raise Exception(f"Failed to extract content: {str(e)}")
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title"""
        # Try different title sources
        title_sources = [
            soup.find('title'),
            soup.find('meta', attrs={'property': 'og:title'}),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('h1')
        ]
        
        for source in title_sources:
            if source:
                title = source.get('content') if source.name == 'meta' else source.get_text()
                if title and title.strip():
                    return title.strip()
        
        # Fallback to URL
        return urlparse(url).netloc
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage with enhanced MSN support"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement', 'iframe', 'noscript']):
            element.decompose()
        
        # Enhanced selectors including Reddit and social media specific ones
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
            # Reddit-specific selectors
            '[data-testid="post-content"]',
            '.Post',
            '[data-click-id="body"]',
            '.thing .entry',
            '.usertext-body',
            '.md',
            '.expando',
            '.sitetable',
            # Social media and forum selectors
            '.feed',
            '.timeline',
            '.posts',
            '.discussions',
            '.threads',
            '[class*="post"]',
            '[class*="feed"]',
            '[data-testid*="post"]',
            '.article-content',
            '.post-body',
            '.content-body',
            # MSN-specific selectors
            '.article-text',
            '.article-content-container',
            '.content-wrapper',
            '[data-module="ArticleBody"]',
            '[data-module="ContentBlock"]',
            '.newsarticlebody',
            '.story-content',
            # Generic content selectors
            '[id*="content"]',
            '[class*="content"]',
            '[id*="article"]',
            '[class*="article"]',
            '[class*="body"]',
            '[class*="text"]'
        ]
        
        content_text = ""
        
        # Try main content selectors first
        for selector in main_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.get_text(separator=' ', strip=True)
                        if len(text) > 100:  # Minimum content threshold
                            content_text += text + " "
                    if len(content_text.strip()) > 200:  # Good content found
                        break
            except Exception:
                continue
        
        # If still no good content, try more aggressive extraction with Reddit/social media patterns
        if len(content_text.strip()) < 200:
            # Try paragraphs and headings with better filtering
            content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'])
            for element in content_elements:
                text = element.get_text(strip=True)
                # More lenient filtering for social media content
                if len(text) > 10 and not self._is_noise_text(text):
                    content_text += text + " "
                    
        # Reddit-specific extraction for posts and comments
        if len(content_text.strip()) < 200:
            reddit_selectors = [
                '[data-testid*="comment"]',
                '.thing',
                '.entry',
                '.usertext',
                '.md-container',
                'div[class*="Post"]',
                'div[class*="Comment"]'
            ]
            
            for selector in reddit_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(separator=' ', strip=True)
                        if len(text) > 20 and not self._is_noise_text(text):
                            content_text += text + " "
                except Exception:
                    continue
        
        # Enhanced fallback: look for data attributes and specific patterns
        if len(content_text.strip()) < 100:
            # MSN often uses data attributes
            data_elements = soup.find_all(['div', 'span'], attrs={'data-module': True})
            for element in data_elements:
                text = element.get_text(strip=True)
                if len(text) > 20 and not self._is_noise_text(text):
                    content_text += text + " "
        
        # Last resort: get all text from divs and spans with better filtering
        if len(content_text.strip()) < 50:
            content_elements = soup.find_all(['div', 'span'])
            for element in content_elements:
                text = element.get_text(strip=True)
                # Use the noise filter to improve quality
                if len(text) > 25 and not self._is_noise_text(text):
                    content_text += text + " "
        
        return content_text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract metadata from webpage"""
        metadata = {
            "domain": urlparse(url).netloc,
            "url": url
        }
        
        # Extract meta description
        desc_meta = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', attrs={'property': 'og:description'})
        if desc_meta:
            metadata["description"] = desc_meta.get('content', '').strip()
        
        # Extract author
        author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                     soup.find('meta', attrs={'property': 'og:author'})
        if author_meta:
            metadata["author"] = author_meta.get('content', '').strip()
        
        # Extract keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            metadata["keywords"] = keywords_meta.get('content', '').strip()
        
        return metadata
    
    def _is_noise_text(self, text: str) -> bool:
        """Check if text is likely noise/boilerplate content"""
        if not text or len(text.strip()) < 10:
            return True
            
        text_lower = text.lower()
        noise_indicators = [
            'cookie', 'privacy policy', 'terms of service', 'subscribe',
            'newsletter', 'advertisement', 'click here', 'read more',
            'follow us', 'social media', 'share this', 'all rights reserved',
            'copyright', '© 2024', '© 2025', 'loading', 'please wait',
            'sign in', 'sign up', 'login', 'register', 'download app',
            'view more', 'show more', 'load more', 'continue reading',
            # Reddit-specific noise (but be more selective)
            'sort by:', 'best hot new top rising', 'community highlights'
        ]
        
        # Check if text is mostly noise indicators
        noise_count = sum(1 for indicator in noise_indicators if indicator in text_lower)
        words = text.split()
        
        # Consider it noise if high ratio of noise indicators or very repetitive
        if noise_count > len(words) * 0.3:
            return True
            
        # Check for repetitive content (common in navigation/menus)
        unique_words = set(word.lower() for word in words)
        if len(words) > 5 and len(unique_words) < len(words) * 0.4:
            return True
            
        return False

    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content with better formatting"""
        if not content:
            return ""
            
        # First, normalize whitespace but preserve sentence structure
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Fix broken sentences and words
        content = re.sub(r'\s+([,.;:!?])', r'\1', content)
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', content)
        
        # Clean up excessive line breaks but preserve paragraphs
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'\n\s+', '\n', content)
        
        # Remove lines that are just noise or navigation
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and len(line) > 5 and not self._is_noise_line(line):
                lines.append(line)
        
        # Join lines with proper spacing
        content = ' '.join(lines)
        
        # Clean up sentence structure
        content = re.sub(r'\s+([.!?])\s+', r'\1 ', content)
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', content)
        
        # Add paragraph breaks at natural points
        content = re.sub(r'([.!?])\s+([A-Z][^.!?]{50,})', r'\1\n\n\2', content)
        
        return content.strip()
        
    def _is_noise_line(self, line: str) -> bool:
        """Check if a line is likely noise content"""
        line_lower = line.lower()
        
        # Skip very short lines
        if len(line.strip()) < 8:
            return True
            
        # Navigation and UI elements
        noise_patterns = [
            'edit', 'talk page', 'learn how and when to remove',
            'citation needed', 'this article', 'help improve',
            'discuss these issues', 'remove this message',
            'cookie', 'privacy', 'terms of service',
            'subscribe', 'newsletter', 'follow us'
        ]
        
        for pattern in noise_patterns:
            if pattern in line_lower:
                return True
                
        return False
    
    async def ask_question_about_url(self, url: str, question: str) -> Dict[str, Any]:
        """Ask a question about content from any URL"""
        try:
            print(f"Processing question about URL: {url}")
            print(f"Question: {question}")
            
            # Extract content from URL
            content_data = await self.extract_content_from_url(url)
            
            # Get AI service
            ai_service = self.get_ai_service()
            
            # Create context for AI
            context = f"""
Title: {content_data['title']}
URL: {content_data['url']}
Content: {content_data['content'][:4000]}  # Limit context to prevent token overflow

Please answer the following question based on the above webpage content:
Question: {question}
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
                "confidence": ai_response.get("confidence", 0.7),
                "source_type": "web_content"
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
_web_service = None

def get_web_service():
    """Get web scraping service instance"""
    global _web_service
    if _web_service is None:
        _web_service = WebScrapingService()
    return _web_service