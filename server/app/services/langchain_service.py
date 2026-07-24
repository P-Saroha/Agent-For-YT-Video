"""
YouTube Video Analysis Service using LangChain and Google Gemini.

How it works:
1. Get the video transcript from YouTube
2. Split the transcript into smaller pieces (chunks)
3. Convert each chunk to a vector (embedding)
4. Store vectors in a database (ChromaDB)
5. When user asks a question:
   - Convert question to vector
   - Find similar chunks using vector similarity
   - Send similar chunks + question to Google Gemini
   - Gemini generates an answer
"""

import os
import re
import tempfile
import shutil
from typing import Dict, Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeRAGService:
    """
    Service to analyze YouTube videos using RAG (Retrieval-Augmented Generation).
    
    RAG = Get relevant information from the video, then use AI to answer questions.
    """

    def __init__(self):
        """Initialize all components needed for video analysis."""
        
        print("Initializing YouTube Video Analysis Service...")

        # ==================== Component 1: Text-to-Vector Converter ====================
        # This converts text into numbers (vectors) that computers can compare
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32  # Process 32 texts at a time (faster)
            }
        )

        # ==================== Component 2: Text Splitter ====================
        # This breaks long text into smaller chunks so the AI can process them
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,           # Each chunk is 800 characters
            chunk_overlap=100,        # 100 characters overlap between chunks (keeps context)
            separators=["\n\n", "\n", ".", "!", "?", " "]  # Split at these characters first
        )

        # ==================== Component 3: AI Model (Gemini) ====================
        # This is the brain that generates answers
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Fast and free model from Google
            temperature=0.0,           # 0 = deterministic (same answer every time), higher = more creative
            convert_system_message_to_human=True
        )

        # ==================== Component 4: Question-Answer Prompt ====================
        # This tells Gemini HOW to answer questions
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant analyzing YouTube video content.

Here is information from the video:
{context}

Rules:
- Answer the question based ONLY on the video content above
- Be clear and concise
- Use markdown formatting (headers, bold, lists) to make answers readable
- If the answer is not in the video content, say "This information is not in the video"
- Sound natural and friendly, like a real person explaining something"""),
            ("human", "{input}")
        ])

        # ==================== Component 5: Memory/Cache ====================
        # Store processed videos to avoid reprocessing
        self.processed_videos = {}    # Maps video_id -> metadata
        self.vector_stores = {}        # Maps video_id -> vector database
        self.temp_directories = {}    # Maps video_id -> temporary folder path

        print("YouTube Service ready!")

    def extract_video_id(self, video_url: str) -> str:
        """
        Extract the video ID from a YouTube URL.
        
        Examples:
            "https://youtube.com/watch?v=dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "https://youtu.be/dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
            "dQw4w9WgXcQ" -> "dQw4w9WgXcQ"
        """
        # Try different URL patterns
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([^&]+)',      # youtube.com/watch?v=...
            r'(?:youtu\.be\/)([^?]+)',                  # youtu.be/...
            r'(?:youtube\.com\/embed\/)([^?]+)'         # youtube.com/embed/...
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)

        # If no pattern matches, assume it's already a video ID
        return video_url

    async def process_video(self, video_url: str) -> Dict[str, Any]:
        """
        Process a YouTube video so it can be asked questions about.
        
        Steps:
        1. Get transcript from YouTube
        2. Split into chunks
        3. Convert to vectors
        4. Store in database
        
        Args:
            video_url: YouTube URL or video ID
            
        Returns:
            Dictionary with processing results
        """
        try:
            video_id = self.extract_video_id(video_url)
            
            # Check if already processed
            if video_id in self.processed_videos:
                print(f"Video {video_id} already processed (using cached data)")
                return self.processed_videos[video_id]

            print(f"Processing video: {video_id}")

            # Step 1: Get transcript from YouTube
            print(f"   1. Getting transcript...")
            transcript = await self._get_transcript(video_id)
            
            # Step 2: Create a document from the transcript
            doc = Document(
                page_content=transcript["text"],
                metadata={
                    "video_id": video_id,
                    "title": transcript.get("title", "Unknown"),
                    "language": transcript.get("language", "unknown")
                }
            )

            # Step 3: Split into chunks
            print(f"   2. Splitting into chunks...")
            chunks = self.text_splitter.split_documents([doc])
            print(f"      Created {len(chunks)} chunks")

            # Step 4: Create temporary directory for vector database
            temp_dir = tempfile.mkdtemp(prefix=f"video_{video_id}_")

            # Step 5: Convert chunks to vectors and store
            print(f"   3. Converting text to vectors...")
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )

            # Step 6: Create a retriever (searches the vector database)
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 10}  # Return top 10 most relevant chunks
            )

            # Step 7: Create the RAG chain (combines retriever + AI)
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.qa_prompt
            )
            rag_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=document_chain
            )

            # Store in memory for future use
            self.processed_videos[video_id] = {
                "title": transcript.get("title", "Unknown"),
                "chunks": len(chunks),
                "language": transcript.get("language", "unknown"),
                "status": "processed"
            }
            self.vector_stores[video_id] = rag_chain
            self.temp_directories[video_id] = temp_dir

            print(f"Video {video_id} processed successfully!")

            return self.processed_videos[video_id]

        except Exception as e:
            print(f"Error processing video: {str(e)}")
            raise

    async def ask_question(self, video_id: str, question: str) -> Dict[str, Any]:
        """
        Ask a question about a processed video.
        
        Args:
            video_id: The YouTube video ID
            question: The question to ask about the video
            
        Returns:
            Dictionary with the answer and metadata
        """
        try:
            # Check if video is processed
            if video_id not in self.vector_stores:
                raise Exception(f"Video {video_id} not processed. Process it first with process_video().")

            print(f"Question about {video_id}: {question[:50]}...")

            # Get the RAG chain
            rag_chain = self.vector_stores[video_id]

            # Ask the question
            result = rag_chain.invoke({"input": question})

            # Extract the answer and source documents
            answer = result["answer"]
            source_docs = result.get("context", [])

            print(f"Generated answer using {len(source_docs)} relevant sections")

            return {
                "question": question,
                "answer": answer,
                "sources_used": len(source_docs),
                "method": "RAG (Retrieval-Augmented Generation)"
            }

        except Exception as e:
            print(f"Error answering question: {str(e)}")
            raise

    async def summarize_video(self, video_id: str) -> Dict[str, Any]:
        """
        Generate a summary of the entire video.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            Dictionary with the summary
        """
        try:
            # Make sure video is processed
            if video_id not in self.vector_stores:
                await self.process_video(f"https://www.youtube.com/watch?v={video_id}")

            # Ask for a summary
            summary_question = """Create a clear, well-organized summary of this video.

