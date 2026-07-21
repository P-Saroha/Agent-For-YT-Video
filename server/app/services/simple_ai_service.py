"""
Simple YouTube AI Service - Direct Gemini API without LangChain complexity.

For quick fallback when the main RAG service has issues.
Uses Google Gemini API directly for simplicity.
"""

import os
import re
import requests
from typing import Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi


def clean_response(text: str) -> str:
    """Clean up AI response formatting while keeping markdown."""
    if not text:
        return ""

    text = text.strip()

    # Fix excessive newlines
    text = re.sub(r'\n{4,}', '\n\n', text)
    
    # Fix spacing around headers
    text = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', text)
    text = re.sub(r'(#{1,6}[^\n]+)\n([^\n#])', r'\1\n\n\2', text)

    # Fix list spacing
    text = re.sub(r'\n([-*+]\s)', r'\n\n\1', text)

    # Remove excessive spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text


class SimpleYouTubeAIService:
    """
    Simple service using direct Gemini API calls.
    
    No LangChain complexity - just straightforward API calls.
    Good for quick fallback or lightweight deployments.
    """

    def __init__(self):
        """Initialize the service."""
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = "gemini-2.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        print("🤖 Simple AI Service initialized")

    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Examples:
            "https://youtube.com/watch?v=dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "https://youtu.be/dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
        """
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
        """
        Get transcript from a YouTube video.
        
        Tries to get English first, then any available transcript.
        """
        try:
            print(f"   Getting transcript for: {video_id}")

            # Get list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get English first
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US'])
            except:
                # Get any available transcript
                transcript = transcript_list.get_transcript(
                    transcript_list.find_generated_transcript(['en']).language_code
                )

            # Extract text from all entries
            text_parts = [entry['text'] for entry in transcript]
            full_text = " ".join(text_parts)

            print(f"   Got {len(full_text)} characters")
            return full_text

        except Exception as e:
            print(f"   ❌ Error getting transcript: {str(e)}")
            return ""

    async def call_gemini_api(self, prompt: str) -> str:
        """
        Call Google Gemini API directly.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Generated text response
        """
        try:
            if not self.api_key:
                return "❌ Error: No Gemini API key configured"

            headers = {'Content-Type': 'application/json'}

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }

            # Make API call
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    answer = data['candidates'][0]['content']['parts'][0]['text']
                    return clean_response(answer)
                else:
                    return "⚠️ No response from AI"
            else:
                return f"❌ API Error: {response.status_code}"

        except Exception as e:
            print(f"   ❌ API Error: {str(e)}")
            return f"❌ Error: {str(e)}"

    async def ask_about_video(self, video_url: str, question: str) -> Dict[str, Any]:
        """
        Ask a question about a YouTube video.
        
        Args:
            video_url: YouTube URL
            question: Question to ask
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            print(f"❓ Processing question about video...")

            # Get video ID
            video_id = self.extract_video_id(video_url)
            
            # Get transcript
            transcript = await self.get_transcript(video_id)
            if not transcript:
                return {
                    "success": False,
                    "answer": "❌ Could not get video transcript. Video might not have subtitles.",
                    "error": "No transcript available"
                }

            # Create prompt for Gemini
            prompt = f"""You are a helpful AI assistant answering questions about YouTube video content.

Video Transcript:
{transcript[:5000]}

User Question: {question}

Instructions:
- Answer based ONLY on the transcript
- Be clear and concise
- Use markdown formatting if helpful
- If the answer isn't in the transcript, say so
- Sound natural and friendly

Answer the question:"""

            # Call Gemini
            answer = await self.call_gemini_api(prompt)

            return {
                "success": True,
                "answer": answer,
                "video_id": video_id,
                "method": "Simple Direct API"
            }

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "answer": f"❌ Error: {str(e)}",
                "error": str(e)
            }

    async def ask_about_text(self, content: str, question: str) -> Dict[str, Any]:
        """
        Ask a question about any text content.
        
        Args:
            content: Text content (from webpage, document, etc.)
            question: Question to ask
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            print(f"❓ Processing question about content...")

            # Create prompt
            prompt = f"""You are a helpful AI assistant answering questions about content.

Content:
{content[:5000]}

User Question: {question}

Instructions:
- Answer based ONLY on the content provided
- Be clear and concise
- Use markdown formatting if helpful
- If the answer isn't in the content, say so
- Sound natural and friendly

Answer the question:"""

            # Call Gemini
            answer = await self.call_gemini_api(prompt)

            return {
                "success": True,
                "answer": answer,
                "method": "Simple Direct API"
            }

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "answer": f"❌ Error: {str(e)}",
                "error": str(e)
            }

    async def summarize_text(self, content: str, title: str = "Content") -> Dict[str, Any]:
        """
        Summarize any text content.
        
        Args:
            content: Text to summarize
            title: Title of the content
            
        Returns:
            Dictionary with summary
        """
        try:
            print(f"📝 Summarizing content...")

            # Create prompt for summary
            prompt = f"""Create a clear summary of this {title}.

Content:
{content[:5000]}

Format the summary as:

## Overview
[2-3 sentence overview]

## Main Points
- Point 1: [Explanation]
- Point 2: [Explanation]
- Point 3: [Explanation]

## Key Takeaways
[Final summary]"""

            # Call Gemini
            summary = await self.call_gemini_api(prompt)

            return {
                "success": True,
                "summary": summary,
                "title": title,
                "method": "Simple Direct API"
            }

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "summary": f"❌ Error: {str(e)}",
                "error": str(e)
            }


def get_simple_service() -> SimpleYouTubeAIService:
    """
    Get an instance of the Simple AI service.
    
    Usage:
        service = get_simple_service()
        result = await service.ask_about_video(video_url, question)
        result = await service.ask_about_text(content, question)
    """
    return SimpleYouTubeAIService()
