from flask import Blueprint, request, jsonify, session, current_app, url_for, redirect
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from functools import wraps
from models import GmailIntegration, Ticket
from extensions import db
import os
import json
from google.auth.transport.requests import Request

gmail_bp = Blueprint('gmail', __name__)

# Gmail API configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.compose']
CLIENT_SECRETS_FILE = "client.json"  # Update this path

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_gmail_service(user_id):
    gmail_integration = GmailIntegration.query.filter_by(user_id=user_id).first()
    if not gmail_integration:
        return None
    
    creds_dict = json.loads(gmail_integration.credentials)
    credentials = Credentials.from_authorized_user_info(creds_dict, SCOPES)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update stored credentials
            gmail_integration.credentials = json.dumps(credentials_to_dict(credentials))
            db.session.commit()
    
    return build('gmail', 'v1', credentials=credentials)

@gmail_bp.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('gmail.oauth2callback', _external=True)
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@gmail_bp.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('gmail.oauth2callback', _external=True)
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    
    # Store credentials in database
    user_id = session['user_id']
    gmail_integration = GmailIntegration.query.filter_by(user_id=user_id).first()
    
    if gmail_integration:
        gmail_integration.credentials = json.dumps(credentials_to_dict(credentials))
    else:
        gmail_integration = GmailIntegration(
            user_id=user_id,
            credentials=json.dumps(credentials_to_dict(credentials))
        )
        db.session.add(gmail_integration)
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@gmail_bp.route('/send-ticket-notification/<ticket_id>')
def send_ticket_notification(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user_id = session['user_id']
    
    service = get_gmail_service(user_id)
    if not service:
        return jsonify({"error": "Gmail service not authenticated"}), 401
    
    message = create_ticket_notification_email(ticket)
    
    try:
        message = (service.users().messages().send(userId='me', body=message)
                  .execute())
        return jsonify({"message": "Notification sent successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return jsonify({"error": "Failed to send notification"}), 500

@gmail_bp.route('/compose-email', methods=['POST'])
def compose_email():
    data = request.json
    user_id = session['user_id']
    
    if not all(k in data for k in ['to', 'subject', 'body']):
        return jsonify({"error": "Missing required fields"}), 400
    
    service = get_gmail_service(user_id)
    if not service:
        return jsonify({"error": "Gmail service not authenticated"}), 401
    
    message = create_email(data['to'], data['subject'], data['body'])
    
    try:
        message = (service.users().messages().send(userId='me', body=message)
                  .execute())
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return jsonify({"error": "Failed to send email"}), 500

def create_ticket_notification_email(ticket):
    message = MIMEText(f"""
    New Ticket Created:
    
    Subject: {ticket.subject}
    Description: {ticket.description}
    Priority: {ticket.priority}
    Status: {ticket.status}
    Created At: {ticket.created_at}
    
    Please review this ticket at your earliest convenience.
    """)
    
    message['to'] = "support@yourdomain.com"  # Update with your support email
    message['subject'] = f"New Support Ticket: {ticket.subject}"
    
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_email(to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}