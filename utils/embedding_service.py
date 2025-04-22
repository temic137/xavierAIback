"""
Embedding service for generating and managing text embeddings.
Supports multiple embedding providers with fallback options.
"""

import os
import logging
import time
import hashlib
import json
from typing import List, Dict, Any, Optional, Union
import numpy as np
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import embedding providers
OPENAI_AVAILABLE = False
COHERE_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import cohere
    # Try to get API key from environment variable (check both variable names)
    COHERE_API_KEY = os.getenv('COHERE_API_KEY') or os.getenv('COHERE_CLIENT')

    if COHERE_API_KEY:
        cohere_client = cohere.Client(COHERE_API_KEY)
        COHERE_AVAILABLE = True
        print("Cohere client initialized successfully")
    else:
        print("Cohere API key not found in environment variables")
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

class EmbeddingService:
    """Service for generating and managing text embeddings."""

    def __init__(self,
                 provider: str = 'auto',
                 model_name: str = None,
                 embedding_dim: int = 384,
                 cache_size: int = 1000):
        """Initialize the embedding service.

        Args:
            provider: Embedding provider ('openai', 'cohere', 'sentence-transformers', or 'auto')
            model_name: Specific model name for the provider
            embedding_dim: Dimension of embeddings (for fallback)
            cache_size: Size of the LRU cache for embeddings
        """
        self.provider = provider
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.cache_size = cache_size

        # Initialize the selected provider
        self._initialize_provider()

        # Create embedding cache
        self.generate_embeddings = lru_cache(maxsize=cache_size)(self._generate_embeddings_uncached)

    def _initialize_provider(self):
        """Initialize the embedding provider based on availability."""
        if self.provider == 'auto':
            # Auto-select provider based on availability
            if OPENAI_AVAILABLE:
                self.provider = 'openai'
                self.model_name = self.model_name or 'text-embedding-3-small'
            elif COHERE_AVAILABLE:
                self.provider = 'cohere'
                self.model_name = self.model_name or 'embed-english-v3.0'
                print("Cohere client initialized1")
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.provider = 'sentence-transformers'
                self.model_name = self.model_name or 'all-MiniLM-L6-v2'
                print("Sentence Transformers client initialized")
            else:
                self.provider = 'fallback'
                logging.warning("No embedding providers available. Using fallback random embeddings.")

        # Initialize the selected provider
        if self.provider == 'openai' and OPENAI_AVAILABLE:
            self.model_name = self.model_name or 'text-embedding-3-small'
            logging.info(f"Using OpenAI embeddings with model {self.model_name}")
        elif self.provider == 'cohere' and COHERE_AVAILABLE:
            self.model_name = self.model_name or 'embed-english-v3.0'
            logging.info(f"Using Cohere embeddings with model {self.model_name}")
        elif self.provider == 'sentence-transformers' and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model_name = self.model_name or 'all-MiniLM-L6-v2'
            self.model = SentenceTransformer(self.model_name)
            logging.info(f"Using Sentence Transformers embeddings with model {self.model_name}")
        else:
            self.provider = 'fallback'
            logging.warning(f"Requested provider '{self.provider}' not available. Using fallback random embeddings.")

    def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            response = openai.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logging.error(f"Error generating OpenAI embeddings: {str(e)}")
            return self._generate_fallback_embeddings(texts)

    def _generate_cohere_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Cohere API.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            response = cohere_client.embed(
                texts=texts,
                model=self.model_name,
                input_type="search_document"  # Required parameter for newer Cohere API
            )
            return response.embeddings
        except Exception as e:
            logging.error(f"Error generating Cohere embeddings: {str(e)}")
            return self._generate_fallback_embeddings(texts)

    def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Sentence Transformers.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logging.error(f"Error generating Sentence Transformers embeddings: {str(e)}")
            return self._generate_fallback_embeddings(texts)

    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate fallback random embeddings.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        # Generate deterministic "random" embeddings based on text hash
        embeddings = []
        for text in texts:
            # Create a hash of the text
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Use the hash to seed a random number generator
            np.random.seed(int(text_hash, 16) % (2**32))
            # Generate a random embedding
            embedding = np.random.random(self.embedding_dim).astype(np.float32)
            # Normalize to unit length
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding.tolist())
        return embeddings

    def _generate_embeddings_uncached(self, text_key: str) -> List[float]:
        """Generate embeddings for a single text (for caching).

        Args:
            text_key: Text to embed

        Returns:
            Embedding vector
        """
        if self.provider == 'openai' and OPENAI_AVAILABLE:
            embeddings = self._generate_openai_embeddings([text_key])
        elif self.provider == 'cohere' and COHERE_AVAILABLE:
            embeddings = self._generate_cohere_embeddings([text_key])
        elif self.provider == 'sentence-transformers' and SENTENCE_TRANSFORMERS_AVAILABLE:
            embeddings = self._generate_sentence_transformer_embeddings([text_key])
        else:
            embeddings = self._generate_fallback_embeddings([text_key])

        return embeddings[0]

    def get_embeddings(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Get embeddings for multiple texts, with batching.

        Args:
            texts: List of text strings
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        # Process in batches to avoid API limits
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Try to get from cache first
            batch_embeddings = []
            for text in batch:
                # Use the cached version
                embedding = self.generate_embeddings(text)
                batch_embeddings.append(embedding)

            all_embeddings.extend(batch_embeddings)

            # Add a small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return all_embeddings

    def clear_cache(self):
        """Clear the embedding cache."""
        self.generate_embeddings.cache_clear()

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings.

        Returns:
            Embedding dimension
        """
        if self.provider == 'openai':
            # OpenAI embedding dimensions
            model_dimensions = {
                'text-embedding-3-small': 1536,
                'text-embedding-3-large': 3072,
                'text-embedding-ada-002': 1536
            }
            return model_dimensions.get(self.model_name, 1536)
        elif self.provider == 'cohere':
            # Cohere embedding dimensions
            model_dimensions = {
                'embed-english-v3.0': 1024,
                'embed-multilingual-v3.0': 1024
            }
            return model_dimensions.get(self.model_name, 1024)
        elif self.provider == 'sentence-transformers':
            # Try to get dimension from model
            if hasattr(self, 'model'):
                return self.model.get_sentence_embedding_dimension()
            # Default dimensions for common models
            model_dimensions = {
                'all-MiniLM-L6-v2': 384,
                'all-mpnet-base-v2': 768
            }
            return model_dimensions.get(self.model_name, 384)
        else:
            return self.embedding_dim

# Create a singleton instance
embedding_service = EmbeddingService()
