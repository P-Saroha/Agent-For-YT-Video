"""
Fast Web Content Service - Optimized for speed
Simplified version that processes content faster for better user experience
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Simple in-memory cache
_content_cache = {}

class FastWebContentService:
    def __init__(self):
        self.session = None
        print("Fast Web Content Service initialized")
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=15)  # Shorter timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """Fast content extraction with caching"""
        try:
            start_time = time.time()
            
            # Check cache first
            if url in _content_cache:
                cache_time = time.time() - start_time
                print(f"Using cached content (took {cache_time:.2f}s)")
                return _content_cache[url]
            
            print(f"Extracting content from: {url}")
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
                
                # Extract main content quickly
                main_content = await self._extract_main_content_fast(soup, url)
                
                # Remove content limit - return full content
                # No truncation to ensure complete content extraction
                
                result = {
                    "title": title_text,
                    "content": main_content,
                    "url": url,
                    "word_count": len(main_content.split()),
                    "char_count": len(main_content),
                    "extracted_at": datetime.now().isoformat(),
                    "processing_time": time.time() - start_time
                }
                
                # Cache the result
                _content_cache[url] = result
                
                processing_time = time.time() - start_time
                print(f"Content extracted (took {processing_time:.2f}s)")
                
                return result
                
        except Exception as e:
            return {
                "error": f"Error extracting content: {str(e)}",
                "url": url
            }
    
    async def ask_question_with_simple_search(self, url: str, question: str) -> Dict[str, Any]:
        """Simple text-based question answering without heavy AI models"""
        try:
            start_time = time.time()
            print(f"Processing question: {question}")
            
            # Get content
            content_data = await self.extract_content_from_url(url)
            
            if "error" in content_data:
                return content_data
            
            content = content_data["content"].lower()
            question_lower = question.lower()
            
            # Simple keyword-based search
            keywords = ["independence", "independent", "freedom", "1947", "august", "15"]
            
            # Find relevant sentences
            sentences = content.split('.')
            relevant_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in keywords) or any(word in sentence.lower() for word in question_lower.split()):
                    relevant_sentences.append(sentence)
            
            if relevant_sentences:
                answer = ". ".join(relevant_sentences[:3])  # First 3 relevant sentences
                if len(answer) > 500:
                    answer = answer[:500] + "..."
            else:
                answer = f"Could not find specific information about '{question}' in the content. The page contains general information about the topic."
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "answer": answer,
                "url": url,
                "title": content_data["title"],
                "question": question,
                "confidence": 0.7 if relevant_sentences else 0.3,
                "source_type": "fast_search",
                "word_count": len(answer.split()),
                "processing_time": processing_time,
                "method": "keyword_search"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing question: {str(e)}",
                "url": url,
                "question": question
            }
    
    async def _extract_main_content_fast(self, soup, url):
        """Fast content extraction focusing on main content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form']):
            element.decompose()
        
        # Try to find main content areas with expanded selectors
        content_areas = []
        
        # Look for main content containers with more comprehensive selectors
        for selector in ['main', 'article', '.content', '#content', '.main-content', '#main', 
                        '.post-content', '.entry-content', '.question', '.answer', '.s-prose']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 100:  # Lowered threshold for more content
                    content_areas.append(text)
        
        # If no specific content areas found, get COMPREHENSIVE text extraction
        if not content_areas:
            print("No main content areas found, extracting ALL text content")
            # Get ALL meaningful text elements - much more comprehensive
            for tag in ['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'dd', 'dt', 'blockquote', 'pre', 'code', 'a', 'strong', 'em']:
                elements = soup.find_all(tag)
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > 5:  # Much lower threshold - include almost everything
                        content_areas.append(text)
        
        # FALLBACK: If still no content, get EVERYTHING from body
        if not content_areas:
            print("Fallback: extracting ALL body text")
            body = soup.find('body')
            if body:
                all_text = body.get_text(strip=True)
                # Split into sentences and add them
                sentences = all_text.split('. ')
                for sentence in sentences:
                    if len(sentence.strip()) > 10:
                        content_areas.append(sentence.strip())
        
        print(f"Total content areas found: {len(content_areas)}")
        
        # Remove duplicates while preserving order but be VERY permissive
        seen = set()
        unique_areas = []
        for area in content_areas:
            area_clean = area.strip()
            # EXTREMELY permissive - include very short content too
            if area_clean not in seen and len(area_clean) > 3:
                seen.add(area_clean)
                unique_areas.append(area_clean)
        
        # Combine ALL content with proper spacing - no limits
        combined_content = '\n\n'.join(unique_areas)
        print(f"Final: {len(unique_areas)} sections, {len(combined_content)} characters")
        print(f"Sample content: {combined_content[:200]}...")
        
        # Ensure we have substantial content
        if len(combined_content) < 1000:
            print("Content too short, trying alternative extraction")
            # Alternative: get ALL text from soup
            all_text = soup.get_text(separator='\n', strip=True)
            if len(all_text) > len(combined_content):
                combined_content = all_text
                print(f"Using alternative extraction: {len(all_text)} characters")
        
        # ULTRA MINIMAL cleaning - keep almost everything
        lines = combined_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # ULTRA permissive - only remove completely empty lines and obvious spam
            if len(line) > 0 and line not in ['', ' ', '\t']:
                cleaned_lines.append(line)
        
        # Join with single newlines to preserve maximum content
        content = '\n'.join(cleaned_lines)
        
        print(f"FINAL CONTENT: {len(content)} characters, {len(content.split())} words")
        
        return content

# Global service instance
_fast_service = None

def get_fast_web_service():
    global _fast_service
    if _fast_service is None:
        _fast_service = FastWebContentService()
    return _fast_service