from flask import Blueprint, request, jsonify, session, current_app, logging, url_for
from models import Chatbot, Feedback, Ticket, TicketResponse, QuestionAnalytics, ConversationMessage
from werkzeug.utils import secure_filename
from extensions import db
from utils.nlp_utils_enhanced import get_enhanced_answer, preprocess_and_index_data, parse_chatbot_data
from utils.file_utils import extract_text_from_pdf, read_text_file, extract_folder_content, extract_text_from_url
from utils.api_utils import fetch_real_time_data
import json
import uuid
import os
from functools import wraps
import logging
import speech_recognition as sr
from sqlalchemy import desc
from flask_cors import cross_origin, CORS
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from routes.analytics import track_question_helper
from dotenv import load_dotenv
import time
from utils.auth_utils import login_required

load_dotenv()

# Pusher integration and real-time chat escalation feature have been removed


logging.basicConfig(level=logging.ERROR)

chatbot_bp = Blueprint('chatbot', __name__)


CORS(chatbot_bp, supports_credentials=True)

recognizer = sr.Recognizer()





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

    # Preprocess and index data using the enhanced vector database
    parsed_data = {'pdf_data': pdf_data, 'folder_data': folder_data, 'web_data': web_data}
    preprocess_and_index_data(parsed_data, chatbot_id)

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

import time
# @chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
# def chatbot_ask(chatbot_id):

#     start_time = time.time()     # Start timing the request

#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     if request.content_type == 'application/json':
#         # Handle JSON input
#         data = request.json
#         question = data.get('question')
#     else:
#         return jsonify({"error": "Unsupported content type"}), 415

#     if not question:
#         return jsonify({"error": "No question provided"}), 400

#     try:
#         chatbot_data_str = chatbot.data if isinstance(chatbot.data, str) else json.dumps(chatbot.data)
#         chatbot_data = json.loads(chatbot_data_str)

#         current_app.logger.debug(f"Chatbot data type: {type(chatbot_data)}")
#         current_app.logger.debug(f"Chatbot data: {chatbot_data}")

#         if isinstance(chatbot_data, list):
#             if len(chatbot_data) > 0:
#                 chatbot_data = chatbot_data[-1]
#             else:
#                 raise ValueError("Chatbot data list is empty")
#         elif not isinstance(chatbot_data, dict):
#             raise ValueError(f"Invalid chatbot data format: {type(chatbot_data)}")

#         current_app.logger.debug(f"Processed chatbot data type: {type(chatbot_data)}")
#         current_app.logger.debug(f"Processed chatbot data: {chatbot_data}")



#         answer = get_general_answer(json.dumps(chatbot_data), question)

#         # Calculate processing time
#         processing_time = time.time() - start_time


#        # Track analytics
#         analytics_data = {
#             "question": question,
#             "answer": answer,
#             "question_metadata": {
#                 "processing_time": processing_time,
#                 "keywords_matched": [
#                     keyword for keyword in ["proce", "inventory", "stock", "available", "category", "type"]
#                     if keyword in question.lower()
#                 ]
#             }
#         }
#         track_question_helper(chatbot_id, analytics_data)

#         return jsonify({
#             "question": question,
#             "answer": answer,
#             "processing_time": round(time() - start_time, 3)
#         })

#     except json.JSONDecodeError as e:
#         current_app.logger.error(f"JSON decode error: {str(e)}")
#         return jsonify({"error": "Invalid chatbot data format"}), 500
#     except ValueError as e:
#         current_app.logger.error(f"Value error: {str(e)}")
#         return jsonify({"error": str(e)}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error in chatbot_ask: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500





#-----------------------------------------------

# @chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
# def chatbot_ask(chatbot_id):
#     start_time = time.time()  # Start timing the request

#     # Validate chatbot exists
#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     # Validate input
#     if request.content_type != 'application/json':
#         return jsonify({"error": "Unsupported content type"}), 415

#     data = request.json
#     question = data.get('question')
#     if not question:
#         return jsonify({"error": "No question provided"}), 400

#     try:
#         # Log question for debugging
#         current_app.logger.info(f"Processing question for chatbot {chatbot_id}: {question}")

#         # Get relevant context passages instead of loading all data
#         relevant_passages = get_relevant_context_for_chatbot(chatbot, question)

#         # Generate answer using only relevant passages
#         answer = generate_answer(question, relevant_passages)

#         # Calculate processing time
#         processing_time = time.time() - start_time

#         # Track analytics
#         analytics_data = {
#             "question": question,
#             "answer": answer,
#             "question_metadata": {
#                 "processing_time": processing_time,
#                 "context_passages_count": len(relevant_passages),
#                 "keywords_matched": extract_keywords(question)
#             }
#         }
#         track_question_helper(chatbot_id, analytics_data)

#         return jsonify({
#             "question": question,
#             "answer": answer,
#             "processing_time": round(processing_time, 3)
#         })

#     except Exception as e:
#         current_app.logger.error(f"Error in chatbot_ask: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

#----------------------------------------------------------------

@chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
def chatbot_ask(chatbot_id):
    start_time = time.time()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    data = request.json
    question = data.get('question')
    conversation_id = data.get('conversation_id')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Create a new conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    try:
        # Get conversation history for context - more efficiently
        conversation_history = []

        # Only retrieve conversation history if we have a valid conversation ID
        # and it's not a new conversation
        if conversation_id and len(conversation_id) > 10:  # Basic validation
            # Use a more efficient query with limit and proper ordering
            # Get only the last 3 exchanges (6 messages) to keep context manageable
            previous_messages = ConversationMessage.query.filter_by(
                conversation_id=conversation_id,
                chatbot_id=chatbot_id
            ).order_by(ConversationMessage.timestamp.desc()).limit(6).all()

            # Format conversation history for the AI - in chronological order
            if previous_messages:
                for msg in reversed(previous_messages):  # Reverse to get chronological order
                    conversation_history.append({"role": "user", "content": msg.message})
                    conversation_history.append({"role": "assistant", "content": msg.response})

        # Use the enhanced context-based answer generation
        answer = get_enhanced_answer(chatbot.data, question, chatbot_id, conversation_history)

        # Save the conversation message
        try:
            new_message = ConversationMessage(
                conversation_id=conversation_id,
                chatbot_id=chatbot_id,
                message=question,
                response=answer
            )
            db.session.add(new_message)
            db.session.commit()
        except SQLAlchemyError as db_error:
            # Log the error but don't fail the request
            current_app.logger.error(f"Database error saving conversation: {str(db_error)}")
            db.session.rollback()
            # Continue processing without failing

        # Track analytics asynchronously if possible
        try:
            processing_time = time.time() - start_time
            track_question_helper(chatbot_id, {
                "question": question,
                "answer": answer,
                "question_metadata": {"processing_time": processing_time}
            })
        except Exception as analytics_error:
            # Log but don't fail the request
            current_app.logger.error(f"Error tracking analytics: {str(analytics_error)}")

        return jsonify({
            "question": question,
            "answer": answer,
            "conversation_id": conversation_id,
            "processing_time": round(time.time() - start_time, 3)
        })
    except Exception as e:
        current_app.logger.error(f"Error in chatbot_ask: {str(e)}")
        return jsonify({
            "question": question,
            "answer": "I apologize, but I ran into an issue while processing your question. Please try again later.",
            "conversation_id": conversation_id,
            "processing_time": round(time.time() - start_time, 3)
        })



# @chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
# def chatbot_ask(chatbot_id):
#     start_time = time.time()  # Start timing the request

#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     if request.content_type == 'application/json':
#         # Handle JSON input
#         data = request.json
#         question = data.get('question')
#     else:
#         return jsonify({"error": "Unsupported content type"}), 415

#     if not question:
#         return jsonify({"error": "No question provided"}), 400

#     try:
#         chatbot_data_str = chatbot.data if isinstance(chatbot.data, str) else json.dumps(chatbot.data)
#         chatbot_data = json.loads(chatbot_data_str)
#         print(f"chatbot_data:) : {chatbot_data}")

#         current_app.logger.debug(f"Chatbot data type: {type(chatbot_data)}")
#         current_app.logger.debug(f"Chatbot data: {chatbot_data}")

#         if isinstance(chatbot_data, list):
#             if len(chatbot_data) > 0:
#                 chatbot_data = chatbot_data[-1]
#             else:
#                 raise ValueError("Chatbot data list is empty")
#         elif not isinstance(chatbot_data, dict):
#             raise ValueError(f"Invalid chatbot data format: {type(chatbot_data)}")

#         current_app.logger.debug(f"Processed chatbot data type: {type(chatbot_data)}")
#         current_app.logger.debug(f"Processed chatbot data: {chatbot_data}")

#         answer = get_general_answer(json.dumps(chatbot_data), question)

#         # Calculate processing time
#         processing_time = time.time() - start_time

#         # Track analytics
#         analytics_data = {
#             "question": question,
#             "answer": answer,
#             "question_metadata": {
#                 "processing_time": processing_time,
#                 "keywords_matched": [
#                     keyword for keyword in ["proce", "inventory", "stock", "available", "category", "type"]
#                     if keyword in question.lower()
#                 ]
#             }
#         }
#         track_question_helper(chatbot_id, analytics_data)

#         return jsonify({
#             "question": question,
#             "answer": answer,
#             "processing_time": round(processing_time, 3)
#         })

#     except json.JSONDecodeError as e:
#         current_app.logger.error(f"JSON decode error: {str(e)}")
#         return jsonify({"error": "Invalid chatbot data format"}), 500
#     except ValueError as e:
#         current_app.logger.error(f"Value error: {str(e)}")
#         return jsonify({"error": str(e)}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error in chatbot_ask: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500



# @chatbot_bp.route('/chatbot/<chatbot_id>/ask', methods=['POST'])
# def chatbot_ask(chatbot_id):
#     from models import Chatbot  # Import here or at top as per your setup
#     from extensions import db

#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     if request.content_type != 'application/json':
#         return jsonify({"error": "Unsupported content type"}), 415

#     data = request.json
#     question = data.get('question')
#     if not question:
#         return jsonify({"error": "No question provided"}), 400

#     try:
#         # Prepare data for NLP service
#         chatbot_data = chatbot.data if isinstance(chatbot.data, str) else json.dumps(chatbot.data)

#         # print(f'chatbot_data: {chatbot_data}')
#         # Call NLP service
#         nlp_response = requests.post(
#             f"{NLP_SERVICE_URL}/generate_answer",
#             json={"data": chatbot_data, "question": question},
#             timeout=15  # Add timeout to prevent hanging
#         )
#         nlp_response.raise_for_status()  # Raise exception for bad status codes

#         answer = nlp_response.json().get("answer")

#         return jsonify({
#             "question": question,
#             "answer": answer
#         })

#     except requests.exceptions.RequestException as e:
#         current_app.logger.error(f"Error calling NLP service: {str(e)}")
#         return jsonify({"error": "Failed to process question"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error in chatbot_ask: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500





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
            created_at=datetime.now(datetime.timezone.utc)
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




# @chatbot_bp.route('/get_chatbot_script/<chatbot_id>')
# @login_required
# @handle_errors
# def get_chatbot_script(chatbot_id):
#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     # Generate URLs for the API endpoints
#     ask_url = url_for('chatbot.chatbot_ask', chatbot_id=chatbot_id, _external=True)
#     feedback_url = url_for('chatbot.submit_feedback', chatbot_id=chatbot_id, _external=True)
#     sentiment_url = url_for('analytics.submit_sentiment', chatbot_id=chatbot_id, _external=True)
#     widget_url = url_for('static', filename='js/widget.js', _external=True)
#     ticket_url = url_for('chatbot.create_ticket', chatbot_id=chatbot_id, _external=True)
#     theme_color = ""
#     avatar = ""
#     escalate_url=url_for('chatbot.create_escalation', chatbot_id=chatbot_id, _external=True)

