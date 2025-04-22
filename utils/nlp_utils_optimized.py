import json
import logging
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
import faiss
from groq import Groq
import os
from dotenv import load_dotenv
import time
from functools import lru_cache

# Load environment variables
load_dotenv()
groq_token = os.getenv('GROQ_API_KEY')

# Initialize Groq client
groq_client = Groq(api_key=groq_token)

nltk.download('punkt', quiet=True)

# FAISS index setup (global for simplicity; persists to disk in production)
dimension = 384  # This should match the embedding size from the model you use
faiss_index = None
metadata_store = []  # Stores chunk metadata

# Cache for chatbot data to avoid repeated JSON parsing
chatbot_data_cache = {}
# Cache expiry time in seconds
CACHE_EXPIRY = 300  # 5 minutes

def generate_embeddings(texts):
    """Generate embeddings for text."""
    try:
        # For simplicity and reliability, we'll use random embeddings
        # This is a temporary solution until we can integrate with a proper embedding API
        embeddings = []
        for _ in texts:
            # Generate a random embedding vector
            embedding = np.random.random(dimension).astype('float32')
            # Normalize the embedding to unit length
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)
        return np.array(embeddings, dtype=np.float32)
    except Exception as e:
        logging.error(f"Error generating embeddings: {str(e)}")
        # Return random embeddings as fallback
        random_embeddings = np.random.random((len(texts), dimension)).astype('float32')
        # Normalize each embedding
        for i in range(len(random_embeddings)):
            random_embeddings[i] = random_embeddings[i] / np.linalg.norm(random_embeddings[i])
        return random_embeddings

def initialize_faiss_index(chunks, chatbot_id):
    """Initialize or update FAISS index with embeddings for data chunks."""
    global faiss_index, metadata_store
    texts = [chunk['content'] for chunk in chunks]
    if not texts:
        return

    # Generate embeddings in batches to avoid API limits
    batch_size = 10  # Smaller batch size due to potential token limits in Groq
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings.extend(generate_embeddings(batch))
    embeddings = np.array(embeddings)

    # Initialize or update FAISS index
    if faiss_index is None:
        faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)

    # Store metadata
    metadata_store.extend([{"chatbot_id": chatbot_id, "content": chunk['content'], "source": chunk['source']}
                           for chunk in chunks])

    # Save to disk for persistence
    faiss.write_index(faiss_index, f"faiss_index_{chatbot_id}.index")
    with open(f"metadata_{chatbot_id}.json", 'w') as f:
        json.dump(metadata_store, f)

