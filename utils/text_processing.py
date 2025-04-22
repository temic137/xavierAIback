"""
Text processing utilities for chatbot knowledge base.
Provides functions for chunking, cleaning, and preprocessing text.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Ensure NLTK resources are downloaded
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logging.warning(f"Failed to download NLTK punkt: {str(e)}")

class TextProcessor:
    """Text processing utilities for chatbot knowledge base."""
    
    def __init__(self, 
                 chunk_size: int = 500, 
                 chunk_overlap: int = 100,
                 min_chunk_size: int = 50):
        """Initialize the text processor.
        
        Args:
            chunk_size: Target size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
            min_chunk_size: Minimum size of a chunk to be included
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that don't add meaning
        text = re.sub(r'[^\w\s.,;:!?\'"\-()]', ' ', text)
        
        # Normalize whitespace again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata.
        
        Args:
            text: Input text
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of dictionaries with 'content' and 'metadata'
        """
        if not text:
            return []
        
        # Clean the text
        text = self.clean_text(text)
        
        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Split text into sentences
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            logging.error(f"Error tokenizing text: {str(e)}")
            # Fallback to simple splitting by periods
            sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        
        # Create chunks by combining sentences
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size and we already have content,
            # save the current chunk and start a new one
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": metadata.copy()
                    })
                
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-min(len(words), self.chunk_overlap // 5):]
                current_chunk = " ".join(overlap_words) + " "
            
            # Add the sentence to the current chunk
            current_chunk += sentence + " "
        
        # Add the last chunk if it's not empty
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": metadata.copy()
            })
        
        return chunks
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of documents into chunks with metadata.
        
        Args:
            documents: List of dictionaries with 'text' and optional metadata
            
        Returns:
            List of dictionaries with 'content' and 'metadata'
        """
        all_chunks = []
        
        for doc in documents:
            if not isinstance(doc, dict) or 'text' not in doc:
                continue
            
            text = doc.get('text', '')
            if not text:
                continue
            
            # Extract metadata from document
            metadata = {k: v for k, v in doc.items() if k != 'text'}
            
            # Chunk the document
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        # Simple keyword extraction based on word frequency
        try:
            # Tokenize and lowercase
            words = word_tokenize(text.lower())
            
            # Remove stopwords (simple list)
            stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
                        'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between',
                        'into', 'through', 'during', 'before', 'after', 'above', 'below',
                        'to', 'of', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been',
                        'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
                        'doing', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                        'it', 'we', 'they', 'their', 'your', 'my', 'his', 'her', 'its',
                        'our', 'can', 'will', 'just', 'should', 'now'}
            
            filtered_words = [word for word in words if word.isalnum() and word not in stopwords]
            
            # Count word frequencies
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Return top keywords
            return [word for word, freq in sorted_words[:max_keywords]]
        
        except Exception as e:
            logging.error(f"Error extracting keywords: {str(e)}")
            return []

# Create a singleton instance
text_processor = TextProcessor()
