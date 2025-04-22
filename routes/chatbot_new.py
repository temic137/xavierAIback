from flask import Blueprint, request, jsonify, session, current_app, logging, url_for, redirect, render_template, url_for, Response
from models import Chatbot, Feedback, Ticket, TicketResponse, QuestionAnalytics
from werkzeug.utils import secure_filename
from extensions import db
from utils.nlp_utils import get_general_answer, initialize_faiss_index, preprocess_data
from utils.file_utils import extract_text_from_pdf, read_text_file, extract_folder_content, extract_text_from_url
from utils.api_utils import fetch_real_time_data
import json
import uuid
import os
from functools import wraps
from transformers import pipeline
import logging
import speech_recognition as sr
import tempfile
from sqlalchemy import desc
from flask_cors import cross_origin, CORS
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from models import Chatbot, GmailIntegration
from extensions import db
from routes.analytics import track_question_helper
import requests
import time
from dotenv import load_dotenv
import os
from PIL import Image
import io

load_dotenv()

logging.basicConfig(level=logging.ERROR)

chatbot_bp = Blueprint('chatbot', __name__)

CORS(chatbot_bp, supports_credentials=True)

recognizer = sr.Recognizer()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    return decorated_function

@chatbot_bp.route('/create_chatbot', methods=['POST'])
@login_required
@handle_errors
def create_chatbot():
    data = request.json
    name = data.get('name')

    new_chatbot = Chatbot(
        id=str(uuid.uuid4()),
        name=name,
        user_id=session['user_id'],
        data=json.dumps([])
    )
    db.session.add(new_chatbot)
    db.session.commit()

    return jsonify({"message": "Chatbot created successfully", "chatbot_id": new_chatbot.id}), 201

@chatbot_bp.route('/chatbots', methods=['GET'])
@login_required
@handle_errors
def get_chatbots():
    try:
        user_id = session.get('user_id')  # Use .get() instead of direct access
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        chatbots = Chatbot.query.filter_by(user_id=user_id).all()
        chatbot_list = [{"id": c.id, "name": c.name} for c in chatbots]

        return jsonify(chatbot_list), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_chatbots: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def transcribe_audio():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None

@chatbot_bp.route('/train_chatbot/<chatbot_id>', methods=['POST'])
@handle_errors
def train_chatbot(chatbot_id):
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or chatbot.user_id != session['user_id']:
        return jsonify({"error": "Chatbot not found or unauthorized"}), 404

    file = request.files.get('file')
    api_url = request.form.get('api_url')
    folder_path = request.form.get('folder_path')
    website_url = request.form.get('website_url')

    pdf_data, db_data, folder_data, web_data = [], [], [], []

    if file:
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension == '.pdf':
            pdf_text = extract_text_from_pdf(filepath)
            pdf_data.append(pdf_text)
        elif file_extension in ['.txt', '.md', '.rst']:
            raw_text = read_text_file(filepath)
            pdf_data.append({'page': 'file', 'text': raw_text})
        os.remove(filepath)

    if api_url:
        real_time_data = fetch_real_time_data(api_url)
        if real_time_data:
            real_time_text = json.dumps(real_time_data, indent=2)
            db_data.append({'page': 'real_time', 'text': real_time_text})
    if folder_path:
        folder_data = extract_folder_content(folder_path)
    if website_url:
        web_data = extract_text_from_url(website_url)

    if not (pdf_data or db_data or folder_data or web_data):
        return jsonify({"error": "No data provided."}), 400

    new_data = {"pdf_data": pdf_data, "db_data": db_data, "folder_data": folder_data, "web_data": web_data}

    if not chatbot.data:
        chatbot.data = []
    if isinstance(chatbot.data, str):
        chatbot.data = json.loads(chatbot.data)
    if isinstance(chatbot.data, list):
        chatbot.data.append(new_data)
    else:
        chatbot.data = [chatbot.data, new_data]

    # Initialize FAISS index with preprocessed data
    structured_data = preprocess_data(pdf_data, folder_data, web_data)
    initialize_faiss_index(structured_data, chatbot_id)

    chatbot.data = json.dumps(chatbot.data)
    db.session.commit()

    return jsonify({"message": "Chatbot trained successfully"}), 200

