from typing import List, Dict, Any
import re

class ChunkingService:
    """Service for chunking text content into manageable pieces"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """Chunk transcript into smaller pieces with overlap"""
        # Clean the transcript first
        clean_transcript = self.clean_text(transcript)
        
        # Split into sentences first
        sentences = self.split_into_sentences(clean_transcript)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append({
                    "id": chunk_id,
                    "text": current_chunk.strip(),
                    "length": current_length,
                    "start_char": len("".join([c["text"] for c in chunks])),
                })
                
                # Start new chunk with overlap
                overlap_text = self.get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
                chunk_id += 1
            else:
                # Add sentence to current chunk
                current_chunk += " " + sentence if current_chunk else sentence
                current_length = len(current_chunk)
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunks.append({
                "id": chunk_id,
                "text": current_chunk.strip(),
                "length": current_length,
                "start_char": len("".join([c["text"] for c in chunks])),
            })
        
        return chunks
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting using regex
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter out very short fragments
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    def get_overlap_text(self, text: str, overlap_length: int) -> str:
        """Get the last part of text for overlap"""
        if len(text) <= overlap_length:
            return text
        
        # Try to find a good breaking point (end of sentence)
        overlap_text = text[-overlap_length:]
        
        # Look for sentence ending in the overlap
        sentence_end = overlap_text.rfind('.')
        if sentence_end != -1 and sentence_end > overlap_length // 2:
            return overlap_text[sentence_end + 1:].strip()
        
        # If no good sentence break, just use the last part
        return overlap_text
    
    def clean_text(self, text: str) -> str:
        """Clean text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common transcript artifacts
        text = re.sub(r'\[.*?\]', '', text)  # [Music], [Applause], etc.
        text = re.sub(r'\(.*?\)', '', text)  # (inaudible), etc.
        
        # Fix common OCR/transcription errors
        text = re.sub(r'\b(\w)\1{2,}\b', r'\1', text)  # Remove repeated characters
        
        return text.strip()
    
    def chunk_by_time(self, transcript_chunks: List[Dict], time_window: float = 60.0) -> List[Dict[str, Any]]:
        """Chunk transcript by time windows"""
        if not transcript_chunks:
            return []
        
        chunks = []
        current_chunk = {
            "id": 0,
            "text": "",
            "start_time": transcript_chunks[0].get("start", 0),
            "end_time": 0,
            "duration": 0
        }
        
        for item in transcript_chunks:
            start_time = item.get("start", 0)
            text = item.get("text", "")
            duration = item.get("duration", 3.0)
            
            # If this item would exceed time window, finalize current chunk
            if start_time - current_chunk["start_time"] > time_window and current_chunk["text"]:
                current_chunk["duration"] = current_chunk["end_time"] - current_chunk["start_time"]
                chunks.append(current_chunk)
                
                # Start new chunk
                current_chunk = {
                    "id": len(chunks),
                    "text": text,
                    "start_time": start_time,
                    "end_time": start_time + duration,
                    "duration": 0
                }
            else:
                # Add to current chunk
                if current_chunk["text"]:
                    current_chunk["text"] += " " + text
                else:
                    current_chunk["text"] = text
                current_chunk["end_time"] = start_time + duration
        
        # Add final chunk
        if current_chunk["text"]:
            current_chunk["duration"] = current_chunk["end_time"] - current_chunk["start_time"]
            chunks.append(current_chunk)
        
        return chunks