#     integration_code = f'''<!-- you can change the color of the theme used in this chat toggle to be integrated into your website with hexadecimal color -->
#     <!-- you can also change the default image of the avatar used in the chatbot widget by changing the data-avatar variable an image   -->
#     <script
#         src="{widget_url}"
#         data-chatbot-id="{chatbot_id}"
#         data-name="{chatbot.name}"
#         data-ask-url="{ask_url}"
#         data-feedback-url="{feedback_url}"
#         data-sentiment-url="{sentiment_url}"
#         data-ticket-url="{ticket_url}"
#         data-theme-color="{theme_color}"
#         data-avatar="{avatar}"
#         data-escalate-url="{escalate_url}"
#     ></script>'''

#     return jsonify({
#         'integration_code': integration_code,
#         'preview': integration_code
#     })

# @chatbot_bp.route('/get_chatbot_script/<chatbot_id>')
# @login_required
# @handle_errors
# def get_chatbot_script(chatbot_id):
#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     # Get customization settings
#     customization = {"theme_color": "", "avatar_url": ""}
#     if chatbot.data:
#         try:
#             chatbot_data = json.loads(chatbot.data) if isinstance(chatbot.data, str) else chatbot.data
#             if isinstance(chatbot_data, list) and chatbot_data:
#                 chatbot_data = chatbot_data[-1]
#             if isinstance(chatbot_data, dict):
#                 stored_custom = chatbot_data.get('customization', {})
#                 customization.update(stored_custom)
#         except json.JSONDecodeError:
#             pass

#     # Generate compact script
#     script = f'''<script src="{url_for('static',filename='js/widget.js',_external=True)}"data-id="{chatbot_id}"data-name="{chatbot.name}"data-theme="{customization['theme_color']}"data-avatar="{customization['avatar_url']}"data-api="{request.url_root}"></script>'''

#     return jsonify({
#         'integration_code': script,
#         'preview': script
#     })



# @chatbot_bp.route('/get_chatbot_script/<chatbot_id>')
# @login_required
# @handle_errors
# def get_chatbot_script(chatbot_id):
#     chatbot = Chatbot.query.get(chatbot_id)
#     if not chatbot:
#         return jsonify({"error": "Chatbot not found"}), 404

#     # Get customization settings with defaults
#     customization = {
#         "theme_color": "",
#         "avatar_url": "",
#         "pusher_key": "43bd6f1835e5bb8165d8",  # Add default for pusher_key
#         "pusher_cluster": "us3"  # Add default for pusher_cluster
#     }
#     if chatbot.data:
#         try:
#             chatbot_data = json.loads(chatbot.data) if isinstance(chatbot.data, str) else chatbot.data
#             if isinstance(chatbot_data, list) and chatbot_data:
#                 chatbot_data = chatbot_data[-1]
#             if isinstance(chatbot_data, dict):
#                 stored_custom = chatbot_data.get('customization', {})
#                 customization.update(stored_custom)
#         except json.JSONDecodeError:
#             pass

#     # Generate compact script with Pusher key and cluster
#     script = (
#         f'''<script src="{url_for('static', filename='js/widget.js', _external=True)}" data-id="{chatbot_id}" data-name="{chatbot.name}" data-theme="{customization['theme_color']}" data-avatar="{customization['avatar_url']}" data-api="{request.url_root}" data-pusher-key="{customization['pusher_key']}" data-pusher-cluster="{customization['pusher_cluster']}"></script>'''
#     )

#     return jsonify({
#         'integration_code': script,
#         'preview': script
#     })



@chatbot_bp.route('/get_chatbot_script/<chatbot_id>', methods=['GET'])
@cross_origin(supports_credentials=False, origins='*')
@handle_errors
def get_chatbot_script(chatbot_id):
    # Log the request for debugging
    current_app.logger.info(f"Get chatbot script called for chatbot: {chatbot_id}")
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

    # Get the base URL
    base_url = request.url_root

    # Only force HTTPS if not localhost
    if base_url.startswith('http://') and not ('localhost' in base_url or '127.0.0.1' in base_url):
        base_url = base_url.replace('http://', 'https://')

    # Ensure the URL ends with a slash
    if not base_url.endswith('/'):
        base_url += '/'

    # Log the URL for debugging
    current_app.logger.info(f"Widget base URL: {base_url}")

    # Create the script tag with all necessary attributes
    # Don't force HTTPS for localhost development
    scheme = None if 'localhost' in base_url or '127.0.0.1' in base_url else 'https'

    # Get the full URL for the widget.js file
    widget_url = url_for('static', filename='js/widget.js', _external=True, _scheme=scheme)

    # Log the widget URL for debugging
    current_app.logger.info(f"Widget URL: {widget_url}")

    script = (
        f'''<script src="{widget_url}" data-id="{chatbot_id}" data-name="{chatbot.name}" data-theme="{customization['theme_color']}" data-avatar="{customization['avatar_url']}" data-api="{base_url}" data-enable-leads="true"></script>'''
    )

    # Log the generated script for debugging
    current_app.logger.info(f"Generated script: {script}")

    # Return the integration code in the expected format
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



# @chatbot_bp.route('/escalate', methods=['POST'])
# @cross_origin()
# def create_escalation():
#     try:
#         # Validate request
#         if not request.is_json:
#             return jsonify({"error": "Request must be JSON"}), 400

#         data = request.get_json()
#         chatbot_id = data.get('chatbot_id')
#         user_id = request.headers.get('User-ID', '4269')

#         # Validate chatbot_id
#         if not chatbot_id:
#             return jsonify({"error": "Missing chatbot_id"}), 400

#         # Check if chatbot exists
#         chatbot = Chatbot.query.get(chatbot_id)
#         if not chatbot:
#             return jsonify({"error": "Chatbot not found"}), 404