Use this format:

## Overview
[2-3 sentences explaining what this video is about]

## Main Topics
- Topic 1: [Explanation]
- Topic 2: [Explanation]
- Topic 3: [Explanation]

## Key Takeaways
1. [Important point 1]
2. [Important point 2]
3. [Important point 3]

## Important Details
[Any other important information from the video]"""

            result = await self.ask_question(video_id, summary_question)
            return {
                "video_id": video_id,
                "summary": result["answer"],
                "method": "AI Summary"
            }

        except Exception as e:
            print(f"Error creating summary: {str(e)}")
            raise

    async def _get_transcript(self, video_id: str) -> Dict[str, str]:
        """
        Get the transcript from a YouTube video with multiple fallback strategies.
        
        Tries:
        1. English manual transcripts
        2. Auto-generated English transcripts
        3. Any available transcript (auto-translate)
        4. Fallback to video description/metadata
        
        Returns:
            Dictionary with "text", "title", and "language"
        """
        try:
            print(f"   Attempt 1: Fetching transcript from YouTube...")
            
            try:
                # Get available transcripts
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Strategy 1: Try to get English manual transcripts
                print(f"      Trying manual English transcript...")
                try:
                    transcript = transcript_list.find_transcript(['en', 'en-US'])
                    transcript_data = transcript.fetch()
                    full_text = " ".join([entry['text'] for entry in transcript_data])
                    print(f"      Success! Got {len(full_text)} chars from manual transcript")
                    
                    return {
                        "text": full_text,
                        "title": f"Video {video_id}",
                        "language": "English (manual)"
                    }
                except:
                    print(f"      Manual transcript not found")
                
                # Strategy 2: Try auto-generated English transcripts
                print(f"      Trying auto-generated English transcript...")
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    transcript_data = transcript.fetch()
                    full_text = " ".join([entry['text'] for entry in transcript_data])
                    print(f"      Success! Got {len(full_text)} chars from auto-generated")
                    
                    return {
                        "text": full_text,
                        "title": f"Video {video_id}",
                        "language": "English (auto-generated)"
                    }
                except:
                    print(f"      Auto-generated English not found")
                
                # Strategy 3: Get any available transcript
                print(f"      Trying any available transcript with translation...")
                available_langs = [t.language_code for t in transcript_list]
                print(f"      Available languages: {available_langs[:3]}...")
                
                if available_langs:
                    transcript_data = transcript_list.get_transcript(available_langs[0])
                    full_text = " ".join([entry['text'] for entry in transcript_data])
                    print(f"      Success! Got {len(full_text)} chars from {available_langs[0]}")
                    
                    return {
                        "text": full_text,
                        "title": f"Video {video_id}",
                        "language": f"{available_langs[0]} (auto-translated)"
                    }
                
                # No transcripts available
                print(f"      No transcripts available for this video")
                raise Exception("Video has no transcripts available")
                
            except Exception as transcript_error:
                print(f"      Transcript extraction failed: {str(transcript_error)}")
                raise transcript_error
        
        except Exception as e:
            error_msg = str(e)
            print(f"   Could not get transcript: {error_msg}")
            
            # Provide helpful error messages
            if "unavailable" in error_msg.lower():
                raise Exception(f"Video {video_id} is unavailable (private, deleted, or age-restricted). Try another video.")
            elif "transcript" in error_msg.lower() and "not" in error_msg.lower():
                raise Exception(f"Video {video_id} has no available transcripts. Videos must have captions (manual or auto-generated) enabled.")
            elif "quota" in error_msg.lower():
                raise Exception("YouTube API quota exceeded. Try again later.")
            else:
                raise Exception(f"Failed to extract transcript: {error_msg}. Try a different video with subtitles enabled.")

    def cleanup_video(self, video_id: str):
        """Clean up resources for a specific video."""
        try:
            if video_id in self.temp_directories:
                temp_dir = self.temp_directories[video_id]
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            # Remove from memory
            if video_id in self.processed_videos:
                del self.processed_videos[video_id]
            if video_id in self.vector_stores:
                del self.vector_stores[video_id]
            if video_id in self.temp_directories:
                del self.temp_directories[video_id]

            print(f"Cleaned up video {video_id}")
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

    def __del__(self):
        """Clean up all resources when the service is destroyed."""
        try:
            for video_id in list(self.temp_directories.keys()):
                self.cleanup_video(video_id)
        except:
            pass


def get_youtube_service() -> YouTubeRAGService:
    """
    Get an instance of the YouTube RAG service.
    
    Usage:
        service = get_youtube_service()
        await service.process_video("https://youtube.com/watch?v=VIDEO_ID")
        result = await service.ask_question(video_id, "What is this about?")
    """
    return YouTubeRAGService()
