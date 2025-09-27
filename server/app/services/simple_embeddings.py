import os
import asyncio
from typing import List, Dict, Any, Optional
import json
import hashlib

class EmbeddingService:
    """Embedding service using sentence-transformers for multilingual support"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_simple_embeddings = True
        self.sentence_transformer_model = None
        
        # Try to use sentence-transformers for better multilingual embeddings
        try:
            from sentence_transformers import SentenceTransformer
            # Use a multilingual model that supports Hindi and other languages
            self.sentence_transformer_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            self.use_simple_embeddings = False
            print("✅ Using sentence-transformers for multilingual embeddings")
        except ImportError:
            print("⚠️  sentence-transformers not available, using simple text-based embeddings")
            print("Using simple text-based embeddings (install sentence-transformers for better results)")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers or fallback to simple method"""
        if not self.use_simple_embeddings and self.sentence_transformer_model:
            # Use sentence-transformers for better multilingual support
            try:
                embeddings = self.sentence_transformer_model.encode(texts)
                # Convert numpy arrays to lists if needed
                if hasattr(embeddings, 'tolist'):
                    embeddings = embeddings.tolist()
                elif isinstance(embeddings, list) and len(embeddings) > 0 and hasattr(embeddings[0], 'tolist'):
                    embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
                return embeddings
            except Exception as e:
                print(f"Error with sentence-transformers: {e}, falling back to simple embeddings")
                self.use_simple_embeddings = True
        
        # Fallback to simple embeddings
        embeddings = []
        for text in texts:
            embedding = self.create_simple_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def find_most_similar(self, query_embedding: List[float], embeddings: List[List[float]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings using cosine similarity"""
        if not query_embedding or not embeddings:
            return []
        
        similarities = []
        for i, emb in enumerate(embeddings):
            similarity = self.cosine_similarity(query_embedding, emb)
            similarities.append({"index": i, "similarity": similarity})
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(vec1) != len(vec2) or not vec1 or not vec2:
                return 0.0
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(a * a for a in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def create_simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Create a simple embedding based on text characteristics"""
        # Convert text to lowercase and split into words
        words = text.lower().split()
        
        # Create features based on text characteristics
        features = []
        
        # Length features
        features.append(len(text) / 1000.0)  # Normalized text length
        features.append(len(words) / 100.0)  # Normalized word count
        features.append(sum(len(word) for word in words) / len(words) if words else 0)  # Avg word length
        
        # Character frequency features
        char_counts = {}
        for char in text.lower():
            if char.isalpha():
                char_counts[char] = char_counts.get(char, 0) + 1
        
        # Add character frequency features (for a-z)
        total_chars = sum(char_counts.values())
        for i in range(26):
            char = chr(ord('a') + i)
            freq = char_counts.get(char, 0) / total_chars if total_chars > 0 else 0
            features.append(freq)
        
        # Word pattern features
        features.append(sum(1 for word in words if word.isupper()) / len(words) if words else 0)
        features.append(sum(1 for word in words if word.isdigit()) / len(words) if words else 0)
        features.append(sum(1 for word in words if len(word) > 7) / len(words) if words else 0)
        
        # Question/answer indicators
        features.append(1.0 if '?' in text else 0.0)
        features.append(1.0 if any(word in text.lower() for word in ['what', 'how', 'why', 'when', 'where']) else 0.0)
        
        # Pad or truncate to desired dimension
        while len(features) < dim:
            features.append(0.0)
        
        return features[:dim]
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.create_simple_embedding(text)
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Simple dot product similarity (since we don't have numpy)
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            
            # Calculate magnitudes
            mag1 = sum(a * a for a in embedding1) ** 0.5
            mag2 = sum(b * b for b in embedding2) ** 0.5
            
            if mag1 == 0 or mag2 == 0:
                return 0.0
            
            return dot_product / (mag1 * mag2)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], embeddings: List[List[float]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query"""
        similarities = []
        
        for i, embedding in enumerate(embeddings):
            similarity = self.cosine_similarity(query_embedding, embedding)
            similarities.append({
                "index": i,
                "similarity": similarity
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:top_k]
    
    async def batch_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.generate_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings