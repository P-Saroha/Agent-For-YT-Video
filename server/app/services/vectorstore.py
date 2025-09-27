import os
import json
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.services.simple_embeddings import EmbeddingService

class VectorStoreService:
    """Service for storing and retrieving vector embeddings"""
    
    def __init__(self):
        self.store_path = Path(os.getenv("VECTOR_STORE_PATH", "store/faiss"))
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.embedding_service = EmbeddingService()
        
        # In-memory storage for development (replace with proper vector DB in production)
        self.video_stores: Dict[str, Dict] = {}
    
    async def store_video_chunks(self, video_id: str, chunks: List[Dict], embeddings: List[List[float]]):
        """Store video chunks and their embeddings"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        # Create video store
        video_store = {
            "video_id": video_id,
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": {
                "total_chunks": len(chunks),
                "embedding_dim": len(embeddings[0]) if embeddings else 0
            }
        }
        
        # Store in memory
        self.video_stores[video_id] = video_store
        
        # Also save to disk for persistence
        await self.save_video_store_to_disk(video_id, video_store)
        
        print(f"Stored {len(chunks)} chunks for video {video_id}")
    
    async def search_similar_chunks(self, video_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks to a query"""
        # Load video store if not in memory
        if video_id not in self.video_stores:
            await self.load_video_store_from_disk(video_id)
        
        if video_id not in self.video_stores:
            raise ValueError(f"Video {video_id} not found in vector store")
        
        video_store = self.video_stores[video_id]
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_single_embedding(query)
        
        # Find similar embeddings
        similar_results = self.embedding_service.find_most_similar(
            query_embedding, 
            video_store["embeddings"], 
            top_k=top_k
        )
        
        # Combine with chunk data
        results = []
        for result in similar_results:
            chunk_index = result["index"]
            chunk = video_store["chunks"][chunk_index].copy()
            chunk["similarity"] = result["similarity"]
            chunk["embedding_index"] = chunk_index
            results.append(chunk)
        
        return results
    
    async def save_video_store_to_disk(self, video_id: str, video_store: Dict):
        """Save video store to disk for persistence"""
        try:
            file_path = self.store_path / f"{video_id}.pkl"
            
            with open(file_path, 'wb') as f:
                pickle.dump(video_store, f)
            
            # Also save metadata as JSON for easier inspection
            metadata_path = self.store_path / f"{video_id}_metadata.json"
            metadata = {
                "video_id": video_id,
                "total_chunks": len(video_store["chunks"]),
                "chunk_preview": [chunk["text"][:100] + "..." for chunk in video_store["chunks"][:3]]
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Error saving video store to disk: {e}")
    
    async def load_video_store_from_disk(self, video_id: str):
        """Load video store from disk"""
        try:
            file_path = self.store_path / f"{video_id}.pkl"
            
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    video_store = pickle.load(f)
                    self.video_stores[video_id] = video_store
                    print(f"Loaded video store for {video_id} from disk")
            
        except Exception as e:
            print(f"Error loading video store from disk: {e}")
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get basic info about a stored video"""
        if video_id in self.video_stores:
            store = self.video_stores[video_id]
            return {
                "video_id": video_id,
                "total_chunks": len(store["chunks"]),
                "embedding_dim": store["metadata"]["embedding_dim"]
            }
        return None
    
    def list_stored_videos(self) -> List[str]:
        """List all stored video IDs"""
        # Check both memory and disk
        memory_videos = set(self.video_stores.keys())
        
        disk_videos = set()
        for file_path in self.store_path.glob("*.pkl"):
            video_id = file_path.stem
            if not video_id.endswith("_metadata"):
                disk_videos.add(video_id)
        
        return list(memory_videos.union(disk_videos))
    
    async def delete_video_store(self, video_id: str):
        """Delete video store from memory and disk"""
        # Remove from memory
        if video_id in self.video_stores:
            del self.video_stores[video_id]
        
        # Remove from disk
        try:
            file_path = self.store_path / f"{video_id}.pkl"
            metadata_path = self.store_path / f"{video_id}_metadata.json"
            
            if file_path.exists():
                file_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
                
            print(f"Deleted video store for {video_id}")
            
        except Exception as e:
            print(f"Error deleting video store: {e}")
    
    def clear_all_stores(self):
        """Clear all video stores (use with caution)"""
        self.video_stores.clear()
        
        # Also clear disk storage
        try:
            for file_path in self.store_path.glob("*.pkl"):
                file_path.unlink()
            for file_path in self.store_path.glob("*_metadata.json"):
                file_path.unlink()
                
            print("Cleared all video stores")
            
        except Exception as e:
            print(f"Error clearing disk storage: {e}")
