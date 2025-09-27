"""
Simple YouTube AI service using only direct Gemini API
No LangChain dependencies - deployment friendly
"""
import os
import asyncio
import requests
import json
from typing import Dict, Any, List
from youtube_transcript_api import YouTubeTranscriptApi


class SimpleYouTubeAIService:
    """Simplified YouTube AI service for deployment"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDvhlqz_tSdNpkG6OZyryXyp5qUYjwDGcc")
        self.model = "gemini-1.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        print("🚀 Simple YouTube AI Service initialized for deployment")
    
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
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry['text'] for entry in transcript_list])
            return transcript_text
        except Exception as e:
            print(f"❌ Error getting transcript: {e}")
            return ""
    
    async def ask_gemini(self, question: str, transcript: str) -> str:
        """Ask Gemini AI about the video content"""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            prompt = f"""Based on this YouTube video transcript, please answer the question.

Transcript:
{transcript[:4000]}  # Limit to avoid token limits

Question: {question}

Please provide a comprehensive answer based only on the information in the transcript."""
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
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
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Sorry, I couldn't generate an answer from the video content."
            else:
                print(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return "Sorry, there was an error processing your question."
                
        except Exception as e:
            print(f"❌ Error asking Gemini: {e}")
            return "Sorry, there was an error processing your question."
    
    async def process_video_question(self, video_url: str, question: str) -> Dict[str, Any]:
        """Main method to process video question"""
        try:
            # Extract video ID
            video_id = self.extract_video_id(video_url)
            print(f"📹 Processing video: {video_id}")
            
            # Get transcript
            transcript = await self.get_transcript(video_id)
            if not transcript:
                return {
                    "success": False,
                    "error": "Could not retrieve video transcript. The video might not have subtitles available.",
                    "video_id": video_id
                }
            
            print(f"📝 Got transcript: {len(transcript)} characters")
            
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


# Global instance
_simple_service = None

def get_simple_service():
    """Get or create simple service instance"""
    global _simple_service
    if _simple_service is None:
        _simple_service = SimpleYouTubeAIService()
    return _simple_service