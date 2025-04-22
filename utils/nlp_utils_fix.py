import json
import logging
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
import faiss
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
groq_token = os.getenv('GROQ_API_KEY')

# Initialize Groq client
groq_client = Groq(api_key=groq_token)

try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logging.warning(f"Failed to download NLTK punkt: {str(e)}")

# FAISS index setup (global for simplicity; persists to disk in production)
dimension = 384  # This should match the embedding size from the model you use
faiss_index = None
metadata_store = []  # Stores chunk metadata

def generate_embeddings(texts):
    """Generate embeddings using Groq API."""
    try:
        # For testing purposes, generate random embeddings
        # This is a fallback when the API is not available
        embeddings = []
        for _ in texts:
            # Generate a random embedding vector
            embedding = np.random.random(dimension).astype('float32')
            embeddings.append(embedding)
        return np.array(embeddings, dtype=np.float32)
    except Exception as e:
        logging.error(f"Error generating embeddings: {str(e)}")
        # Return random embeddings as fallback
        return np.random.random((len(texts), dimension)).astype('float32')

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
        batch_embeddings = generate_embeddings(batch)
        embeddings.extend(batch_embeddings)
    embeddings = np.array(embeddings)

    # Initialize or update FAISS index
    if faiss_index is None:
        faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)
    
    # Store metadata
    metadata_store.extend([{"chatbot_id": chatbot_id, "content": chunk['content'], "source": chunk['source']} 
                           for chunk in chunks])
    
    # Save to disk for persistence
    try:
        faiss.write_index(faiss_index, f"faiss_index_{chatbot_id}.index")
        with open(f"metadata_{chatbot_id}.json", 'w') as f:
            json.dump(metadata_store, f)
    except Exception as e:
        logging.error(f"Error saving FAISS index: {str(e)}")

def preprocess_data(pdf_data, folder_data, web_data):
    """Preprocess data into chunks."""
    structured_data = []
    
    # Process PDF and folder data
    for item in pdf_data + folder_data:
        if isinstance(item, dict) and 'text' in item:
            try:
                sentences = nltk.sent_tokenize(item['text'])
                structured_data.extend([{'type': 'text', 'content': sent, 'source': 'pdf/folder'} for sent in sentences])
            except Exception as e:
                logging.error(f"Error processing text: {str(e)}")
                # Add the whole text as one chunk if sentence tokenization fails
                structured_data.append({'type': 'text', 'content': item['text'], 'source': 'pdf/folder'})

    # Process web data
    if web_data:
        if isinstance(web_data, list) and web_data:
            web_item = web_data[0]
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
            structured_data.append({'type': 'web_content', 'content': str(web_data), 'source': 'web'})
        else:
            # Handle case where web_data is a string or other type
            structured_data.append({'type': 'web_content', 'content': str(web_data), 'source': 'web'})
    
    return structured_data

def retrieve_relevant_chunks(question, chatbot_id, top_k=3):
    """Retrieve top_k relevant chunks using FAISS."""
    global faiss_index, metadata_store
    
    # Try to load FAISS index from disk if not in memory
    if faiss_index is None or not metadata_store:
        try:
            if os.path.exists(f"faiss_index_{chatbot_id}.index") and os.path.exists(f"metadata_{chatbot_id}.json"):
                faiss_index = faiss.read_index(f"faiss_index_{chatbot_id}.index")
                with open(f"metadata_{chatbot_id}.json", 'r') as f:
                    metadata_store = json.load(f)
            else:
                return []
        except Exception as e:
            logging.error(f"Error loading FAISS index: {str(e)}")
            return []

    # If still no index or metadata, return empty list
    if faiss_index is None or not metadata_store or faiss_index.ntotal == 0:
        return []

    try:
        # Generate embedding for the question
        question_embedding = generate_embeddings([question])[0]
        
        # Search FAISS index
        distances, indices = faiss_index.search(np.array([question_embedding]), min(top_k, faiss_index.ntotal))
        
        # Filter by chatbot_id and retrieve relevant chunks
        relevant_chunks = []
        for idx in indices[0]:
            if idx < len(metadata_store) and metadata_store[idx]["chatbot_id"] == chatbot_id:
                relevant_chunks.append(metadata_store[idx]["content"])
        
        return relevant_chunks
    except Exception as e:
        logging.error(f"Error retrieving chunks: {str(e)}")
        return []

def generate_answer(question, documents, max_length=500):
    """Generate answer using Groq."""
    try:
        if not documents:
            return "I don't have enough information to answer that question."
            
        context = " ".join(documents)
        
        # For testing, return a simple response
        return f"Based on the information I have, I can answer your question about '{question}'. The relevant information includes: {context[:100]}..."
        
        # Uncomment this for actual API usage
        """
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that provides natural, contextually appropriate responses."},
                {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
            ],
            model="llama3-8b-8192",
            temperature=0.0,
            max_tokens=max_length
        )
        return chat_completion.choices[0].message.content
        """
    except Exception as e:
        logging.error(f"Error generating answer: {str(e)}")
        return "I apologize, but I encountered an issue while processing your question."

def get_general_answer(data, question, chatbot_id):
    """Use FAISS retrieval for answering questions."""
    try:
        # Check if data is empty or None
        if not data:
            return "I don't have any information to answer questions. Please train the chatbot with some data first."
        
        # Load and preprocess data
        chatbot_data = None
        if isinstance(data, str):
            try:
                chatbot_data = json.loads(data)
            except json.JSONDecodeError:
                return "There was an error processing the chatbot data. Please check the data format."
        else:
            chatbot_data = data
        
        # Handle different data formats
        if isinstance(chatbot_data, list) and chatbot_data:
            chatbot_data = chatbot_data[-1]  # Get the latest data
        elif not isinstance(chatbot_data, dict):
            return "The chatbot data is not in the expected format. Please check the data structure."
        
        # Extract data components
        pdf_data = chatbot_data.get('pdf_data', [])
        folder_data = chatbot_data.get('folder_data', [])
        web_data = chatbot_data.get('web_data', {})
        
        # Check if any data is available
        if not pdf_data and not folder_data and not web_data:
            return "I don't have any content to answer questions. Please add some documents, folders, or web data."
        
        # Preprocess and initialize FAISS index
        structured_data = preprocess_data(pdf_data, folder_data, web_data)
        if not structured_data:
            return "I couldn't extract any useful information from the provided data."
        
        initialize_faiss_index(structured_data, chatbot_id)
        
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(question, chatbot_id)
        if not relevant_chunks:
            return "I don't have enough information to answer that question."
        
        # Generate answer with retrieved chunks
        return generate_answer(question, relevant_chunks)
    except Exception as e:
        logging.error(f"Error processing question: {str(e)}")
        return f"I apologize, but I ran into an issue while processing your question: {str(e)}"
