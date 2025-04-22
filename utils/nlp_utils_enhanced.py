"""
Enhanced NLP utilities for chatbot question answering.
Uses vector database for efficient retrieval and context management.
"""

import json
import logging
import os
import time
from typing import List, Dict, Any, Optional, Union
from functools import lru_cache
import numpy as np
from dotenv import load_dotenv

# Import our custom services
from utils.vector_db import vector_db
from utils.text_processing import text_processor
from utils.embedding_service import embedding_service

# Load environment variables
load_dotenv()

# Initialize Groq client for LLM
try:
    from groq import Groq
    groq_token = os.getenv('GROQ_API_KEY')
    if groq_token:
        groq_client = Groq(api_key=groq_token)
    else:
        logging.warning("GROQ_API_KEY not found in environment variables")
except ImportError:
    logging.warning("Groq package not installed")
    groq_client = None

# Cache for parsed chatbot data
chatbot_data_cache = {}
CACHE_EXPIRY = 300  # 5 minutes

def parse_chatbot_data(data: Union[str, Dict, List], chatbot_id: str) -> Optional[Dict[str, Any]]:
    """Parse chatbot data from various formats.
    
    Args:
        data: Chatbot data (string, dict, or list)
        chatbot_id: ID of the chatbot
        
    Returns:
        Dictionary with parsed data components or None if parsing fails
    """
    # Check cache first
    cache_key = f"{chatbot_id}_{hash(str(data))}"
    current_time = time.time()
    
    if cache_key in chatbot_data_cache:
        cached_data, timestamp = chatbot_data_cache[cache_key]
        if current_time - timestamp < CACHE_EXPIRY:
            return cached_data
    
    # Parse the data
    try:
        chatbot_data = None
        if isinstance(data, str):
            try:
                chatbot_data = json.loads(data)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON for chatbot {chatbot_id}")
                return None
        else:
            chatbot_data = data

        # Handle different data formats
        if isinstance(chatbot_data, list) and chatbot_data:
            chatbot_data = chatbot_data[-1]  # Get the latest data

        # Extract data components
        if isinstance(chatbot_data, dict):
            result = {
                'pdf_data': chatbot_data.get('pdf_data', []),
                'folder_data': chatbot_data.get('folder_data', []),
                'web_data': chatbot_data.get('web_data', {})
            }
            
            # Cache the result
            chatbot_data_cache[cache_key] = (result, current_time)
            return result
        else:
            return None
    except Exception as e:
        logging.error(f"Error parsing chatbot data: {str(e)}")
        return None

