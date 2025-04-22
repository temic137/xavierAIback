"""
Vector database service for efficient storage and retrieval of embeddings.
This implementation uses Qdrant, a vector similarity search engine.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np

# Import Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant not installed. Using fallback local FAISS implementation.")
    import faiss

class VectorDBService:
    """Service for managing vector embeddings and similarity search."""
    
    def __init__(self, use_qdrant=True):
        """Initialize the vector database service.
        
        Args:
            use_qdrant: Whether to use Qdrant (if available) or fallback to local FAISS
        """
        self.use_qdrant = use_qdrant and QDRANT_AVAILABLE
        
        if self.use_qdrant:
            # Initialize Qdrant client
            # For local development, use in-memory storage
            self.client = QdrantClient(":memory:")
            self.collections = set()
        else:
            # Fallback to FAISS
            self.indexes = {}
            self.metadata_stores = {}
    
    def create_collection(self, collection_name: str, vector_size: int = 384) -> bool:
        """Create a new collection in the vector database.
        
        Args:
            collection_name: Name of the collection (usually chatbot_id)
            vector_size: Dimension of the embedding vectors
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_qdrant:
                # Create collection if it doesn't exist
                if collection_name not in self.collections:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=models.Distance.COSINE
                        )
                    )
                    self.collections.add(collection_name)
            else:
                # Create FAISS index if it doesn't exist
                if collection_name not in self.indexes:
                    self.indexes[collection_name] = faiss.IndexFlatL2(vector_size)
                    self.metadata_stores[collection_name] = []
            return True
        except Exception as e:
            logging.error(f"Error creating collection {collection_name}: {str(e)}")
            return False
    
    def add_documents(
        self, 
        collection_name: str, 
        texts: List[str], 
        embeddings: List[List[float]], 
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """Add documents to the vector database.
        
        Args:
            collection_name: Name of the collection
            texts: List of text content
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_qdrant:
                # Ensure collection exists
                if collection_name not in self.collections:
                    self.create_collection(collection_name, len(embeddings[0]))
                
                # Prepare points for Qdrant
                points = []
                for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
                    # Add text to metadata
                    metadata["text"] = text
                    
                    points.append(PointStruct(
                        id=i,
                        vector=embedding,
                        payload=metadata
                    ))
                
                # Upsert points to Qdrant
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            else:
                # Ensure index exists
                if collection_name not in self.indexes:
                    self.create_collection(collection_name, len(embeddings[0]))
                
                # Convert embeddings to numpy array
                embeddings_np = np.array(embeddings, dtype=np.float32)
                
                # Add to FAISS index
                self.indexes[collection_name].add(embeddings_np)
                
                # Store metadata
                for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                    # Add text to metadata
                    metadata["text"] = text
                    self.metadata_stores[collection_name].append(metadata)
            
            return True
        except Exception as e:
            logging.error(f"Error adding documents to {collection_name}: {str(e)}")
            return False
    
    def search(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector database.
        
        Args:
            collection_name: Name of the collection
            query_embedding: Embedding vector of the query
            top_k: Number of results to return
            filter_dict: Dictionary of metadata filters
            
        Returns:
            List of dictionaries containing text and metadata
        """
        try:
            if self.use_qdrant:
                # Ensure collection exists
                if collection_name not in self.collections:
                    return []
                
                # Convert filter_dict to Qdrant filter
                filter_obj = None
                if filter_dict:
                    filter_conditions = []
                    for key, value in filter_dict.items():
                        filter_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )
                    filter_obj = models.Filter(
                        must=filter_conditions
                    )
                
                # Search Qdrant
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=top_k,
                    query_filter=filter_obj
                )
                
                # Format results
                results = []
                for result in search_results:
                    # Extract text from payload
                    text = result.payload.pop("text", "")
                    
                    results.append({
                        "text": text,
                        "metadata": result.payload,
                        "score": result.score
                    })
                
                return results
            else:
                # Ensure index exists
                if collection_name not in self.indexes:
                    return []
                
                # Convert query_embedding to numpy array
                query_embedding_np = np.array([query_embedding], dtype=np.float32)
                
                # Search FAISS index
                distances, indices = self.indexes[collection_name].search(
                    query_embedding_np, min(top_k, self.indexes[collection_name].ntotal)
                )
                
                # Format results
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.metadata_stores[collection_name]):
                        metadata = self.metadata_stores[collection_name][idx].copy()
                        
                        # Apply filter if provided
                        if filter_dict:
                            skip = False
                            for key, value in filter_dict.items():
                                if key not in metadata or metadata[key] != value:
                                    skip = True
                                    break
                            if skip:
                                continue
                        
                        # Extract text from metadata
                        text = metadata.pop("text", "")
                        
                        results.append({
                            "text": text,
                            "metadata": metadata,
                            "score": float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                        })
                
                return results
        except Exception as e:
            logging.error(f"Error searching in {collection_name}: {str(e)}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the vector database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.use_qdrant:
                if collection_name in self.collections:
                    self.client.delete_collection(collection_name=collection_name)
                    self.collections.remove(collection_name)
            else:
                if collection_name in self.indexes:
                    del self.indexes[collection_name]
                    del self.metadata_stores[collection_name]
            return True
        except Exception as e:
            logging.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection information
        """
        try:
            if self.use_qdrant:
                if collection_name in self.collections:
                    collection_info = self.client.get_collection(collection_name=collection_name)
                    return {
                        "name": collection_name,
                        "vector_size": collection_info.config.params.vectors.size,
                        "points_count": collection_info.vectors_count
                    }
                return {"name": collection_name, "exists": False}
            else:
                if collection_name in self.indexes:
                    return {
                        "name": collection_name,
                        "vector_size": self.indexes[collection_name].d,
                        "points_count": self.indexes[collection_name].ntotal
                    }
                return {"name": collection_name, "exists": False}
        except Exception as e:
            logging.error(f"Error getting info for collection {collection_name}: {str(e)}")
            return {"name": collection_name, "error": str(e)}

# Create a singleton instance
vector_db = VectorDBService(use_qdrant=QDRANT_AVAILABLE)
