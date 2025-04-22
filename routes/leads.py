from flask import Blueprint, request, jsonify, session, current_app
from models import Lead, Chatbot, User
from extensions import db
from datetime import datetime
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
import logging
from utils.auth_utils import login_required

leads_bp = Blueprint('leads', __name__)

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    return decorated_function

@leads_bp.route('/api/leads/submit', methods=['POST'])
@handle_errors
def submit_lead():
    """
    Submit a new lead from the chatbot interface
    """
    data = request.json

    # Validate required fields
    required_fields = ['name', 'email', 'chatbot_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Get the chatbot to verify it exists and get the owner
    chatbot = Chatbot.query.get(data['chatbot_id'])
    if not chatbot:
        return jsonify({"error": "Chatbot not found"}), 404

    # Create new lead
    try:
        new_lead = Lead(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            message=data.get('message'),
            chatbot_id=data['chatbot_id'],
            user_id=chatbot.user_id,  # Assign to the chatbot owner
            created_at=datetime.now(dt.timezone.utc),
            status='new',
            notes=None  # Explicitly set notes to None
        )
    except Exception as e:
        current_app.logger.error(f"Error creating lead with user_id: {str(e)}")
        # Try without user_id if it fails
        new_lead = Lead(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            message=data.get('message'),
            chatbot_id=data['chatbot_id'],
            created_at=datetime.now(dt.timezone.utc),
            status='new',
            notes=None  # Explicitly set notes to None
        )

    try:
        db.session.add(new_lead)
        db.session.commit()
        return jsonify({"message": "Lead submitted successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in submit_lead: {str(e)}")
        return jsonify({"error": "An error occurred while saving the lead"}), 500

@leads_bp.route('/api/leads', methods=['GET'])
@login_required
@handle_errors
def get_leads():
    """
    Get all leads for the current user
    """
    user_id = session.get('user_id')

    # Get query parameters for filtering
    chatbot_id = request.args.get('chatbot_id')
    status = request.args.get('status')

    # Base query - get leads for the current user
    # Use a raw SQL query to handle the case where user_id column might not exist
    try:
        query = Lead.query.filter(Lead.user_id == user_id)
    except Exception as e:
        current_app.logger.error(f"Error filtering by user_id: {str(e)}")
        # Fallback to getting all leads if user_id column doesn't exist
        query = Lead.query

    # Apply filters if provided
    if chatbot_id:
        query = query.filter_by(chatbot_id=chatbot_id)
    if status:
        query = query.filter_by(status=status)

    # Order by created_at descending (newest first)
    leads = query.order_by(Lead.created_at.desc()).all()

    # Format the leads for the response
    leads_data = []
    for lead in leads:
        leads_data.append({
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'message': lead.message,
            'chatbot_id': lead.chatbot_id,
            'created_at': lead.created_at.isoformat(),
            'status': lead.status,
            'notes': getattr(lead, 'notes', None)  # Safely get notes attribute
        })

    return jsonify(leads_data), 200

@leads_bp.route('/api/leads/<int:lead_id>', methods=['GET'])
@login_required
@handle_errors
def get_lead(lead_id):
    """
    Get a specific lead by ID
    """
    user_id = session.get('user_id')

    # Get the lead and verify ownership
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    # Check if lead has user_id and if it matches the current user
    try:
        if lead.user_id and lead.user_id != user_id:
            return jsonify({"error": "Unauthorized access to this lead"}), 403
    except Exception as e:
        current_app.logger.error(f"Error checking lead ownership: {str(e)}")
        # If there's an error (e.g., user_id column doesn't exist), skip the check

    # Format the lead for the response
    lead_data = {
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'message': lead.message,
        'chatbot_id': lead.chatbot_id,
        'created_at': lead.created_at.isoformat(),
        'status': lead.status,
        'notes': getattr(lead, 'notes', None)  # Safely get notes attribute
    }

    return jsonify(lead_data), 200

@leads_bp.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@login_required
@handle_errors
def update_lead(lead_id):
    """
    Update a lead's status or notes
    """
    user_id = session.get('user_id')
    data = request.json

    # Get the lead and verify ownership
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    # Check if lead has user_id and if it matches the current user
    try:
        if lead.user_id and lead.user_id != user_id:
            return jsonify({"error": "Unauthorized access to this lead"}), 403
    except Exception as e:
        current_app.logger.error(f"Error checking lead ownership: {str(e)}")
        # If there's an error (e.g., user_id column doesn't exist), skip the check

    # Update fields if provided
    if 'status' in data:
        lead.status = data['status']

    if 'notes' in data:
        try:
            lead.notes = data['notes']
        except AttributeError:
            current_app.logger.warning("Notes column does not exist in lead table")

    try:
        db.session.commit()
        return jsonify({"message": "Lead updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_lead: {str(e)}")
        return jsonify({"error": "An error occurred while updating the lead"}), 500

@leads_bp.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@login_required
@handle_errors
def delete_lead(lead_id):
    """
    Delete a lead
    """
    user_id = session.get('user_id')

    # Get the lead and verify ownership
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    # Check if lead has user_id and if it matches the current user
    try:
        if lead.user_id and lead.user_id != user_id:
            return jsonify({"error": "Unauthorized access to this lead"}), 403
    except Exception as e:
        current_app.logger.error(f"Error checking lead ownership: {str(e)}")
        # If there's an error (e.g., user_id column doesn't exist), skip the check

    try:
        db.session.delete(lead)
        db.session.commit()
        return jsonify({"message": "Lead deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_lead: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the lead"}), 500
