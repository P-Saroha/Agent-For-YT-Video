import os
import asyncio
from typing import Dict, List, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import re

class TranscriptService:
    """Service for fetching YouTube video transcripts"""
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    
    async def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get transcript for a YouTube video"""
        try:
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Try to get English transcript first
            try:
                transcript = api.fetch(video_id, languages=['en'])
                transcript_list = transcript.snippets
                language = "en"
            except Exception:
                # If English not available, get list of all available transcripts
                transcript_list_obj = api.list(video_id)
                if not transcript_list_obj:
                    raise Exception("No transcripts available for this video")
                
                # Get the first available transcript (prefer manually created over auto-generated)
                available_transcripts = list(transcript_list_obj)
                if not available_transcripts:
                    raise Exception("No transcripts available for this video")
                
                # Sort by preference: manual first, then auto-generated
                available_transcripts.sort(key=lambda t: (t.is_generated, t.language_code))
                selected_transcript = available_transcripts[0]
                
                # Fetch the selected transcript
                transcript = selected_transcript.fetch()
                transcript_list = transcript.snippets
                language = selected_transcript.language_code
            
            # Combine transcript chunks into full text
            full_transcript = " ".join([item.text for item in transcript_list])
            
            # Get video metadata
            metadata = await self.get_video_metadata(video_id)
            
            return {
                "video_id": video_id,
                "transcript": full_transcript,
                "transcript_chunks": transcript_list,
                "title": metadata.get("title", "Unknown Title"),
                "channel": metadata.get("channel", "Unknown Channel"),
                "duration": metadata.get("duration"),
                "language": language
            }
            
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {e}")
            # Try to get any available transcript as fallback
            try:
                api = YouTubeTranscriptApi()
                transcript_list_obj = api.list(video_id)
                if not transcript_list_obj:
                    raise Exception("No transcripts available for this video")
                
                available_transcripts = list(transcript_list_obj)
                if not available_transcripts:
                    raise Exception("No transcripts available for this video")
                
                # Get the first available transcript
                selected_transcript = available_transcripts[0]
                transcript = selected_transcript.fetch()
                transcript_list = transcript.snippets
                language = selected_transcript.language_code
                
                full_transcript = " ".join([item.text for item in transcript_list])
                metadata = await self.get_video_metadata(video_id)
                
                return {
                    "video_id": video_id,
                    "transcript": full_transcript,
                    "transcript_chunks": transcript_list,
                    "title": metadata.get("title", "Unknown Title"),
                    "channel": metadata.get("channel", "Unknown Channel"),
                    "duration": metadata.get("duration"),
                    "language": language
                }
            except Exception as e2:
                raise Exception(f"Could not get transcript: {e2}")
    
    async def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata from YouTube API or scraping"""
        if self.youtube_api_key:
            return await self.get_metadata_from_api(video_id)
        else:
            return await self.get_metadata_from_scraping(video_id)
    
    async def get_metadata_from_api(self, video_id: str) -> Dict[str, Any]:
        """Get metadata using YouTube Data API"""
        try:
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,contentDetails",
                "id": video_id,
                "key": self.youtube_api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data["items"]:
                item = data["items"][0]
                snippet = item["snippet"]
                content_details = item["contentDetails"]
                
                return {
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "description": snippet.get("description", ""),
                    "duration": content_details["duration"],
                    "published_at": snippet["publishedAt"]
                }
            else:
                return {"title": "Unknown Title", "channel": "Unknown Channel"}
                
        except Exception as e:
            print(f"Error getting metadata from API: {e}")
            return {"title": "Unknown Title", "channel": "Unknown Channel"}
    
    async def get_metadata_from_scraping(self, video_id: str) -> Dict[str, Any]:
        """Get metadata by scraping YouTube page (fallback method)"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Extract title using regex
            title_match = re.search(r'"title":"([^"]*)"', response.text)
            channel_match = re.search(r'"author":"([^"]*)"', response.text)
            
            return {
                "title": title_match.group(1) if title_match else "Unknown Title",
                "channel": channel_match.group(1) if channel_match else "Unknown Channel"
            }
            
        except Exception as e:
            print(f"Error scraping metadata: {e}")
            return {"title": "Unknown Title", "channel": "Unknown Channel"}
    
    def clean_transcript(self, transcript: str) -> str:
        """Clean and normalize transcript text"""
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript)
        
        # Remove common transcript artifacts
        transcript = re.sub(r'\[.*?\]', '', transcript)  # Remove [Music], [Applause], etc.
        transcript = re.sub(r'\(.*?\)', '', transcript)  # Remove (inaudible), etc.
        
        # Normalize punctuation
        transcript = re.sub(r'([.!?])\s*', r'\1 ', transcript)
        
        return transcript.strip()
