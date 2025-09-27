import os
import asyncio
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
import tempfile
import shutil

class LangChainYouTubeService:
    """YouTube AI Assistant using LangChain framework"""
    
    def __init__(self):
        # Initialize components
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDvhlqz_tSdNpkG6OZyryXyp5qUYjwDGcc")
        
        # Initialize embeddings with multilingual support
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "।", ".", "!", "?", ",", " ", ""]
        )
        
        # Initialize Gemini LLM (using available model from your API key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.gemini_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        # Custom prompt template for multilingual content
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful AI assistant that answers questions about YouTube video content.
You have been provided with relevant excerpts from a video transcript that may be in Hindi or other languages.

Instructions:
- Answer the question in English based on the provided context
- If the transcript is in Hindi or another language, translate and explain the content in English
- Be accurate and specific, using information directly from the transcript
- If the context doesn't contain enough information, say so clearly
- Provide complete, detailed answers (not just fragments)
- For summary requests, provide comprehensive overviews of the main topics

Context from video transcript:
{context}

Question: {question}

Detailed English Answer:"""
        )
        
        # Store for processed videos
        self.processed_videos = {}
        
        print("LangChain YouTube AI Assistant initialized")
    
    async def process_video(self, video_url: str) -> Dict[str, Any]:
        """Process a YouTube video using LangChain"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                raise Exception("Invalid YouTube URL")
            
            # Check if already processed
            if video_id in self.processed_videos:
                cached_data = self.processed_videos[video_id]
                return {
                    "video_id": video_id,
                    "title": cached_data["metadata"]["title"],
                    "channel": cached_data["metadata"]["channel"],
                    "chunks_count": cached_data["metadata"]["chunks_count"],
                    "language": cached_data["metadata"]["language"],
                    "status": "already_processed"
                }
            
            print(f"Processing video: {video_id}")
            
            # Get transcript using youtube-transcript-api
            transcript_data = await self.get_transcript(video_id)
            
            # Create documents from transcript
            documents = [Document(
                page_content=transcript_data["transcript"],
                metadata={
                    "video_id": video_id,
                    "title": transcript_data.get("title", "Unknown"),
                    "channel": transcript_data.get("channel", "Unknown"),
                    "language": transcript_data.get("language", "unknown")
                }
            )]
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            print(f"📄 Created {len(chunks)} chunks")
            
            # Create temporary directory for this video's vector store
            temp_dir = tempfile.mkdtemp(prefix=f"chroma_{video_id}_")
            
            # Create vector store
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
            
            # Create retrieval chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                ),
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            
            # Store processed video info
            self.processed_videos[video_id] = {
                "qa_chain": qa_chain,
                "vectorstore": vectorstore,
                "temp_dir": temp_dir,
                "metadata": {
                    "video_id": video_id,
                    "title": transcript_data.get("title", "Unknown"),
                    "channel": transcript_data.get("channel", "Unknown"),
                    "chunks_count": len(chunks),
                    "language": transcript_data.get("language", "unknown")
                }
            }
            
            print(f"Video {video_id} processed successfully")
            
            return {
                "video_id": video_id,
                "title": transcript_data.get("title", "Unknown"),
                "channel": transcript_data.get("channel", "Unknown"),
                "chunks_count": len(chunks),
                "language": transcript_data.get("language", "unknown"),
                "status": "processed"
            }
            
        except Exception as e:
            print(f"❌ Error processing video: {e}")
            raise e
    
    async def ask_question(self, video_id: str, question: str) -> Dict[str, Any]:
        """Ask a question about a processed video using LangChain"""
        try:
            if video_id not in self.processed_videos:
                raise Exception("Video not processed. Please process the video first.")
            
            video_data = self.processed_videos[video_id]
            qa_chain = video_data["qa_chain"]
            
            print(f"🤔 Answering question: {question}")
            
            # Use LangChain to get answer (using invoke instead of deprecated __call__)
            result = qa_chain.invoke({"query": question})
            
            answer = result["result"]
            source_docs = result.get("source_documents", [])
            
            # Calculate confidence based on source relevance
            confidence = min(len(source_docs) * 0.2, 1.0) if source_docs else 0.3
            
            print(f"Generated answer with {len(source_docs)} source documents")
            
            return {
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "sources": [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata} for doc in source_docs],
                "method": "langchain_qa",
                "language": video_data["metadata"]["language"]
            }
            
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            raise e
    
    async def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get transcript for a YouTube video"""
        try:
            api = YouTubeTranscriptApi()
            
            # Try to get English transcript first
            try:
                transcript = api.fetch(video_id, languages=['en'])
                transcript_list = transcript.snippets
                language = "en"
            except Exception:
                # Get available transcripts and use the first one
                transcript_list_obj = api.list(video_id)
                available_transcripts = list(transcript_list_obj)
                
                if not available_transcripts:
                    raise Exception("No transcripts available for this video")
                
                # Prefer manually created over auto-generated
                available_transcripts.sort(key=lambda t: (t.is_generated, t.language_code))
                selected_transcript = available_transcripts[0]
                
                transcript = selected_transcript.fetch()
                transcript_list = transcript.snippets
                language = selected_transcript.language_code
            
            # Combine transcript chunks
            full_transcript = " ".join([item.text for item in transcript_list])
            
            # Get basic metadata (you could enhance this with YouTube API)
            return {
                "video_id": video_id,
                "transcript": full_transcript,
                "title": f"YouTube Video {video_id}",
                "channel": "Unknown Channel",
                "language": language
            }
            
        except Exception as e:
            raise Exception(f"Could not get transcript: {e}")
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def cleanup_video(self, video_id: str):
        """Clean up resources for a processed video"""
        if video_id in self.processed_videos:
            video_data = self.processed_videos[video_id]
            temp_dir = video_data.get("temp_dir")
            
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            del self.processed_videos[video_id]
            print(f"🧹 Cleaned up resources for video {video_id}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get status of a processed video"""
        if video_id not in self.processed_videos:
            return {"status": "not_found"}
        
        return {
            "status": "processed",
            **self.processed_videos[video_id]["metadata"]
        }