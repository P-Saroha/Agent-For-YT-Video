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
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDvhlqz_tSdNpkG6OZyryXyp5qUYjwDGcc")
        self.model = "gemini-2.5-flash"  # NEWER FREE Flash model (2.5 version)
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
        """Get transcript for video"""
        try:
            print(f"Processing video: {video_id}")
            # Use the correct API - create instance and call list, then find transcript
            from youtube_transcript_api._api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Find English transcript or fallback to any available
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                transcript = transcript_list.find_transcript(['hi', 'es', 'fr', 'de', 'auto'])
            
            # Fetch the actual transcript data
            transcript_data = transcript.fetch()
            transcript_text = " ".join([entry.text for entry in transcript_data])  # Use .text instead of ['text']
            print(f"Successfully got transcript: {len(transcript_text)} characters")
            return transcript_text
            
        except Exception as e:
            print(f"Error getting transcript: {e}")
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
                # Use the detailed format for summaries
                prompt = f"""Based on this YouTube video transcript, answer the question with an engaging, well-formatted response.

Transcript: {transcript[:6000]}

Question: {question}

Format your response exactly like this:

## 🎥 [Creative Title Related to the Content]

Start with a compelling paragraph that immediately captures what this video is about. Make it interesting and engaging.

## 📝 Key Points

Write 2-3 natural paragraphs here explaining the main content. Use normal sentences, not bullet points. Make it flow like a story or article that someone would actually want to read.

## 💡 Important Details  

Add another 2-3 paragraphs with more specific information, insights, or interesting details from the video. Keep it conversational and engaging.

## ✨ Summary

End with a strong conclusion paragraph that ties everything together and gives the reader clear takeaways.

CRITICAL: Each section must be 2-3 full paragraphs, NOT bullet points. Write like you're telling an interesting story."""
            
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
            
            prompt = f"""Based on the following content, answer the question with a well-formatted, engaging response.

Content: {content[:6000]}

Question: {question}

Format exactly like this:

## 🌟 [Creative Title]

Write an engaging opening paragraph that immediately answers the main question and captures the reader's interest.

## 📊 Main Information

Write 2-3 natural paragraphs explaining the key points. Use complete sentences and make it flow like an interesting article, not bullet points.

## 💡 Key Details

Add 2-3 more paragraphs with important details, insights, or specific information. Keep it conversational and engaging.

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
            print(f"❌ Error processing video question: {e}")
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