#         # Check for existing active escalation
#         existing_escalation = Escalation.query.filter_by(
#             chatbot_id=chatbot_id,
#             user_id=user_id,
#             status='pending'
#         ).first()

#         if existing_escalation:
#             return jsonify({
#                 "escalation_id": existing_escalation.id,
#                 "status": "existing",
#                 "status_url": f"/escalation/{existing_escalation.id}/status",
#                 "send_url": f"/escalation/{existing_escalation.id}/send",
#                 "messages_url": f"/escalation/{existing_escalation.id}/messages"
#             }), 200

#         # Create new escalation
#         escalation = Escalation(
#             chatbot_id=chatbot_id,
#             user_id=user_id,
#             status='pending',
#             created_at=datetime.utcnow()
#         )

#         db.session.add(escalation)
#         db.session.commit()

#         # Return success with URLs
#         return jsonify({
#             "escalation_id": escalation.id,
#             "status": "created",
#             "status_url": f"/escalation/{escalation.id}/status",
#             "send_url": f"/escalation/{escalation.id}/send",
#             "messages_url": f"/escalation/{escalation.id}/messages"
#         }), 201

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in escalation: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Escalation error: {str(e)}")
#         return jsonify({"error": "Internal server error"}), 500




# @chatbot_bp.route('/escalation/<escalation_id>/messages', methods=['GET'])
# def get_messages(escalation_id):
#     last_id = request.args.get('last_id', 0)
#     messages = EscalationMessage.query.filter(
#         EscalationMessage.escalation_id == escalation_id,
#         EscalationMessage.id > last_id
#     ).order_by(EscalationMessage.id.asc()).all()

#     return jsonify([{
#         "id": msg.id,
#         "sender": "agent" if msg.sender_id == 0 else "user",
#         "message": msg.message,
#         "timestamp": msg.timestamp.isoformat()
#     } for msg in messages]), 200


# @chatbot_bp.route('/escalation/<escalation_id>/send', methods=['POST'])
# def send_message(escalation_id):
#     data = request.json
#     message = data.get('message')
#     user_id = request.headers.get('User-ID', '4269')

#     escalation = Escalation.query.get(escalation_id)
#     if not escalation:
#         return jsonify({"error": "Escalation not found"}), 404

#     sender_id = user_id if escalation.user_id == user_id else 0  # 0 represents agent

#     new_message = EscalationMessage(
#         escalation_id=escalation_id,
#         sender_id=sender_id,
#         message=message
#     )
#     db.session.add(new_message)

#     if escalation.status == 'pending':
#         escalation.status = 'in_progress'

#     db.session.commit()

#     return jsonify({"status": "success"}), 200


# @chatbot_bp.route('/escalation/<escalation_id>/status', methods=['GET'])
# def check_escalation_status(escalation_id):
#     escalation = Escalation.query.get(escalation_id)
#     if not escalation:
#         return jsonify({"error": "Escalation not found"}), 404

#     return jsonify({
#         "status": escalation.status,
#         "agent_joined": escalation.agent_id is not None
#     }), 200

# @chatbot_bp.route('/agent/escalations', methods=['GET'])
# def get_pending_escalations():
#     escalations = Escalation.query.filter_by(status='pending').all()
#     return jsonify([{
#         "id": esc.id,
#         "chatbot_id": esc.chatbot_id,
#         "user_id": esc.user_id,
#         "created_at": esc.created_at.isoformat()
#     } for esc in escalations]), 200

# @chatbot_bp.route('/agent/escalation/<escalation_id>/join', methods=['POST'])
# def join_escalation(escalation_id):
#     escalation = Escalation.query.get(escalation_id)
#     if not escalation:
#         return jsonify({"error": "Escalation not found"}), 404

#     escalation.status = 'in_progress'
#     escalation.agent_id = 0  # Replace with actual agent ID from session
#     db.session.commit()

#     return jsonify({"message": "Escalation joined successfully"}), 200




# @chatbot_bp.route('/escalation/<escalation_id>/events', methods=['GET'])
# def escalation_events(escalation_id):
#     def event_stream():
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             yield "data: Escalation not found\n\n"
#             return

#         last_id = request.args.get('last_id', 0)
#         while True:
#             # Check for new messages
#             messages = EscalationMessage.query.filter(
#                 EscalationMessage.escalation_id == escalation_id,
#                 EscalationMessage.id > last_id
#             ).order_by(EscalationMessage.id.asc()).all()

#             for message in messages:
#                 yield f"""data: {json.dumps({
#                     'id': message.id,
#                     'sender': 'agent' if message.sender_id == 0 else 'user',
#                     'message': message.message,
#                     'timestamp': message.timestamp.isoformat()
#                 })}\n\n"""
#                 last_id = message.id

#             # Check for status changes
#             escalation = Escalation.query.get(escalation_id)
#             if escalation.status == 'in_progress' and escalation.agent_id is not None:
#                 yield f"""data: {json.dumps({
#                     'type': 'status',
#                     'status': escalation.status,
#                     'agent_joined': True
#                 })}\n\n"""

#             time.sleep(1)  # Adjust the sleep time as needed

#     return Response(stream_with_context(event_stream()), content_type='text/event-stream')





from flask import Blueprint, request, jsonify
from models import Chatbot
from extensions import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import json

# Live chat feature has been removed

# Add a route to handle the escalation endpoint that's still being called
@chatbot_bp.route('/agent/escalations/<chatbot_id>', methods=['GET'])
def handle_removed_escalation(chatbot_id):
    # Log the request for debugging
    current_app.logger.info(f"Escalation endpoint called for chatbot: {chatbot_id}")
    return jsonify({
        "message": "Escalation feature has been removed",
        "status": "disabled"
    }), 200

# CSS is now embedded directly in the widget.js file
# No need for separate CSS endpoints



# @chatbot_bp.route('/escalate', methods=['POST'])
# @cross_origin()
# def create_escalation():
#     try:
#         # Validate request
#         if not request.is_json:
#             return jsonify({"error": "Request must be JSON"}), 400