def preprocess_data(pdf_data, folder_data, web_data):
    """Preprocess data into chunks."""
    structured_data = []

    # Process PDF data
    if pdf_data:
        for item in pdf_data:
            if isinstance(item, dict) and 'text' in item and item['text']:
                try:
                    # Try to tokenize into sentences
                    try:
                        sentences = nltk.sent_tokenize(item['text'])
                        structured_data.extend([{'type': 'text', 'content': sent, 'source': 'pdf'} for sent in sentences])
                    except:
                        # If tokenization fails, split by newlines
                        lines = item['text'].split('\n')
                        structured_data.extend([{'type': 'text', 'content': line, 'source': 'pdf'}
                                              for line in lines if line.strip()])
                except Exception as e:
                    logging.error(f"Error processing PDF text: {str(e)}")
                    # Add the whole text as one chunk if all processing fails
                    structured_data.append({'type': 'text', 'content': item['text'], 'source': 'pdf'})

    # Process folder data
    if folder_data:
        for item in folder_data:
            if isinstance(item, dict) and 'text' in item and item['text']:
                try:
                    # Try to tokenize into sentences
                    try:
                        sentences = nltk.sent_tokenize(item['text'])
                        structured_data.extend([{'type': 'text', 'content': sent, 'source': 'folder'} for sent in sentences])
                    except:
                        # If tokenization fails, split by newlines
                        lines = item['text'].split('\n')
                        structured_data.extend([{'type': 'text', 'content': line, 'source': 'folder'}
                                              for line in lines if line.strip()])
                except Exception as e:
                    logging.error(f"Error processing folder text: {str(e)}")
                    # Add the whole text as one chunk if all processing fails
                    structured_data.append({'type': 'text', 'content': item['text'], 'source': 'folder'})

    # Process web data
    if web_data:
        if isinstance(web_data, list) and web_data:
            for web_item in web_data:
                if isinstance(web_item, dict):
                    if 'title' in web_item:
                        structured_data.append({'type': 'title', 'content': web_item['title'], 'source': 'web'})
                    if 'sections' in web_item:
                        for section in web_item['sections']:
                            if 'heading' in section:
                                structured_data.append({'type': 'heading', 'content': section['heading'], 'source': 'web'})
                            if 'content' in section:
                                structured_data.extend([{'type': 'web_content', 'content': item, 'source': 'web'}
                                                      for item in section['content']])
        elif isinstance(web_data, dict):
            # Handle case where web_data is a dictionary
            for key, value in web_data.items():
                structured_data.append({'type': 'web_content', 'content': f"{key}: {value}", 'source': 'web'})
        elif isinstance(web_data, str) and web_data.strip():
            # Handle case where web_data is a non-empty string
            structured_data.append({'type': 'web_content', 'content': web_data, 'source': 'web'})

    # If we still have no structured data but have raw text in pdf_data or folder_data,
    # use a more aggressive approach to extract content
    if not structured_data:
        all_text = ""

        # Extract text from pdf_data
        for item in pdf_data:
            if isinstance(item, dict) and 'text' in item and item['text']:
                all_text += item['text'] + "\n\n"

        # Extract text from folder_data
        for item in folder_data:
            if isinstance(item, dict) and 'text' in item and item['text']:
                all_text += item['text'] + "\n\n"

        if all_text.strip():
            # Split by paragraphs (double newlines)
            paragraphs = all_text.split("\n\n")
            for para in paragraphs:
                if para.strip():
                    structured_data.append({'type': 'text', 'content': para.strip(), 'source': 'combined'})

    return structured_data

@lru_cache(maxsize=32)
def retrieve_relevant_chunks(question, chatbot_id, top_k=3):
    """Retrieve top_k relevant chunks using FAISS."""
    global faiss_index, metadata_store
    if faiss_index is None or not metadata_store:
        if os.path.exists(f"faiss_index_{chatbot_id}.index") and os.path.exists(f"metadata_{chatbot_id}.json"):
            faiss_index = faiss.read_index(f"faiss_index_{chatbot_id}.index")
            with open(f"metadata_{chatbot_id}.json", 'r') as f:
                metadata_store = json.load(f)
        else:
            return []

    # Generate embedding for the question
    question_embedding = generate_embeddings([question])[0]

    # Search FAISS index
    distances, indices = faiss_index.search(np.array([question_embedding]), top_k)

    # Filter by chatbot_id and retrieve relevant chunks
    relevant_chunks = [metadata_store[idx] for idx in indices[0] if idx < len(metadata_store) and metadata_store[idx]["chatbot_id"] == chatbot_id]
    return [chunk["content"] for chunk in relevant_chunks]

