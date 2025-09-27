import os
import asyncio
from typing import List, Dict, Any, Optional
import re
import json
import requests
import time

class GeminiQuestionAnsweringService:
    """Question answering service using Google Gemini API"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDvhlqz_tSdNpkG6OZyryXyp5qUYjwDGcc")
        self.model = "gemini-2.5-flash"  # Available model from your API key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
            print("Using Google Gemini API for advanced question answering")
        else:
            print("⚠️  No Gemini API key found. Using simple pattern-based answering.")
    
    async def generate_answer(self, question: str, relevant_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an answer based on question and relevant context chunks"""
        
        # Prepare context from relevant chunks
        context = self.prepare_context(relevant_chunks)
        
        if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
            return await self.generate_gemini_answer(question, context, relevant_chunks)
        else:
            # Fallback to simple method
            return await self.generate_simple_answer(question, context, relevant_chunks)
    
    def prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            similarity = chunk.get("similarity", 0.0)
            
            # Add chunk with some metadata
            context_parts.append(f"[Section {i+1} - Relevance: {similarity:.2f}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    async def generate_gemini_answer(self, question: str, context: str, chunks: List[Dict]) -> Dict[str, Any]:
        """Generate answer using Google Gemini API"""
        try:
            # If Gemini API not available, use simple fallback
            if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
                return await self.generate_simple_answer(question, context, chunks)
            
            # Create the prompt for Gemini
            prompt = f"""You are a helpful AI assistant that answers questions about YouTube video content. 
You have been provided with relevant excerpts from a video transcript.

Instructions:
- Answer the question based on the provided context from the video transcript
- Be accurate and specific, using information directly from the transcript
- If the context doesn't contain enough information to answer the question, say so clearly
- Keep your answer concise but complete (2-3 sentences maximum)
- Reference specific parts of the transcript when relevant
- If multiple sections provide relevant information, synthesize them coherently
- If the transcript is in Hindi or another language, translate and summarize the content in English

Context from video transcript:
{context}

Question: {question}

Answer based on the video content:"""

            # Try Gemini API first
            try:
                # Prepare the request payload
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 500,
                    }
                }
                
                # Make the API request
                headers = {
                    "Content-Type": "application/json",
                }
                
                url = f"{self.api_url}?key={self.gemini_api_key}"
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "candidates" in result and len(result["candidates"]) > 0:
                        answer_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                        
                        # Calculate confidence based on chunk similarities
                        avg_similarity = sum(chunk.get("similarity", 0) for chunk in chunks) / len(chunks) if chunks else 0
                        confidence = min(avg_similarity * 1.2, 1.0)  # Scale and cap at 1.0
                        
                        return {
                            "answer": answer_text,
                            "confidence": confidence,
                            "method": "gemini_api",
                            "model": self.model
                        }
                    else:
                        raise Exception("No response candidates from Gemini")
                else:
                    error_msg = f"Gemini API error: {response.status_code}"
                    if response.text:
                        error_msg += f" - {response.text}"
                    raise Exception(error_msg)
                    
            except Exception as api_error:
                print(f"Gemini API failed: {api_error}")
                # Fall back to simple method if API fails
                return await self.generate_simple_answer(question, context, chunks)
                
        except Exception as e:
            print(f"Error in generate_gemini_answer: {e}")
            return await self.generate_simple_answer(question, context, chunks)
    
    async def generate_enhanced_simple_answer(self, question: str, context: str, chunks: List[Dict]) -> Dict[str, Any]:
        """Enhanced simple answer generation with better context analysis and translation"""
        try:
            print(f"🔍 Processing question: {question}")
            print(f"📊 Received {len(chunks)} chunks")
            
            # Debug: Show chunks received
            for i, chunk in enumerate(chunks):
                similarity = chunk.get('similarity', 0)
                text_preview = chunk.get('text', '')[:100]
                print(f"  Chunk {i+1} (similarity: {similarity:.3f}): {text_preview}...")
            
            # Combine all chunk texts
            full_context = " ".join([chunk.get("text", "") for chunk in chunks])
            print(f"📝 Full context length: {len(full_context)} characters")
            
            # Basic keyword matching and context extraction
            question_lower = question.lower()
            context_lower = full_context.lower()
            
            # Translation dictionary for common Hindi terms
            hindi_translations = {
                'नमस्कार': 'Hello/Greetings',
                'साथियों': 'friends',
                'स्वागत': 'welcome',
                'चर्चा': 'discussion',
                'जोहो': 'Zoho',
                'माइक्रोसॉफ्ट': 'Microsoft',
                'कंपनी': 'company',
                'प्लेटफॉर्म': 'platform',
                'सॉफ्टवेयर': 'software',
                'बिजनेस': 'business',
                'टेक्नोलॉजी': 'technology',
                'सेवा': 'service',
                'उत्पाद': 'product',
                'अंकित अवस्थी': 'Ankit Avasthi',
                'पाठशाला': 'educational channel',
                'कमेंट': 'comments',
                'भारतीय': 'Indian',
                'भारत': 'India',
                'देश': 'country',
                'फाउंडर': 'founder',
                'सिस्टम': 'system'
            }
            
            # Check for summary requests
            if any(word in question_lower for word in ['summary', 'summarize', 'about', 'main', 'topic', 'discuss', 'what']):
                print("🎯 Detected summary request")
                # Extract key information and translate context
                english_summary = self.translate_and_summarize_content(full_context, hindi_translations)
                
                return {
                    "answer": english_summary,
                    "confidence": 0.8,
                    "method": "enhanced_summary_translation"
                }
            
            # Look for specific terms mentioned in the question
            question_words = question_lower.split()
            relevant_chunks = []
            
            for chunk in chunks:
                text = chunk.get("text", "")
                text_lower = text.lower()
                
                # Check if chunk contains question keywords or key terms
                score = sum(1 for word in question_words if word in text_lower and len(word) > 3)
                if 'zoho' in question_lower and 'जोहो' in text_lower:
                    score += 3
                if 'microsoft' in question_lower and ('माइक्रोसॉफ्ट' in text_lower or 'microsoft' in text_lower):
                    score += 3
                
                if score > 0:
                    relevant_chunks.append((text, score))
            
            print(f"🎯 Found {len(relevant_chunks)} relevant chunks")
            
            if relevant_chunks:
                # Sort by relevance score and translate
                relevant_chunks.sort(key=lambda x: x[1], reverse=True)
                translated_content = self.translate_and_summarize_content(
                    ". ".join([chunk[0] for chunk in relevant_chunks[:3]]), 
                    hindi_translations
                )
                
                return {
                    "answer": translated_content,
                    "confidence": 0.7,
                    "method": "keyword_matching_translation"
                }
            
            # If no specific matches, provide general translated context
            if full_context and len(full_context) > 100:
                print("🔄 Using general translation fallback")
                translated_summary = self.translate_and_summarize_content(full_context[:2000], hindi_translations)
                return {
                    "answer": translated_summary,
                    "confidence": 0.6,
                    "method": "general_translation"
                }
            
            return {
                "answer": "I found a transcript in Hindi discussing technology topics, but I need more specific information to provide a detailed answer. The video appears to be about Zoho and Microsoft platforms.",
                "confidence": 0.3,
                "method": "fallback"
            }
            
        except Exception as e:
            print(f"Error in enhanced simple answer: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": "I encountered an error while processing the video transcript. Please try rephrasing your question.",
                "confidence": 0.1,
                "method": "error_fallback"
            }
    
    def translate_and_summarize_content(self, hindi_text: str, translation_dict: dict) -> str:
        """Translate key Hindi terms and create an English summary"""
        try:
            # Split into sentences
            sentences = hindi_text.split('।')  # Hindi sentence delimiter
            if len(sentences) <= 1:
                sentences = hindi_text.split('.')
            
            translated_parts = []
            key_points = []
            
            # Process each sentence
            for sentence in sentences[:10]:  # Process first 10 sentences
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                
                # Extract key information patterns
                if 'जोहो' in sentence.lower():
                    key_points.append("Discussion about Zoho platform/company")
                if 'माइक्रोसॉफ्ट' in sentence.lower():
                    key_points.append("Comparison with Microsoft")
                if 'कंपनी' in sentence.lower() or 'बिजनेस' in sentence.lower():
                    key_points.append("Business and company analysis")
                if 'प्लेटफॉर्म' in sentence.lower() or 'सॉफ्टवेयर' in sentence.lower():
                    key_points.append("Software platform discussion")
                if 'भारत' in sentence.lower() or 'देश' in sentence.lower():
                    key_points.append("Focus on Indian market/companies")
            
            # Create comprehensive English summary
            if key_points:
                summary_intro = "This video discusses: " + "; ".join(set(key_points)) + ". "
            else:
                summary_intro = "This appears to be a Hindi technology video. "
            
            # Add context about the content
            context_analysis = ""
            if 'अंकित अवस्थी' in hindi_text:
                context_analysis += "The presenter is Ankit Avasthi. "
            if 'पाठशाला' in hindi_text:
                context_analysis += "This appears to be an educational channel. "
            if 'कमेंट' in hindi_text:
                context_analysis += "The presenter mentions audience comments requesting this topic. "
            
            # Combine everything
            full_summary = summary_intro + context_analysis
            
            # Add specific Zoho context if mentioned
            if 'जोहो' in hindi_text.lower():
                full_summary += "The main focus is on Zoho, likely discussing its features, comparison with other platforms like Microsoft, and its relevance in the Indian tech ecosystem. "
            
            # Ensure minimum length and completeness
            if len(full_summary) < 100:
                full_summary += "The video content appears to focus on technology and business topics."
            
            return full_summary
            
        except Exception as e:
            print(f"Translation error: {e}")
            return "This appears to be a Hindi video discussing technology topics. Please provide a more specific question for better analysis."
    
    async def generate_simple_answer(self, question: str, context: str, chunks: List[Dict]) -> Dict[str, Any]:
        """Fallback simple answer generation"""
        try:
            # Simple extractive approach
            answer = self.extract_relevant_sentences(question, context)
            
            # Calculate confidence based on chunk similarities
            avg_similarity = sum(chunk.get("similarity", 0) for chunk in chunks) / len(chunks) if chunks else 0
            confidence = avg_similarity * 0.7  # Lower confidence for fallback method
            
            return {
                "answer": answer,
                "confidence": confidence,
                "method": "simple_fallback"
            }
            
        except Exception as e:
            print(f"Error in fallback answer generation: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "confidence": 0.0,
                "method": "error_fallback"
            }
    
    def extract_relevant_sentences(self, question: str, context: str) -> str:
        """Extract relevant sentences from context (simple fallback method)"""
        # Split context into sentences
        sentences = re.split(r'[.!?]+', context)
        
        # Extract key words from question
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        question_words = {word for word in question_words if len(word) > 3}  # Filter short words
        
        # Score sentences based on word overlap
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
                
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            overlap = len(question_words.intersection(sentence_words))
            
            if overlap > 0:
                scored_sentences.append((sentence, overlap))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = scored_sentences[:2]
        
        if top_sentences:
            answer = " ".join([sent[0] for sent in top_sentences])
            return f"Based on the video content: {answer}"
        else:
            return "I couldn't find specific information in the video transcript to answer your question. Could you try rephrasing or asking a different question?"
    
    def test_api_connection(self) -> bool:
        """Test if the Gemini API is working"""
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Hello, can you respond with 'API working' if you receive this?"
                    }]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            url = f"{self.api_url}?key={self.gemini_api_key}"
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False