#         data = request.get_json()
#         chatbot_id = data.get('chatbot_id')
#         user_id = request.headers.get('User-ID', '4269')

#         # Validate chatbot_id
#         if not chatbot_id:
#             return jsonify({"error": "Missing chatbot_id"}), 400

#         # Check if chatbot exists
#         chatbot = Chatbot.query.get(chatbot_id)
#         if not chatbot:
#             return jsonify({"error": "Chatbot not found"}), 404

#         # Check for existing active escalation
#         existing_escalation = Escalation.query.filter_by(
#             chatbot_id=chatbot_id,
#             user_id=user_id,
#             status='pending'
#         ).first()

#         if existing_escalation:
#             return jsonify({
#                 "escalation_id": existing_escalation.id,
#                 "status": "existing",
#                 "status_url": f"/escalation/{existing_escalation.id}/status",
#                 "send_url": f"/escalation/{existing_escalation.id}/send",
#                 "messages_url": f"/escalation/{existing_escalation.id}/messages"
#             }), 200

#         # Create new escalation
#         escalation = Escalation(
#             chatbot_id=chatbot_id,
#             user_id=user_id,
#             status='pending',
#             created_at=datetime.utcnow()
#         )

#         db.session.add(escalation)
#         db.session.commit()

#         # Return success with URLs
#         return jsonify({
#             "escalation_id": escalation.id,
#             "status": "created",
#             "status_url": f"/escalation/{escalation.id}/status",
#             "send_url": f"/escalation/{escalation.id}/send",
#             "messages_url": f"/escalation/{escalation.id}/messages"
#         }), 201

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in escalation: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Escalation error: {str(e)}")
#         return jsonify({"error": "Internal server error"}), 500




# Live chat feature has been removed


# @chatbot_bp.route('/escalation/<escalation_id>/messages', methods=['GET'])
# def get_messages(escalation_id):
#     try:
#         last_id = request.args.get('last_id', 0, type=int)
#
#         # Use context manager for database session
#         with db.session() as session:
#             messages = session.query(EscalationMessage).filter(
#                 EscalationMessage.escalation_id == escalation_id,
#                 EscalationMessage.id > last_id
#             ).order_by(EscalationMessage.id.asc()).all()
#
#             return jsonify([{
#                 "id": msg.id,
#                 "sender": "agent" if msg.sender_id == 0 else "user",
#                 "message": msg.message,
#                 "timestamp": msg.timestamp.isoformat()
#             } for msg in messages]), 200
#
#     except Exception as e:
#         current_app.logger.error(f"Error fetching messages: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500




# @chatbot_bp.route('/escalation/<escalation_id>/send', methods=['POST'])
# def send_message(escalation_id):
#     try:
#         data = request.json
#         message = data.get('message')
#         user_id = request.headers.get('User-ID', '4269')

#         if not message:
#             return jsonify({"error": "Message is required"}), 400

#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404

#         sender_id = user_id if escalation.user_id == user_id else 0  # 0 represents agent

#         new_message = EscalationMessage(
#             escalation_id=escalation_id,
#             sender_id=sender_id,
#             message=message
#         )
#         db.session.add(new_message)

#         # if escalation.status == 'pending':
#         #     escalation.status = 'in_progress'

#         db.session.commit()

#         return jsonify({"status": "success"}), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in send_message: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error sending message: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/escalation/<escalation_id>/send', methods=['POST'])
# def send_message(escalation_id):
#     try:
#         data = request.json
#         message = data.get('message')
#         user_id = request.headers.get('User-ID', '4269')

#         if not message:
#             return jsonify({"error": "Message is required"}), 400

#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404

#         sender_id = user_id if escalation.user_id == user_id else 0  # 0 represents agent

#         new_message = EscalationMessage(
#             escalation_id=escalation_id,
#             sender_id=sender_id,
#             message=message
#         )
#         db.session.add(new_message)

#         if escalation.status == 'pending':
#             escalation.status = 'in_progress'

#         db.session.commit()

#         # Publish new message event
#         pusher_client.trigger(
#             f'escalation-{escalation_id}',
#             'new-message',
#             {
#                 'type': 'message',
#                 'id': new_message.id,
#                 'sender': 'agent' if sender_id == 0 else 'user',
#                 'message': message,
#                 'timestamp': new_message.timestamp.isoformat()
#             }
#         )

#         # Publish status update if changed
#         if escalation.status == 'in_progress':
#             pusher_client.trigger(
#                 f'escalation-{escalation_id}',
#                 'status-update',
#                 {
#                     'type': 'status',
#                     'status': escalation.status,
#                     'agent_joined': escalation.agent_id is not None
#                 }
#             )

#         return jsonify({"status": "success"}), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in send_message: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error sending message: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

# @chatbot_bp.route('/escalation/<escalation_id>/send', methods=['POST'])
# def send_message(escalation_id):
#     try:
#         data = request.json
#         message = data.get('message')
#         user_id_str = request.headers.get('User-ID', '4269')  # String from header
#
#         if not message:
#             return jsonify({"error": "Message is required"}), 400
#
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404
#
#         # Convert user_id to integer
#         try:
#             user_id = int(user_id_str)
#         except ValueError:
#             user_id = 4269  # Fallback if invalid
#
#         # Determine sender (0 for agent, user_id for user)
#         sender_id = user_id if escalation.user_id == user_id else 0
#
#         new_message = EscalationMessage(
#             escalation_id=escalation_id,
#             sender_id=sender_id,
#             message=message
#         )
#         db.session.add(new_message)
#
#         if escalation.status == 'pending':
#             escalation.status = 'in_progress'
#
#         db.session.commit()
#
#         # Publish new message event with explicit sender
#         pusher_client.trigger(
#             f'escalation-{escalation_id}',
#             'new-message',
#             {
#                 'type': 'message',
#                 'id': new_message.id,
#                 'sender': 'agent' if sender_id == 0 else 'user',
#                 'message': message,
#                 'timestamp': new_message.timestamp.isoformat()
#             }
#         )
#
#         # Publish status update if changed
#         if escalation.status == 'in_progress':
#             pusher_client.trigger(
#                 f'escalation-{escalation_id}',
#                 'status-update',
#                 {
#                     'type': 'status',
#                     'status': escalation.status,
#                     'agent_joined': escalation.agent_id is not None
#                 }
#             )
#
#         return jsonify({"status": "success"}), 200
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in send_message: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error sending message: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500