@chatbot_bp.route('/chatbot/<chatbot_id>', methods=['GET'])
def get_chatbot_data(chatbot_id):
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or chatbot.user_id != session['user_id']:
        return jsonify({"error": "Chatbot not found or unauthorized"}), 404

    return jsonify({"id": chatbot.id, "name": chatbot.name, "data": chatbot.data}), 200

@chatbot_bp.route('/chatbot/<chatbot_id>', methods=['PUT'])
def update_chatbot_data(chatbot_id):
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or chatbot.user_id != session['user_id']:
        return jsonify({"error": "Chatbot not found or unauthorized"}), 404

    data = request.json
    chatbot.name = data.get('name', chatbot.name)
    chatbot.data = data.get('data', chatbot.data)

    db.session.commit()

    return jsonify({"message": "Chatbot updated successfully"}), 200

@chatbot_bp.route('/delete_chatbot/<chatbot_id>', methods=['DELETE'])
@handle_errors
def delete_chatbot(chatbot_id):
    # First check if the chatbot exists and belongs to the current user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or chatbot.user_id != session['user_id']:
        return jsonify({"error": "Chatbot not found or unauthorized"}), 404

    # Delete all related question_analytics records first
    QuestionAnalytics.query.filter_by(chatbot_id=chatbot_id).delete()

    # Then delete the chatbot
    db.session.delete(chatbot)
    db.session.commit()

    return jsonify({"message": "Chatbot deleted successfully"}), 200

@chatbot_bp.route('/chatbots/<chatbot_id>', methods=['GET'])
@handle_errors
def get_chatbot(chatbot_id):
    user_id = session['user_id']
    chatbots = Chatbot.query.filter_by(user_id=user_id).all()

    chatbot = Chatbot.query.get_or_404(chatbot_id)

    # Ensure the chatbot belongs to the current user
    if chatbot.user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    chatbot_list = [{"id": c.id, "name": c.name} for c in chatbots]

    return jsonify({
        "chatbot": {
            "id": chatbot.id,
            "name": chatbot.name
        },
        "chatbot_list": chatbot_list
    }), 200

@chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
def chatbot_ask(chatbot_id):
    start_time = time.time()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Use FAISS-based retrieval with Hugging Face embeddings
    answer = get_general_answer(chatbot.data, question, chatbot_id)

    processing_time = time.time() - start_time
    track_question_helper(chatbot_id, {
        "question": question,
        "answer": answer,
        "question_metadata": {"processing_time": processing_time}
    })

    return jsonify({
        "question": question,
        "answer": answer,
        "processing_time": round(processing_time, 3)
    })

def transcribe_audio_file(file_path):
    r = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return None

