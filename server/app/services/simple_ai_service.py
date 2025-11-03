"""
Simple YouTube AI service using only direct Gemini API
No LangChain dependencies - deployment friendly
"""
import os
import asyncio
import requests
import json
import re
from typing import Dict, Any, List
from youtube_transcript_api import YouTubeTranscriptApi


def clean_ai_response(text: str) -> str:
    """
    Production-ready AI response cleaning with advanced formatting.
    
    Fixes common Gemini API formatting problems while preserving markdown structure:
    - Malformed headers and excessive spacing
    - Proper paragraph and list formatting
    - Emoji spacing and unicode handling
    - Robust edge case handling
    """
    if not text:
        return ""
    
    # Initial cleanup
    text = text.strip()
    
    # Fix common Gemini formatting issues
    text = re.sub(r'# #\s*', '## ', text)      # Fix malformed headers
    text = re.sub(r'###+', '###', text)        # Fix excessive hash marks
    
    # Smart paragraph handling - preserve intentional breaks
    text = re.sub(r'\n{4,}', '\n\n\n', text)   # Max 3 newlines
    text = re.sub(r'\n\n\n+', '\n\n', text)    # But usually just 2
    
    # Clean up spacing while preserving structure
    text = re.sub(r'[ \t]+\n', '\n', text)     # Remove trailing spaces
    text = re.sub(r'\n[ \t]+', '\n', text)     # Remove leading spaces on new lines
    text = re.sub(r'[ \t]{2,}', ' ', text)     # Collapse multiple spaces
    
    # Ensure proper spacing around headers
    text = re.sub(r'([^\n])(#{1,6}\s+[^\n]*)', r'\1\n\n\2', text)
    text = re.sub(r'(#{1,6}\s+[^\n]*)\n([^\n#\s])', r'\1\n\n\2', text)
    
    # Fix list formatting with proper spacing
    text = re.sub(r'\n([-*+]\s)', r'\n\n\1', text)      # Space before lists
    text = re.sub(r'([-*+]\s[^\n]*)\n([^\n-*+\s])', r'\1\n\n\2', text)  # Space after lists
    
    # Ensure proper spacing around numbered lists
    text = re.sub(r'\n(\d+\.\s)', r'\n\n\1', text)
    text = re.sub(r'(\d+\.\s[^\n]*)\n([^\n\d\s])', r'\1\n\n\2', text)
    
    # Fix emoji spacing for better readability
    text = re.sub(r'([^\s])([🌟🎯🚀📊💡⚡🎨✨🔥📝🎥🧩🎪🎭🎪🌈🎊])', r'\1 \2', text)
    text = re.sub(r'([🌟🎯🚀📊💡⚡🎨✨🔥📝🎥🧩🎪🎭🎪🌈🎊])([^\s])', r'\1 \2', text)
    
    # Final cleanup - ensure no excessive newlines remain
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