# @chatbot_bp.route('/escalation/<escalation_id>/status', methods=['GET'])
# def check_escalation_status(escalation_id):
#     try:
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404
#
#         return jsonify({
#             "status": escalation.status,
#             "agent_joined": escalation.agent_id is not None
#         }), 200
#
#     except Exception as e:
#         current_app.logger.error(f"Error checking escalation status: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/agent/escalations', methods=['GET'])
# def get_pending_escalations():
#     try:
#         escalations = Escalation.query.filter_by(status='pending').all()
#         return jsonify([{
#             "id": esc.id,
#             "chatbot_id": esc.chatbot_id,
#             "user_id": esc.user_id,
#             "created_at": esc.created_at.isoformat()
#         } for esc in escalations]), 200

#     except Exception as e:
#         current_app.logger.error(f"Error fetching pending escalations: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/agent/escalations<chatbot_id>', methods=['GET'])
# def get_pending_escalations():
#     try:
#         # Fetch escalations with status 'pending' or 'in_progress'
#         escalations = Escalation.query.filter(
#             Escalation.status.in_(['pending', 'in_progress'])
#         ).order_by(desc(Escalation.created_at)).all()

#         # Prepare the response data
#         escalations_data = [{
#             "id": esc.id,
#             "chatbot_id": esc.chatbot_id,
#             "user_id": esc.user_id,
#             "status": esc.status,
#             "created_at": esc.created_at.isoformat()
#         } for esc in escalations]

#         # Disable caching to ensure fresh data
#         response = jsonify(escalations_data)
#         response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#         response.headers['Pragma'] = 'no-cache'
#         response.headers['Expires'] = '0'

#         return response, 200

#     except Exception as e:
#         current_app.logger.error(f"Error fetching escalations: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

# @chatbot_bp.route('/agent/escalations/<chatbot_id>', methods=['GET'])
# def get_chatbot_escalations(chatbot_id):
#     try:
#         # Verify chatbot exists
#         chatbot = Chatbot.query.get(chatbot_id)
#         if not chatbot:
#             return jsonify({"error": "Chatbot not found"}), 404
#
#         # Fetch escalations with status 'pending' or 'in_progress' for specific chatbot
#         escalations = Escalation.query.filter(
#             (Escalation.chatbot_id == chatbot_id) &
#             (Escalation.status.in_(['pending', 'in_progress', 'resolved', 'closed']))
#         ).order_by(desc(Escalation.created_at)).all()
#
#         # Prepare the response data
#         escalations_data = [{
#             "id": esc.id,
#             "chatbot_id": esc.chatbot_id,
#             "user_id": esc.user_id,
#             "status": esc.status,
#             "created_at": esc.created_at.isoformat(),
#             "messages_count": EscalationMessage.query.filter_by(escalation_id=esc.id).count()
#         } for esc in escalations]
#
#         # Disable caching to ensure fresh data
#         response = jsonify({
#             "chatbot_name": chatbot.name,
#             "total_escalations": len(escalations_data),
#             "escalations": escalations_data
#         })
#         response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#         response.headers['Pragma'] = 'no-cache'
#         response.headers['Expires'] = '0'
#
#         return response, 200
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in get_chatbot_escalations: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error fetching escalations: {str(e)}")
#         return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500





# @chatbot_bp.route('/agent/escalation/<escalation_id>/join', methods=['POST'])
# def join_escalation(escalation_id):
#     try:
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404

#         escalation.status = 'in_progress'
#         escalation.agent_id = 0  # Replace with actual agent ID from session
#         db.session.commit()

#         return jsonify({"message": "Escalation joined successfully"}), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in join_escalation: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error joining escalation: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/agent/escalation/<escalation_id>/join', methods=['POST'])
# def join_escalation(escalation_id):
#     try:
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404
#
#         escalation.status = 'in_progress'
#         escalation.agent_id = 0  # Replace with actual agent ID from session
#         db.session.commit()
#
#         # Publish status update
#         pusher_client.trigger(
#             f'escalation-{escalation_id}',
#             'status-update',
#             {
#                 'type': 'status',
#                 'status': escalation.status,
#                 'agent_joined': True
#             }
#         )
#
#         return jsonify({"message": "Escalation joined successfully"}), 200
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in join_escalation: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error joining escalation: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/escalation/<escalation_id>/events', methods=['GET'])
# def escalation_events(escalation_id):
#     def event_stream():
#         try:
#             escalation = Escalation.query.get(escalation_id)
#             if not escalation:
#                 yield "data: Escalation not found\n\n"
#                 return

#             last_id = request.args.get('last_id', 0, type=int)
#             last_status = None  # Add this to track status changes

#             while True:
#                 # Check for new messages
#                 messages = EscalationMessage.query.filter(
#                     EscalationMessage.escalation_id == escalation_id,
#                     EscalationMessage.id > last_id
#                 ).order_by(EscalationMessage.id.asc()).all()

#                 for message in messages:
#                     yield f"""data: {json.dumps({
#                         'type': 'message',
#                         'id': message.id,
#                         'sender': 'agent' if message.sender_id == 0 else 'user',
#                         'message': message.message,
#                         'timestamp': message.timestamp.isoformat()
#                     })}\n\n"""
#                     last_id = message.id

#                 # Check for status changes
#                 escalation = Escalation.query.get(escalation_id)

