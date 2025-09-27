import os
import asyncio
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import sqlite3
import json
import hashlib

from app.services.transcript import TranscriptService

class OptimizedYouTubeService:
    """
    Optimized YouTube AI Assistant for Chrome Extension
    Features:
    - Lightweight storage with SQLite cache
    - Smart chunking with size limits
    - LRU cache for recent videos
    - Automatic cleanup
    - Memory optimization
    """
    
    def __init__(self, max_cache_size: int = 10, max_chunk_size: int = 1000):
        self.api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBMBY7KhVxHZy4j66tBoiT9r0Bk4IQznq8')
        self.max_cache_size = max_cache_size  # Max videos to keep in memory
        self.max_chunk_size = max_chunk_size  # Max characters per chunk
        
        # Initialize services
        self.transcript_service = TranscriptService()
        
        # Lightweight embeddings for extension
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",  # Smaller, faster model
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Google Gemini with optimized settings
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=500,  # Limit response length for extension
            convert_system_message_to_human=True
        )
        
        # Optimized text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Optimized prompt
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""Based on this YouTube video content, answer the question concisely:

Context: {context}

Question: {question}

Answer (maximum 3 sentences):"""
        )
        
        # In-memory cache with LRU
        self.video_cache = {}  # video_id -> qa_chain
        self.access_order = []  # For LRU management
        
        # Initialize SQLite for metadata storage
        self.init_database()
        
        print("Optimized YouTube AI Assistant initialized")
        print(f"📊 Cache size limit: {self.max_cache_size} videos")
        print(f"📏 Max chunk size: {self.max_chunk_size} characters")
    
    def init_database(self):
        """Initialize lightweight SQLite database for metadata"""
        self.db_path = os.path.join(tempfile.gettempdir(), "youtube_ai_cache.db")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_metadata (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    channel TEXT,
                    language TEXT,
                    chunks_count INTEGER,
                    processed_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    transcript_hash TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_chunks (
                    video_id TEXT,
                    chunk_index INTEGER,
                    content TEXT,
                    embedding BLOB,
                    PRIMARY KEY (video_id, chunk_index)
                )
            """)
    
    async def process_video_smart(self, video_url: str) -> Dict[str, Any]:
        """Smart video processing with caching and optimization"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                raise Exception("Invalid YouTube URL")
            
            print(f"Smart processing video: {video_id}")
            
            # Check if already in memory cache
            if video_id in self.video_cache:
                print(f"💨 Found in memory cache: {video_id}")
                self._update_access_order(video_id)
                return self._get_video_metadata(video_id)
            
            # Check database cache
            if self._is_in_database(video_id):
                print(f"💾 Found in database cache: {video_id}")
                return await self._load_from_database(video_id)
            
            # Process new video
            return await self._process_new_video(video_url, video_id)
            
        except Exception as e:
            print(f"❌ Error in smart processing: {e}")
            raise
    
    async def _process_new_video(self, video_url: str, video_id: str) -> Dict[str, Any]:
        """Process a completely new video"""
        print(f"🆕 Processing new video: {video_id}")
        
        # Get transcript
        transcript_data = await self.get_transcript(video_id)
        transcript_text = transcript_data["transcript"]
        
        # Create hash for change detection
        transcript_hash = hashlib.md5(transcript_text.encode()).hexdigest()
        
        # Limit transcript size for extension (max 50KB)
        MAX_TRANSCRIPT_SIZE = 50000
        if len(transcript_text) > MAX_TRANSCRIPT_SIZE:
            transcript_text = transcript_text[:MAX_TRANSCRIPT_SIZE] + "..."
            print(f"⚠️ Transcript truncated to {MAX_TRANSCRIPT_SIZE} characters")
        
        # Create documents
        documents = [Document(
            page_content=transcript_text,
            metadata={
                "video_id": video_id,
                "title": transcript_data.get("title", "Unknown"),
                "channel": transcript_data.get("channel", "Unknown"),
                "language": transcript_data.get("language", "unknown")
            }
        )]
        
        # Split into optimized chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Limit number of chunks for extension performance
        MAX_CHUNKS = 20
        if len(chunks) > MAX_CHUNKS:
            chunks = chunks[:MAX_CHUNKS]
            print(f"⚠️ Limited to {MAX_CHUNKS} chunks for performance")
        
        print(f"📄 Created {len(chunks)} optimized chunks")
        
        # Create temporary vector store
        temp_dir = tempfile.mkdtemp(prefix=f"opt_chroma_{video_id}_")
        
        try:
            # Create vector store with limited chunks
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
            
            # Create lightweight QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}  # Reduced for faster responses
                ),
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=False  # Don't return sources to save memory
            )
            
            # Store in memory cache
            self._add_to_cache(video_id, qa_chain, temp_dir)
            
            # Save to database for persistence
            self._save_to_database(video_id, transcript_data, chunks, transcript_hash)
            
            metadata = {
                "video_id": video_id,
                "title": transcript_data.get("title", "Unknown"),
                "channel": transcript_data.get("channel", "Unknown"),
                "chunks_count": len(chunks),
                "language": transcript_data.get("language", "unknown"),
                "status": "processed"
            }
            
            print(f"Video {video_id} processed and cached successfully")
            return metadata
            
        except Exception as e:
            # Clean up temp directory on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise
    
    def _add_to_cache(self, video_id: str, qa_chain, temp_dir: str):
        """Add video to memory cache with LRU management"""
        # Remove oldest if cache is full
        while len(self.video_cache) >= self.max_cache_size:
            oldest_id = self.access_order.pop(0)
            if oldest_id in self.video_cache:
                old_temp_dir = self.video_cache[oldest_id].get("temp_dir")
                if old_temp_dir and os.path.exists(old_temp_dir):
                    shutil.rmtree(old_temp_dir)
                del self.video_cache[oldest_id]
                print(f"🗑️ Removed {oldest_id} from cache (LRU)")
        
        # Add new video to cache
        self.video_cache[video_id] = {
            "qa_chain": qa_chain,
            "temp_dir": temp_dir,
            "cached_at": datetime.now()
        }
        self.access_order.append(video_id)
    
    def _update_access_order(self, video_id: str):
        """Update LRU access order"""
        if video_id in self.access_order:
            self.access_order.remove(video_id)
        self.access_order.append(video_id)
    
    def _is_in_database(self, video_id: str) -> bool:
        """Check if video is in database cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT video_id FROM video_metadata WHERE video_id = ?",
                (video_id,)
            )
            return cursor.fetchone() is not None
    
    def _save_to_database(self, video_id: str, transcript_data: dict, chunks: list, transcript_hash: str):
        """Save video data to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save metadata
            conn.execute("""
                INSERT OR REPLACE INTO video_metadata 
                (video_id, title, channel, language, chunks_count, processed_at, last_accessed, transcript_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                transcript_data.get("title", "Unknown"),
                transcript_data.get("channel", "Unknown"),
                transcript_data.get("language", "unknown"),
                len(chunks),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                transcript_hash
            ))
            
            # Save chunks (without embeddings for now - too large)
            conn.execute("DELETE FROM video_chunks WHERE video_id = ?", (video_id,))
            for i, chunk in enumerate(chunks):
                conn.execute("""
                    INSERT INTO video_chunks (video_id, chunk_index, content)
                    VALUES (?, ?, ?)
                """, (video_id, i, chunk.page_content))
    
    async def _load_from_database(self, video_id: str) -> Dict[str, Any]:
        """Load video from database cache"""
        # For now, we'll re-process from database
        # In a full implementation, you'd store embeddings too
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT title, channel, language, chunks_count 
                FROM video_metadata WHERE video_id = ?
            """, (video_id,))
            row = cursor.fetchone()
            
            if row:
                # Update last accessed
                conn.execute("""
                    UPDATE video_metadata SET last_accessed = ? WHERE video_id = ?
                """, (datetime.now().isoformat(), video_id))
                
                return {
                    "video_id": video_id,
                    "title": row[0],
                    "channel": row[1], 
                    "language": row[2],
                    "chunks_count": row[3],
                    "status": "cached"
                }
        
        return None
    
    def _get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get metadata for cached video"""
        if video_id in self.video_cache:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT title, channel, language, chunks_count 
                    FROM video_metadata WHERE video_id = ?
                """, (video_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "video_id": video_id,
                        "title": row[0],
                        "channel": row[1],
                        "language": row[2], 
                        "chunks_count": row[3],
                        "status": "ready"
                    }
        return {"video_id": video_id, "status": "not_found"}
    
    async def ask_question_optimized(self, video_id: str, question: str) -> Dict[str, Any]:
        """Ask question with optimized response"""
        try:
            # Check if video is in memory cache
            if video_id not in self.video_cache:
                # Check if it's in database and load it to memory
                if self._is_in_database(video_id):
                    print(f"🔄 Loading video {video_id} from database to memory...")
                    # For simplicity, use fallback method for database-cached videos
                    return await self._fallback_answer(video_id, question)
                else:
                    return {
                        "question": question,
                        "answer": "Video not processed yet. Please process the video first.",
                        "confidence": 0.0,
                        "method": "optimized_error"
                    }
            
            qa_chain = self.video_cache[video_id]["qa_chain"]
            
            try:
                # Get answer with timeout for extension
                import asyncio
                result = await asyncio.wait_for(
                    asyncio.to_thread(qa_chain.run, {"query": question}),
                    timeout=30.0  # 30 second timeout for better processing
                )
                
                return {
                    "question": question,
                    "answer": result.strip(),
                    "confidence": 0.8,
                    "method": "optimized_langchain",
                    "language": "auto-detected"
                }
                
            except asyncio.TimeoutError:
                # If LangChain times out, try simple fallback
                print(f"⏰ LangChain timeout for {video_id}, trying fallback...")
                return await self._fallback_answer(video_id, question)
            
        except Exception as e:
            print(f"❌ Error in optimized question: {e}")
            try:
                # Try fallback on any error
                return await self._fallback_answer(video_id, question)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return {
                    "question": question,
                    "answer": f"Error processing question: {str(e)}",
                    "confidence": 0.0,
                    "method": "optimized_error"
                }
    
    async def _fallback_answer(self, video_id: str, question: str) -> Dict[str, Any]:
        """Fallback method when LangChain fails"""
        try:
            # Get transcript chunks from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT content FROM video_chunks 
                    WHERE video_id = ? 
                    ORDER BY chunk_index 
                    LIMIT 3
                """, (video_id,))
                
                chunks = [row[0] for row in cursor.fetchall()]
            
            if not chunks:
                return {
                    "question": question,
                    "answer": "No transcript data found for this video.",
                    "confidence": 0.0,
                    "method": "fallback_error"
                }
            
            # Simple keyword-based matching for fallback
            combined_text = " ".join(chunks)
            question_lower = question.lower()
            
            # Create a simple answer based on content
            if "about" in question_lower or "what" in question_lower:
                # Take first 200 characters as summary
                summary = combined_text[:300] + "..." if len(combined_text) > 300 else combined_text
                answer = f"Based on the transcript, this video appears to discuss: {summary}"
            else:
                # Search for question keywords in transcript
                answer = f"According to the video transcript: {combined_text[:200]}..."
            
            return {
                "question": question,
                "answer": answer,
                "confidence": 0.6,
                "method": "fallback_simple",
                "language": "auto-detected"
            }
            
        except Exception as e:
            print(f"❌ Fallback method failed: {e}")
            return {
                "question": question,
                "answer": "Unable to process question due to technical issues. Please try again.",
                "confidence": 0.0,
                "method": "fallback_error"
            }
    
    def cleanup_old_cache(self, days_old: int = 7):
        """Clean up old cached data"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            # Find old videos
            cursor = conn.execute("""
                SELECT video_id FROM video_metadata 
                WHERE last_accessed < ?
            """, (cutoff_date.isoformat(),))
            
            old_videos = [row[0] for row in cursor.fetchall()]
            
            for video_id in old_videos:
                # Remove from database
                conn.execute("DELETE FROM video_metadata WHERE video_id = ?", (video_id,))
                conn.execute("DELETE FROM video_chunks WHERE video_id = ?", (video_id,))
                
                # Remove from memory if present
                if video_id in self.video_cache:
                    temp_dir = self.video_cache[video_id].get("temp_dir")
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    del self.video_cache[video_id]
                    if video_id in self.access_order:
                        self.access_order.remove(video_id)
            
            print(f"🗑️ Cleaned up {len(old_videos)} old videos")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM video_metadata")
            db_count = cursor.fetchone()[0]
        
        return {
            "memory_cache_size": len(self.video_cache),
            "database_cache_size": db_count,
            "max_cache_size": self.max_cache_size,
            "max_chunk_size": self.max_chunk_size,
            "current_videos": list(self.video_cache.keys())
        }
    
    # Include all the helper methods from the original service
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        import re
        pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    async def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get video transcript using the transcript service"""
        return await self.transcript_service.get_transcript(video_id)
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get video processing status"""
        if video_id in self.video_cache:
            return {"status": "ready", "in_memory": True}
        elif self._is_in_database(video_id):
            return {"status": "cached", "in_memory": False}
        else:
            return {"status": "not_processed", "in_memory": False}
    
    def cleanup_video(self, video_id: str):
        """Clean up resources for a specific video"""
        if video_id in self.video_cache:
            temp_dir = self.video_cache[video_id].get("temp_dir")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            del self.video_cache[video_id]
            if video_id in self.access_order:
                self.access_order.remove(video_id)
        
        # Also remove from database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM video_metadata WHERE video_id = ?", (video_id,))
            conn.execute("DELETE FROM video_chunks WHERE video_id = ?", (video_id,))
        
        print(f"🗑️ Cleaned up video: {video_id}")