def preprocess_and_index_data(chatbot_data: Dict[str, Any], chatbot_id: str) -> bool:
    """Preprocess and index chatbot data into the vector database.
    
    Args:
        chatbot_data: Dictionary with data components
        chatbot_id: ID of the chatbot
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract data components
        pdf_data = chatbot_data.get('pdf_data', [])
        folder_data = chatbot_data.get('folder_data', [])
        web_data = chatbot_data.get('web_data', {})
        
        # Convert web_data to list format if it's a dictionary
        if isinstance(web_data, dict):
            web_data = [{'text': web_data.get('content', ''), 'url': web_data.get('url', '')}]
        
        # Process documents into chunks
        all_documents = []
        
        # Process PDF data
        for item in pdf_data:
            if isinstance(item, dict) and 'text' in item:
                doc = {
                    'text': item['text'],
                    'source': 'pdf',
                    'filename': item.get('filename', 'unknown'),
                    'chatbot_id': chatbot_id
                }
                all_documents.append(doc)
        
        # Process folder data
        for item in folder_data:
            if isinstance(item, dict) and 'text' in item:
                doc = {
                    'text': item['text'],
                    'source': 'folder',
                    'filename': item.get('filename', 'unknown'),
                    'chatbot_id': chatbot_id
                }
                all_documents.append(doc)
        
        # Process web data
        for item in web_data:
            if isinstance(item, dict) and 'text' in item:
                doc = {
                    'text': item['text'],
                    'source': 'web',
                    'url': item.get('url', 'unknown'),
                    'chatbot_id': chatbot_id
                }
                all_documents.append(doc)
        
        # If no documents, return early
        if not all_documents:
            logging.warning(f"No documents found for chatbot {chatbot_id}")
            return False
        
        # Process documents into chunks
        chunks = text_processor.process_documents(all_documents)
        
        if not chunks:
            logging.warning(f"No chunks generated for chatbot {chatbot_id}")
            return False
        
        # Extract text content for embedding
        texts = [chunk['content'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = embedding_service.get_embeddings(texts)
        
        # Get embedding dimension
        embedding_dim = embedding_service.get_embedding_dimension()
        
        # Create vector database collection
        vector_db.create_collection(chatbot_id, embedding_dim)
        
        # Add documents to vector database
        vector_db.add_documents(
            collection_name=chatbot_id,
            texts=texts,
            embeddings=embeddings,
            metadatas=[chunk['metadata'] for chunk in chunks]
        )
        
        return True
    except Exception as e:
        logging.error(f"Error preprocessing and indexing data: {str(e)}")
        return False

def retrieve_relevant_context(question: str, chatbot_id: str, top_k: int = 5) -> List[str]:
    """Retrieve relevant context for a question.
    
    Args:
        question: User's question
        chatbot_id: ID of the chatbot
        top_k: Number of relevant chunks to retrieve
        
    Returns:
        List of relevant text chunks
    """
    try:
        # Generate embedding for the question
        question_embedding = embedding_service.get_embeddings([question])[0]
        
        # Search vector database
        search_results = vector_db.search(
            collection_name=chatbot_id,
            query_embedding=question_embedding,
            top_k=top_k,
            filter_dict={"chatbot_id": chatbot_id}
        )
        
        # Extract text from search results
        relevant_chunks = [result['text'] for result in search_results]
        
        return relevant_chunks
    except Exception as e:
        logging.error(f"Error retrieving relevant context: {str(e)}")
        return []

def format_conversation_history(conversation_history: List[Dict[str, Any]]) -> str:
    """Format conversation history for the LLM prompt.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Formatted conversation history string
    """
    if not conversation_history:
        return ""
    
    formatted_history = "\nPrevious conversation:\n"
    for message in conversation_history:
        role = "User" if message["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {message['content']}\n"
    
    return formatted_history

def generate_answer_with_llm(question: str, context: List[str], conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generate an answer using the LLM.
    
    Args:
        question: User's question
        context: List of relevant text chunks
        conversation_history: Optional conversation history
        
    Returns:
        Generated answer
    """
    try:
        if not groq_client:
            return "I apologize, but the LLM service is not available. Please try again later."
        
        if not context:
            return "I don't have enough information to answer that question. Would you like to create a support ticket so someone can help you with this?"
        
        # Combine context chunks
        combined_context = "\n\n".join(context)
        
        # Limit context size to avoid token limits
        max_context_length = 8000  # Adjusted for model context window
        if len(combined_context) > max_context_length:
            combined_context = combined_context[:max_context_length] + "..."
        
        # Format conversation history if provided
        # Only include recent messages to save tokens
        if conversation_history and len(conversation_history) > 6:
            conversation_history = conversation_history[-6:]  # Keep last 6 messages
            
        conversation_context = format_conversation_history(conversation_history) if conversation_history else ""
        
        # Generate answer with LLM
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": """You are a helpful AI assistant that provides natural, contextually appropriate responses based on the provided knowledge base.
                Only use information from the provided context to answer questions.
                If you don't have enough information to answer a question, say 'I don't have enough information to answer that question. Would you like to create a support ticket so someone can help you with this?'
                Be direct, concise, and helpful."""},
                {"role": "user", "content": f"Knowledge Base:\n{combined_context}\n{conversation_context}\nCurrent Question: {question}"}
            ],
            # model="llama3-8b-8192",
            model="llama3-70b-8192",
            temperature=0.0,
            max_tokens=500
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating answer with LLM: {str(e)}")
        return f"I apologize, but I encountered an issue while processing your question. Please try again later."

def get_enhanced_answer(data: Union[str, Dict, List], question: str, chatbot_id: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Get an answer to a question using enhanced context retrieval.
    
    Args:
        data: Chatbot knowledge base data
        question: User's question
        chatbot_id: ID of the chatbot
        conversation_history: Optional conversation history
        
    Returns:
        Generated answer
    """
    try:
        # Parse chatbot data
        parsed_data = parse_chatbot_data(data, chatbot_id)
        if not parsed_data:
            return "I don't have any content to answer questions. Would you like to create a support ticket so someone can help you with this?"
        
        # Check if vector database collection exists
        collection_info = vector_db.get_collection_info(chatbot_id)
        
        # If collection doesn't exist or is empty, preprocess and index data
        if not collection_info.get('exists', False) or collection_info.get('points_count', 0) == 0:
            success = preprocess_and_index_data(parsed_data, chatbot_id)
            if not success:
                return "I'm having trouble processing the knowledge base. Would you like to create a support ticket so someone can help you with this?"
        
        # Retrieve relevant context
        relevant_chunks = retrieve_relevant_context(question, chatbot_id, top_k=5)
        
        if not relevant_chunks:
            return "I don't have enough information to answer that question. Would you like to create a support ticket so someone can help you with this?"
        
        # Generate answer with LLM
        return generate_answer_with_llm(question, relevant_chunks, conversation_history)
    except Exception as e:
        logging.error(f"Error getting enhanced answer: {str(e)}")
        return f"I apologize, but I encountered an issue while processing your question. Please try again later."