#                 if (escalation.status in ['in_progress', 'pending']):
#                     if escalation.status != last_status:  # Only send if status changed
#                         print(f"Status update triggered: {escalation.status}")
#                         yield f"""data: {json.dumps({
#                             'type': 'status',
#                             'status': escalation.status,
#                             'agent_joined': True
#                         })}\n\n"""
#                         last_status = escalation.status

#                 time.sleep(1)

#         except Exception as e:
#             current_app.logger.error(f"Error in event_stream: {str(e)}")
#             yield "data: An error occurred\n\n"

#     return Response(stream_with_context(event_stream()), content_type='text/event-stream')





# Removed unused imports

# @chatbot_bp.route('/escalation/<escalation_id>/events', methods=['GET'])
# def escalation_events(escalation_id):
#     def event_stream():
#         try:
#             escalation = Escalation.query.get(escalation_id)
#             if not escalation:
#                 yield "data: Escalation not found\n\n"
#                 return

#             last_id = request.args.get('last_id', 0, type=int)
#             last_status = None  # Add this to track status changes

#             while True:
#                 # Check for new messages
#                 messages = EscalationMessage.query.filter(
#                     EscalationMessage.escalation_id == escalation_id,
#                     EscalationMessage.id > last_id
#                 ).order_by(EscalationMessage.id.asc()).all()

#                 for message in messages:
#                     yield f"""data: {json.dumps({
#                         'type': 'message',
#                         'id': message.id,
#                         'sender': 'agent' if message.sender_id == 0 else 'user',
#                         'message': message.message,
#                         'timestamp': message.timestamp.isoformat()
#                     })}\n\n"""
#                     last_id = message.id

#                 # Check for status changes
#                 escalation = Escalation.query.get(escalation_id)

#                 if (escalation.status in ['in_progress', 'pending']):
#                     if escalation.status != last_status:  # Only send if status changed
#                         print(f"Status update triggered: {escalation.status}")
#                         yield f"""data: {json.dumps({
#                             'type': 'status',
#                             'status': escalation.status,
#                             'agent_joined': True
#                         })}\n\n"""
#                         last_status = escalation.status

#                 time.sleep(1)

#         except Exception as e:
#             current_app.logger.error(f"Error in event_stream: {str(e)}")
#             yield "data: An error occurred\n\n"

#     return Response(stream_with_context(event_stream()), content_type='text/event-stream')


# @chatbot_bp.route('/escalation/<escalation_id>/events', methods=['GET'])
# def escalation_events(escalation_id):
#     def event_stream():
#         session = None
#         try:
#             # Create a new session using the session factory
#             session = db.session()  # Changed from create_scoped_session()

#             escalation = session.query(Escalation).get(escalation_id)
#             if not escalation:
#                 yield "data: Escalation not found\n\n"
#                 return

#             last_id = request.args.get('last_id', 0, type=int)
#             last_status = None

#             while True:
#                 try:
#                     # Query with the session
#                     messages = session.query(EscalationMessage).filter(
#                         EscalationMessage.escalation_id == escalation_id,
#                         EscalationMessage.id > last_id
#                     ).order_by(EscalationMessage.id.asc()).all()

#                     for message in messages:
#                         yield f"""data: {json.dumps({
#                             'type': 'message',
#                             'id': message.id,
#                             'sender': 'agent' if message.sender_id == 0 else 'user',
#                             'message': message.message,
#                             'timestamp': message.timestamp.isoformat()
#                         })}\n\n"""
#                         last_id = message.id

#                     # Refresh escalation object
#                     session.refresh(escalation)

#                     if escalation.status in ['in_progress']:
#                         if escalation.status != last_status:
#                             yield f"""data: {json.dumps({
#                                 'type': 'status',
#                                 'status': escalation.status,
#                                 'agent_joined': True
#                             })}\n\n"""
#                             last_status = escalation.status

#                     # Explicitly commit
#                     session.commit()

#                     time.sleep(1)

#                 except Exception as e:
#                     if session:
#                         session.rollback()
#                     current_app.logger.error(f"Error in event stream loop: {str(e)}")
#                     continue

#         except Exception as e:
#             current_app.logger.error(f"Error in event_stream: {str(e)}")
#             yield "data: An error occurred\n\n"
#         finally:
#             if session:
#                 session.close()

#     return Response(
#         stream_with_context(event_stream()),
#         content_type='text/event-stream',
#         headers={
#             'Cache-Control': 'no-cache',
#             'Connection': 'keep-alive',
#             'X-Accel-Buffering': 'no'
#         }
#     )


# @chatbot_bp.route('/escalation/<escalation_id>', methods=['DELETE'])
# def delete_escalation(escalation_id):
#     try:
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404
#
#         db.session.delete(escalation)
#         db.session.commit()
#
#         return jsonify({"message": "Escalation deleted successfully"}), 200
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in delete_escalation: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error in delete_escalation: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500


# @chatbot_bp.route('/escalation/<escalation_id>/status', methods=['PUT'])
# def update_escalation_status(escalation_id):
#     try:
#         # Validate request
#         if not request.is_json:
#             return jsonify({"error": "Request must be JSON"}), 400

#         data = request.get_json()
#         new_status = data.get('status')

#         # Validate status
#         if new_status not in ['resolved', 'closed']:
#             return jsonify({"error": "Invalid status. Must be 'resolved' or 'closed'"}), 400

#         # Check if escalation exists
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404

#         # Update status
#         escalation.status = new_status
#         db.session.commit()

#         return jsonify({
#             "escalation_id": escalation.id,
#             "status": escalation.status,
#             "message": f"Escalation status updated to {new_status}"
#         }), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in update_escalation_status: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error updating escalation status: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