@chatbot_bp.route('/chatbot/<chatbot_id>/feedback', methods=['POST', 'OPTIONS'])
def submit_feedback(chatbot_id):
    if request.method == 'OPTIONS':
        return '', 204

    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    data = request.json
    feedback_text = data.get('feedback')
    # user_id = request.headers.get('User-ID')
    user_id = request.headers.get('User-ID', '4269')  # Retrieve the user ID

    # user_id = data.get('user_id')  # Assume user provides their user_id in the request
    if not user_id:
        # If no user_id is provided, create a temporary user_id (or a placeholder, like "guest")
        user_id = '4269'
    if not feedback_text:
        return "Feedback is missing", 400

    if not feedback_text:
        return jsonify({"error": "No feedback provided"}), 400
    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400  # Ensure User-ID is present

    try:
        new_feedback = Feedback(
            chatbot_id=chatbot_id,
            user_id=4269,  # Ensure this is an integer or correct type as per your DB schema
            feedback=feedback_text,
            created_at=datetime.utcnow()
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({"message": "Feedback submitted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in submit_feedback: {str(e)}")
        return jsonify({"error": "An error occurred while saving the feedback"}), 500

@chatbot_bp.route('/chatbot/<chatbot_id>/feedback', methods=['GET'])
@login_required
@handle_errors
def get_chatbot_feedback(chatbot_id):
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    # Query all feedback for the specified chatbot
    feedback_list = Feedback.query.filter_by(chatbot_id=chatbot_id).order_by(desc(Feedback.created_at)).all()

    # Prepare the response data as a string
    feedback_strings = []
    for feedback in feedback_list:
        feedback_str = (
            f"Feedback ID: {feedback.id}\n"
            f"User ID: {feedback.user_id}\n"
            f"Feedback: {feedback.feedback}\n"
            f"Created At: {feedback.created_at.isoformat()}\n"
            f"------------------------"
        )
        feedback_strings.append(feedback_str)

    # Join all feedback strings with newlines
    combined_feedback = "\n".join(feedback_strings)

    return jsonify({
        "chatbot_name": chatbot.name,
        "feedback": combined_feedback
    }), 200

@chatbot_bp.route('/chatbot/all-feedback', methods=['GET'])
def get_all_chatbots_feedback():
    # Query all chatbots
    chatbots = Chatbot.query.all()

    if not chatbots:
        return jsonify({"error": "No chatbots found"}), 404

    response_data = []

    for chatbot in chatbots:
        # Query all feedback for each chatbot
        feedback_list = Feedback.query.filter_by(chatbot_id=chatbot.id)\
                              .order_by(desc(Feedback.created_at)).all()

        # Prepare feedback strings for this chatbot
        feedback_strings = []
        for feedback in feedback_list:
            feedback_str = (
                f"Feedback ID: {feedback.id}\n"
                f"User ID: {feedback.user_id}\n"
                f"Feedback: {feedback.feedback}\n"
                f"Created At: {feedback.created_at.isoformat()}\n"
                f"------------------------"
            )
            feedback_strings.append(feedback_str)

        # Add chatbot data to response
        chatbot_data = {
            "chatbot_id": chatbot.id,
            "chatbot_name": chatbot.name,
            "feedback": "\n".join(feedback_strings) if feedback_strings else "No feedback available"
        }
        response_data.append(chatbot_data)

    return jsonify({
        "total_chatbots": len(chatbots),
        "chatbots": response_data
    }), 200

@chatbot_bp.route('/get_chatbot_script/<chatbot_id>')
@login_required
@handle_errors
def get_chatbot_script(chatbot_id):
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    # Get customization settings with defaults
    customization = {
        "theme_color": "",
        "avatar_url": ""
    }
    if chatbot.data:
        try:
            chatbot_data = json.loads(chatbot.data) if isinstance(chatbot.data, str) else chatbot.data
            if isinstance(chatbot_data, list) and chatbot_data:
                chatbot_data = chatbot_data[-1]
            if isinstance(chatbot_data, dict):
                stored_custom = chatbot_data.get('customization', {})
                customization.update(stored_custom)
        except json.JSONDecodeError:
            pass

    # Ensure HTTPS in the script URL
    script = (
        f'''<script src="{url_for('static', filename='js/widget.js', _external=True, _scheme='https')}" data-id="{chatbot_id}" data-name="{chatbot.name}" data-theme="{customization['theme_color']}" data-avatar="{customization['avatar_url']}" data-api="{request.url_root.replace('http://', 'https://')}" data-enable-leads="true"></script>'''
    )

    return jsonify({
        'integration_code': script,
        'preview': script
    })

@chatbot_bp.route('/ticket/create/<chatbot_id>', methods=['POST'])
def create_ticket(chatbot_id):
    data = request.json

    # Check required fields
    if not all(field in data for field in ['subject', 'description', 'account_details']):
        return jsonify({"error": "Missing required fields"}), 400

    # Create the ticket with default user_id
    new_ticket = Ticket(
        user_id=4269,  # Always use the default user
        chatbot_id=chatbot_id,
        subject=data['subject'],
        description=data['description'],
        priority=data.get('priority', 'medium'),
        account_details=data['account_details']
    )

    try:
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({
            "message": "Ticket created successfully",
            "ticket_id": new_ticket.id
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in create_ticket: {str(e)}")
        return jsonify({"error": "An error occurred while creating the ticket"}), 500

@chatbot_bp.route('/tickets/<chatbot_id>', methods=['GET'])
@login_required
@handle_errors
def list_tickets1(chatbot_id):
    # Query tickets filtered by chatbot_id
    user_tickets = Ticket.query.filter_by(chatbot_id=chatbot_id).all()

    # Return the filtered tickets
    return jsonify({
        "tickets": [{
            "id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at.isoformat(),
            "chatbot_id": ticket.chatbot_id,
            "user_id": ticket.user_id,
            "account_details": ticket.account_details
        } for ticket in user_tickets]
    }), 200

@chatbot_bp.route('/tickets', methods=['GET'])
# @login_required
def list_tickets():
    user_tickets = Ticket.query.all()
    return jsonify({
        "tickets": [{
            "id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at.isoformat()
        } for ticket in user_tickets]
    }), 200

@chatbot_bp.route('/ticket/<ticket_id>', methods=['GET'])
# @login_required
# @handle_errors
def get_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    responses = TicketResponse.query.filter_by(ticket_id=ticket_id).all()

    return jsonify({
        "ticket": {
            "id": ticket.id,
            "subject": ticket.subject,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "account_details": ticket.account_details,
            "created_at": ticket.created_at.isoformat()
        },
        "responses": [{
            "id": response.id,
            "message": response.message,
            "user_id": response.user_id,
            "created_at": response.created_at.isoformat()
        } for response in responses]
    }), 200

@chatbot_bp.route('/ticket/<ticket_id>/update-status', methods=['PATCH'])
@login_required
@handle_errors
def update_ticket_status(ticket_id):
    data = request.json
    if 'status' not in data:
        return jsonify({"error": "Status is required"}), 400

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = data['status']
    db.session.commit()

    return jsonify({
        "message": "Ticket status updated successfully",
        "ticket": {
            "id": ticket.id,
            "status": ticket.status
        }
    }), 200

@chatbot_bp.route('/ticket/delete/<ticket_id>', methods=['DELETE'])
@login_required
@handle_errors
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket deleted successfully"}), 200

@chatbot_bp.route('/chatbot/<chatbot_id>/customize', methods=['GET'])
@cross_origin(supports_credentials=True)
@handle_errors
def get_chatbot_customization(chatbot_id):
    try:
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return jsonify({"error": "Chatbot not found"}), 404

        # Initialize default customization
        customization = {
            "theme_color": "#0084ff",  # Default blue color
            "avatar_url": "",  # Default empty avatar URL
            "enable_tickets": True  # Default to enabled
        }

        # Get customization settings if they exist
        if chatbot.data:
            try:
                # Handle string data
                if isinstance(chatbot.data, str):
                    chatbot_data = json.loads(chatbot.data)
                else:
                    chatbot_data = chatbot.data

                # Handle list data (take the last item if it's a list)
                if isinstance(chatbot_data, list):
                    if chatbot_data:
                        chatbot_data = chatbot_data[-1]
                    else:
                        chatbot_data = {}

                # Get customization from dictionary
                if isinstance(chatbot_data, dict):
                    stored_customization = chatbot_data.get('customization', {})
                    if stored_customization:
                        customization.update(stored_customization)

            except json.JSONDecodeError:
                current_app.logger.error("Invalid JSON in chatbot data")
                pass  # Use default customization

        return jsonify(customization), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_chatbot_customization: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@chatbot_bp.route('/chatbot/<chatbot_id>/customize', methods=['PUT'])
@cross_origin(supports_credentials=True)
@handle_errors
def customize_chatbot(chatbot_id):
    try:
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return jsonify({"error": "Chatbot not found"}), 404

        data = request.json
        theme_color = data.get('theme_color')
        avatar_url = data.get('avatar_url')
        enable_tickets = data.get('enable_tickets')

        # Validate theme color (hex format)
        if theme_color:
            if not isinstance(theme_color, str) or not theme_color.startswith('#') or len(theme_color) != 7:
                return jsonify({"error": "Invalid theme color format. Use hex format (e.g., #FF0000)"}), 400

        # Validate avatar URL
        if avatar_url and not isinstance(avatar_url, str):
            return jsonify({"error": "Invalid avatar URL format"}), 400

        # Validate boolean values
        if enable_tickets is not None and not isinstance(enable_tickets, bool):
            return jsonify({"error": "enable_tickets must be a boolean value"}), 400

        # Initialize or get existing data
        try:
            if chatbot.data:
                if isinstance(chatbot.data, str):
                    chatbot_data = json.loads(chatbot.data)
                else:
                    chatbot_data = chatbot.data
            else:
                chatbot_data = {}

            # If data is a list, convert to dict or initialize new dict
            if isinstance(chatbot_data, list):
                chatbot_data = chatbot_data[-1] if chatbot_data else {}

            # Ensure we have a dictionary
            if not isinstance(chatbot_data, dict):
                chatbot_data = {}

            # Initialize customization if it doesn't exist
            if 'customization' not in chatbot_data:
                chatbot_data['customization'] = {}

            # Update the customization values
            if theme_color:
                chatbot_data['customization']['theme_color'] = theme_color
            if avatar_url:
                chatbot_data['customization']['avatar_url'] = avatar_url
            if enable_tickets is not None:
                chatbot_data['customization']['enable_tickets'] = enable_tickets

            # Store the updated data
            chatbot.data = json.dumps(chatbot_data)
            db.session.commit()

            return jsonify({
                "message": "Chatbot customization updated successfully",
                "customization": chatbot_data['customization']
            }), 200

        except json.JSONDecodeError:
            current_app.logger.error("Invalid JSON in chatbot data")
            # Initialize new data structure with all settings
            new_data = {
                'customization': {
                    'theme_color': theme_color if theme_color else "#0084ff",
                    'avatar_url': avatar_url if avatar_url else "",
                    'enable_tickets': enable_tickets if enable_tickets is not None else True
                }
            }
            chatbot.data = json.dumps(new_data)
            db.session.commit()
            
            return jsonify({
                "message": "Chatbot customization initialized successfully",
                "customization": new_data['customization']
            }), 200

    except Exception as e:
        current_app.logger.error(f"Error in customize_chatbot: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chatbot_bp.route('/chatbot/<chatbot_id>/upload-avatar', methods=['POST'])
@cross_origin(supports_credentials=True)
@handle_errors
def upload_avatar(chatbot_id):
    try:
        if 'avatar' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Process and compress image
            image = Image.open(file)

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            # Resize image while maintaining aspect ratio
            max_size = (400, 400)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Generate unique filename
            filename = secure_filename(f"{chatbot_id}_{int(time.time())}.jpg")
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # Save compressed image
            image.save(filepath, 'JPEG', quality=85, optimize=True)

            # Generate URL for the saved image
            avatar_url = url_for('static',
                               filename=f'uploads/avatars/{filename}',
                               _external=True)

            return jsonify({"avatar_url": avatar_url}), 200

        return jsonify({"error": "Invalid file type"}), 400

    except Exception as e:
        current_app.logger.error(f"Error uploading avatar: {str(e)}")
        return jsonify({"error": "Failed to upload image"}), 500

def get_db_session():
    """Get a database session and ensure proper cleanup"""
    session = db.session()
    try:
        yield session
    finally:
        session.close()

@chatbot_bp.route('/ticket/<ticket_id>/priority', methods=['PUT'])
@handle_errors
def update_ticket_priority(ticket_id):
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        new_priority = data.get('priority')

        # Validate priority
        valid_priorities = ['low', 'medium', 'high']
        if not new_priority or new_priority not in valid_priorities:
            return jsonify({"error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}), 400

        # Check if ticket exists
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404

        # Update priority
        ticket.priority = new_priority
        db.session.commit()

        return jsonify({
            "ticket_id": ticket.id,
            "priority": ticket.priority,
            "message": f"Ticket priority updated to {new_priority}"
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_ticket_priority: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        current_app.logger.error(f"Error updating ticket priority: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