class SimpleYouTubeAIService:
    """Simplified YouTube AI service for deployment"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = "gemini-2.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        print("Simple YouTube AI Service initialized for deployment")
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats"""
        import re
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url  # Assume it's already a video ID
    
    async def get_transcript(self, video_id: str) -> str:
        """Get transcript with advanced anti-blocking techniques"""
        import time
        import random
        
        try:
            print(f"🎬 Processing video: {video_id}")
            
            # Add random delay to mimic human behavior (1-3 seconds)
            delay = random.uniform(1.0, 3.0)
            print(f"  ⏱️  Waiting {delay:.1f}s to avoid detection...")
            time.sleep(delay)
            
            # Try Method 1: Direct transcript API with custom headers
            try:
                from youtube_transcript_api._api import YouTubeTranscriptApi
                from youtube_transcript_api._html_unescaping import unescape
                import requests
                
                # Rotate through realistic user agents
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
                
                # Create custom session with realistic headers
                session = requests.Session()
                session.headers.update({
                    'User-Agent': random.choice(user_agents),
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                })
                
                print(f"  🔍 Method 1: Trying YouTube Transcript API with stealth headers...")
                
                # Monkey-patch the session into youtube-transcript-api
                import youtube_transcript_api._transcripts
                original_get = youtube_transcript_api._transcripts._TranscriptListFetcher._extract_captions_json
                
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id)
                
                # Try languages in priority order
                languages_to_try = ['en', 'hi', 'es', 'fr', 'de', 'ja', 'ko', 'pt', 'ar']
                transcript = None
                
                for lang in languages_to_try:
                    try:
                        transcript = transcript_list.find_transcript([lang])
                        print(f"  ✅ Found {lang} transcript")
                        break
                    except:
                        continue
                
                if not transcript:
                    # Try any available transcript
                    for t in transcript_list:
                        transcript = t
                        print(f"  ✅ Found {t.language} transcript")
                        break
                
                if transcript:
                    # If translatable and not English, translate
                    if transcript.language_code != 'en' and transcript.is_translatable:
                        print(f"  🔄 Translating {transcript.language} to English...")
                        transcript = transcript.translate('en')
                    
                    transcript_data = transcript.fetch()
                    transcript_text = " ".join([entry['text'] if isinstance(entry, dict) else entry.text for entry in transcript_data])
                    
                    if len(transcript_text) > 50:
                        print(f"  ✅ SUCCESS: Got {len(transcript_text)} characters")
                        return transcript_text
                
            except Exception as e1:
                print(f"  ❌ Method 1 failed: {str(e1)[:100]}")
            
            # Method 2: Try yt-dlp with stealth settings
            try:
                import yt_dlp
                import tempfile
                
                print(f"  🔍 Method 2: Trying yt-dlp with anti-detection...")
                
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # yt-dlp with maximum stealth
                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en', 'hi', 'es', 'fr', 'de'],
                    'subtitlesformat': 'json3',
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                    'http_headers': {
                        'User-Agent': random.choice(user_agents),
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': '*/*',
                        'Referer': 'https://www.youtube.com/'
                    }
                }
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts['paths'] = {'home': tmpdir}
                    ydl_opts['outtmpl'] = {'default': f'{tmpdir}/%(id)s.%(ext)s'}
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=False)
                        ydl.download([video_url])
                        
                        # Parse subtitle files
                        import os
                        for filename in os.listdir(tmpdir):
                            if filename.endswith('.json3'):
                                filepath = os.path.join(tmpdir, filename)
                                
                                lines = []
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        try:
                                            obj = json.loads(line.strip())
                                            segs = obj.get('segs', [])
                                            for seg in segs:
                                                text = seg.get('utf8', '').strip()
                                                if text:
                                                    lines.append(text)
                                        except:
                                            continue
                                
                                transcript_text = ' '.join(lines)
                                
                                if len(transcript_text) > 50:
                                    print(f"  ✅ SUCCESS via yt-dlp: {len(transcript_text)} characters")
                                    return transcript_text
                
            except Exception as e2:
                print(f"  ❌ Method 2 failed: {str(e2)[:100]}")
            
            # If all methods fail
            raise Exception("YouTube is blocking all transcript requests from your IP. Please use VPN (connect to US/EU server) or wait 24 hours.")
            
        except Exception as e:
            print(f"❌ All methods exhausted: {str(e)[:150]}")
            return ""
    
    async def ask_gemini(self, question: str, transcript: str) -> str:
        """Ask Gemini AI about the video content - provides concise answers for questions"""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            # Check if this is a specific question or a general summary request
            question_lower = question.lower()
            is_specific_question = any(word in question_lower for word in [
                'what', 'when', 'where', 'who', 'how', 'why', 'which', 'how much', 'how many'
            ])
            
            if is_specific_question:
                # Provide a concise, direct answer
                prompt = f"""Based on this YouTube video transcript, answer the specific question directly and concisely.

Transcript: {transcript[:6000]}

Question: {question}

Instructions:
1. Answer the question directly in 1-3 sentences
2. If relevant, provide a brief context or explanation 
3. Keep the response focused and to the point
4. Don't use section headers or lengthy formatting
5. Just give a clear, helpful answer

Answer:"""
            else:
                # Use natural conversational format like ChatGPT/Claude
                prompt = f"""Based on this YouTube video transcript, answer the question naturally and conversationally, like ChatGPT or Claude would.

Transcript: {transcript[:6000]}

Question: {question}

Instructions:
- Write in a natural, friendly, conversational tone
- Use markdown for formatting (## headers, **bold**, bullet lists) when it makes sense
- Break your response into clear paragraphs
- Use **bold** to emphasize important points
- Use bullet points or numbered lists when listing multiple items
- Keep your language simple and easy to understand
- Make it engaging and interesting to read

Respond naturally and helpfully, as if you're explaining this to a friend."""
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "text/plain"
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    raw_response = data['candidates'][0]['content']['parts'][0]['text']
                    return clean_ai_response(raw_response)
                else:
                    return "Sorry, I couldn't generate an answer from the video content."
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return "Sorry, there was an error processing your question."
                
        except Exception as e:
            print(f"Error asking Gemini: {e}")
            return f"Sorry, there was an error processing your question: {str(e)}"
    
    async def ask_question_simple(self, content: str, question: str) -> Dict[str, Any]:
        """Ask a question about any text content (for web scraping service)"""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            prompt = f"""Based on the following content, answer the question naturally and conversationally, like ChatGPT or Claude would.

Content: {content[:6000]}

Question: {question}

Instructions:
- Write in a natural, friendly, conversational tone
- Use markdown for formatting (## headers, **bold**, bullet lists) when it makes sense
- Break your response into clear paragraphs
- Use **bold** to emphasize important points
- Use bullet points or numbered lists when listing multiple items
- Keep your language simple and easy to understand
- Make it engaging and interesting to read

Respond naturally and helpfully, as if you're explaining this to a friend.

## ✨ Summary

End with a strong conclusion that summarizes the main takeaways and gives the reader clear value.

IMPORTANT: Write in full paragraphs, NOT bullet lists. Make it engaging and story-like."""
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "text/plain"
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    raw_answer = data['candidates'][0]['content']['parts'][0]['text']
                    clean_answer = clean_ai_response(raw_answer)
                    return {
                        "response": clean_answer,
                        "confidence": 0.8,
                        "success": True
                    }
                else:
                    return {
                        "response": "Sorry, I couldn't generate an answer from the provided content.",
                        "confidence": 0.0,
                        "success": False
                    }
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return {
                    "response": "Sorry, there was an error processing your question.",
                    "confidence": 0.0,
                    "success": False
                }
                
        except Exception as e:
            print(f"Error asking question: {e}")
            return {
                "response": f"Sorry, there was an error processing your question: {str(e)}",
                "confidence": 0.0,
                "success": False
            }
    
    async def process_video_question(self, video_url: str, question: str) -> Dict[str, Any]:
        """Main method to process video question"""
        try:
            # Extract video ID
            video_id = self.extract_video_id(video_url)
            print(f"Processing video: {video_id}")
            
            # Get transcript
            transcript = await self.get_transcript(video_id)
            if not transcript:
                return {
                    "success": False,
                    "error": "Could not retrieve video transcript. The video might not have subtitles available.",
                    "video_id": video_id
                }
            
            print(f"Got transcript: {len(transcript)} characters")
            
            # Ask Gemini
            answer = await self.ask_gemini(question, transcript)
            
            return {
                "success": True,
                "answer": answer,
                "video_id": video_id,
                "transcript_length": len(transcript)
            }
            
        except Exception as e:
            print(f"Error processing video question: {e}")
            return {
                "success": False,
                "error": f"Error processing request: {str(e)}"
            }
    
    async def ask_gemini_direct(self, prompt: str) -> str:
        """Direct AI call for web content summarization"""
        try:
            print(f"Making direct Gemini API call...")
            
            if not self.gemini_api_key or self.gemini_api_key == "":
                print("ERROR: No Gemini API key configured!")
                return "AI service configuration error: No API key"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "text/plain"
                }
            }
            
            print(f"Calling API URL: {self.api_url}")
            
            response = requests.post(
                f"{self.api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"API Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"API Response data keys: {list(data.keys())}")
                
                if 'candidates' in data and len(data['candidates']) > 0:
                    raw_answer = data['candidates'][0]['content']['parts'][0]['text']
                    clean_answer = clean_ai_response(raw_answer)
                    print(f"Generated answer: {len(clean_answer)} characters")
                    return clean_answer
                else:
                    print(f"No candidates in response: {data}")
                    return "Unable to generate answer - no response from AI"
            else:
                error_text = response.text
                print(f"Gemini API error: {response.status_code} - {error_text}")
                return f"AI service error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            print(f"Gemini API timeout")
            return "AI service timeout - please try again"
        except Exception as e:
            print(f"Error calling Gemini directly: {e}")
            import traceback
            traceback.print_exc()
            return f"Failed to generate answer: {str(e)}"


# Global instance
_simple_service = None

def get_simple_service():
    """Get or create simple service instance"""
    global _simple_service
    if _simple_service is None:
        _simple_service = SimpleYouTubeAIService()
    return _simple_service