# @chatbot_bp.route('/escalation/<escalation_id>/status', methods=['PUT'])
# def update_escalation_status(escalation_id):
#     try:
#         if not request.is_json:
#             return jsonify({"error": "Request must be JSON"}), 400
#
#         data = request.get_json()
#         new_status = data.get('status')
#
#         if new_status not in ['resolved', 'closed']:
#             return jsonify({"error": "Invalid status. Must be 'resolved' or 'closed'"}), 400
#
#         escalation = Escalation.query.get(escalation_id)
#         if not escalation:
#             return jsonify({"error": "Escalation not found"}), 404
#
#         escalation.status = new_status
#         db.session.commit()
#
#         # Publish status update
#         pusher_client.trigger(
#             f'escalation-{escalation_id}',
#             'status-update',
#             {
#                 'type': 'status',
#                 'status': escalation.status,
#                 'agent_joined': escalation.agent_id is not None
#             }
#         )
#
#         return jsonify({
#             "escalation_id": escalation.id,
#             "status": escalation.status,
#             "message": f"Escalation status updated to {new_status}"
#         }), 200
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error in update_escalation_status: {str(e)}")
#         return jsonify({"error": "Database error occurred"}), 500
#     except Exception as e:
#         current_app.logger.error(f"Error updating escalation status: {str(e)}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

# @chatbot_bp.route('/agent/escalations/<chatbot_id>/events', methods=['GET'])
# def chatbot_escalations_events(chatbot_id):
#     def event_stream():
#         try:
#             # Verify chatbot exists
#             chatbot = Chatbot.query.get(chatbot_id)
#             if not chatbot:
#                 yield "data: {\"error\": \"Chatbot not found\"}\n\n"
#                 return

#             last_check = datetime.utcnow()

#             while True:
#                 # Fetch new or updated escalations since last check
#                 escalations = Escalation.query.filter(
#                     (Escalation.chatbot_id == chatbot_id) &
#                     (Escalation.updated_at >= last_check)
#                 ).all()

#                 if escalations:
#                     # Prepare escalations data
#                     escalations_data = [{
#                         "id": esc.id,
#                         "chatbot_id": esc.chatbot_id,
#                         "user_id": esc.user_id,
#                         "status": esc.status,
#                         "created_at": esc.created_at.isoformat(),
#                         "messages_count": EscalationMessage.query.filter_by(escalation_id=esc.id).count()
#                     } for esc in escalations]

#                     # Create the update event data
#                     event_data = {
#                         "type": "escalations_update",
#                         "escalations": escalations_data
#                     }

#                     # Properly format the SSE data
#                     message = "data: " + json.dumps(event_data) + "\n\n"
#                     yield message

#                     last_check = datetime.utcnow()

#                 time.sleep(2)  # Check every 2 seconds

#         except Exception as e:
#             current_app.logger.error(f"Error in escalations event stream: {str(e)}")
#             error_data = json.dumps({"error": str(e)})
#             yield f"data: {error_data}\n\n"

#     return Response(
#         stream_with_context(event_stream()),
#         mimetype='text/event-stream',
#         headers={
#             'Cache-Control': 'no-cache',
#             'Connection': 'keep-alive',
#             'X-Accel-Buffering': 'no'  # Added for Nginx compatibility
#         }
#     )

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
                chatbot_data = None

                # Handle string data
                if isinstance(chatbot.data, str):
                    chatbot_data = json.loads(chatbot.data)
                else:
                    chatbot_data = chatbot.data

                # Log the data for debugging
                current_app.logger.info(f"Chatbot data type: {type(chatbot_data)}")
                current_app.logger.info(f"Chatbot data: {chatbot_data}")

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
                        # Ensure we have proper types
                        if 'theme_color' in stored_customization:
                            customization['theme_color'] = str(stored_customization['theme_color'])
                        if 'avatar_url' in stored_customization:
                            customization['avatar_url'] = str(stored_customization['avatar_url']) if stored_customization['avatar_url'] else ""
                        if 'enable_tickets' in stored_customization:
                            customization['enable_tickets'] = bool(stored_customization['enable_tickets'])

            except json.JSONDecodeError as e:
                current_app.logger.error(f"Invalid JSON in chatbot data: {str(e)}")
                # Use default customization
            except Exception as e:
                current_app.logger.error(f"Error processing customization data: {str(e)}")
                # Use default customization

        current_app.logger.info(f"Returning customization: {customization}")
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
        current_app.logger.info(f"Received customization data: {data}")

        theme_color = data.get('theme_color')
        avatar_url = data.get('avatar_url', "")
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

        # Create a new customization object
        new_customization = {
            'theme_color': theme_color if theme_color else "#0084ff",
            'avatar_url': avatar_url,
            'enable_tickets': enable_tickets if enable_tickets is not None else True
        }

        # Create a new data object
        new_data = {'customization': new_customization}

        # Store the updated data as a JSON string
        chatbot.data = json.dumps(new_data)
        db.session.commit()

        current_app.logger.info(f"Saved customization: {new_customization}")

        return jsonify({
            "message": "Chatbot customization updated successfully",
            "customization": new_customization
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in customize_chatbot: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


import os
from werkzeug.utils import secure_filename
from PIL import Image

UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chatbot_bp.route('/chatbot/<chatbot_id>/upload-avatar', methods=['POST'])
@cross_origin(supports_credentials=True)
@handle_errors
def upload_avatar(chatbot_id):
    try:
        # Check if chatbot exists
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return jsonify({"error": "Chatbot not found"}), 404

        if 'avatar' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            try:
                # Create upload directory if it doesn't exist
                upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)

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
                filepath = os.path.join(upload_path, filename)

                # Save compressed image
                image.save(filepath, 'JPEG', quality=85, optimize=True)

                # Generate URL for the saved image
                avatar_url = url_for('static',
                                   filename=f'uploads/avatars/{filename}',
                                   _external=True)

                current_app.logger.info(f"Avatar saved to {filepath}")
                current_app.logger.info(f"Avatar URL: {avatar_url}")

                return jsonify({"avatar_url": avatar_url}), 200
            except Exception as e:
                current_app.logger.error(f"Error processing image: {str(e)}")
                return jsonify({"error": f"Failed to process image: {str(e)}"}), 500

        return jsonify({"error": "Invalid file type"}), 400

    except Exception as e:
        current_app.logger.error(f"Error uploading avatar: {str(e)}")
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


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