def format_conversation_history(conversation_history):
    """Format conversation history for the LLM prompt."""
    if not conversation_history:
        return ""
    
    formatted_history = "\nPrevious conversation:\n"
    for message in conversation_history:
        role = "User" if message["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {message['content']}\n"
    
    return formatted_history

def get_chatbot_data(data, chatbot_id):
    """Parse and cache chatbot data to avoid repeated processing."""
    global chatbot_data_cache
    
    # Check if we have a valid cached version
    cache_key = f"{chatbot_id}_{hash(str(data))}"
    current_time = time.time()
    
    if cache_key in chatbot_data_cache:
        cached_data, timestamp = chatbot_data_cache[cache_key]
        if current_time - timestamp < CACHE_EXPIRY:
            return cached_data
    
    # Parse the data if not cached or cache expired
    try:
        chatbot_data = None
        if isinstance(data, str):
            try:
                chatbot_data = json.loads(data)
            except json.JSONDecodeError:
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

def get_general_answer(data, question, chatbot_id, conversation_history=None):
    """Generate answers using the Groq API with full context and conversation history."""
    try:
        # Check if data is empty or None
        if not data:
            return "I don't have any information to answer questions. Please train the chatbot with some data first. Would you like to create a support ticket instead?"

        # Get and parse chatbot data (using cache if available)
        parsed_data = get_chatbot_data(data, chatbot_id)
        if not parsed_data:
            return "There was an error processing the chatbot data. Please check the data format."
        
        pdf_data = parsed_data['pdf_data']
        folder_data = parsed_data['folder_data']
        web_data = parsed_data['web_data']

        # Check if any data is available
        if not pdf_data and not folder_data and not web_data:
            return "I don't have any content to answer questions. Would you like to create a support ticket so someone can help you with this?"

        # Use a more efficient approach to extract context
        # Instead of loading all data, retrieve only relevant chunks based on the question
        relevant_chunks = retrieve_relevant_chunks(question, chatbot_id, top_k=5)
        
        if not relevant_chunks:
            # If no relevant chunks found, extract some representative content
            all_text_chunks = []
            
            # Get a sample from each data source
            if pdf_data and len(pdf_data) > 0:
                sample = pdf_data[0]
                if isinstance(sample, dict) and 'text' in sample:
                    all_text_chunks.append(sample['text'][:1000])  # First 1000 chars
            
            if folder_data and len(folder_data) > 0:
                sample = folder_data[0]
                if isinstance(sample, dict) and 'text' in sample:
                    all_text_chunks.append(sample['text'][:1000])
            
            if not all_text_chunks:
                return "I couldn't find relevant information to answer your question. Would you like to create a support ticket to get help from a human agent?"
        else:
            all_text_chunks = relevant_chunks

        # Combine chunks into context, limiting total size
        combined_context = "\n\n".join(all_text_chunks)
        max_context_length = 8000  # Reduced context window to save tokens
        if len(combined_context) > max_context_length:
            combined_context = combined_context[:max_context_length] + "..."

        # Format conversation history if provided
        # Only include the most recent messages to save tokens
        if conversation_history and len(conversation_history) > 6:
            conversation_history = conversation_history[-6:]  # Keep last 6 messages (3 exchanges)
            
        conversation_context = format_conversation_history(conversation_history) if conversation_history else ""

        # Use Groq API to generate an answer based on the context and conversation history
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """You are a helpful AI assistant that provides natural, conversational responses based on the provided knowledge base.
                    
                    Guidelines:
                    1. Only use information from the provided context to answer questions
                    2. If you don't have enough information, say 'I don't have enough information to answer that question. Would you like to create a support ticket so someone can help you with this?'
                    3. Be direct, concise, and helpful
                    4. Maintain a natural, conversational tone
                    5. NEVER start responses with phrases like "Based on the information I have" or similar
                    6. Answer directly and conversationally as if you're having a natural dialogue
                    7. Use the conversation history to maintain context and provide more relevant responses
                    8. Refer to previous exchanges when appropriate to create a more cohesive conversation
                    9. Adapt your tone to match the user's style and level of formality"""},
                    {"role": "user", "content": f"Knowledge Base:\n{combined_context}\n{conversation_context}\nCurrent Question: {question}"}
                ],
                # model="llama3-8b-8192",
                model="llama3-70b-8192",
                temperature=0.0,
                max_tokens=300  # Reduced token count for efficiency
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logging.error(f"Error calling Groq API: {str(e)}")
            # Fallback to a simple response if API call fails
            return "I apologize, but I encountered an issue while processing your question. Please try again later."

    except Exception as e:
        logging.error(f"Error processing question: {str(e)}")
        return f"I apologize, but I ran into an issue while processing your question."
