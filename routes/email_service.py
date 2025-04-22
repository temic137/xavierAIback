from flask import Blueprint, request, jsonify, current_app
import os
from models import Ticket
from extensions import db
from functools import wraps
from flask import session
import resend

email_bp = Blueprint('email', __name__)

# Decorator for login required routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Handle errors for routes
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function

@email_bp.route('/send-email', methods=['POST'])
@login_required
@handle_errors
def send_email():
    """
    Send an email using Resend API
    Required fields in request body:
    - from_email: Sender email address
    - to_email: Recipient email address
    - subject: Email subject
    - html_content: Email body in HTML format
    """
    data = request.json

    # Validate required fields
    if not all(k in data for k in ['from_email', 'to_email', 'subject', 'html_content']):
        return jsonify({"error": "Missing required fields"}), 400

    # Get Resend API key from environment variable
    resend_api_key = os.environ.get('RESEND_API_KEY')
    if not resend_api_key:
        return jsonify({"error": "Resend API key not configured"}), 500

    # Initialize Resend client
    resend.api_key = resend_api_key

    # Prepare the email payload
    # Extract display name and email for reply-to
    from_email = data['from_email']
    reply_to_email = data.get('reply_to', from_email)
    display_name = ""

    # Check if the email contains a display name
    if '<' in from_email and '>' in from_email:
        display_name = from_email.split('<')[0].strip()
        email_part = from_email.split('<')[1].split('>')[0].strip()
        # Use the verified domain but keep the display name
        from_email = f'"{display_name}" <noreply@xavierai.site>'
    else:
        # No display name, just use the verified domain with the email as the name
        from_email = f'"{from_email}" <noreply@xavierai.site>'

    payload = {
        'from': from_email,
        'to': data['to_email'],
        'reply_to': reply_to_email,  # Set the reply-to address to the original email
        'subject': data['subject'],
        'html': data['html_content']
    }

    # Send the email using Resend
    try:
        response = resend.Emails.send(payload)
        return jsonify({"message": "Email sent successfully", "data": response}), 200
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@email_bp.route('/send-ticket-email/<ticket_id>', methods=['POST'])
@login_required
@handle_errors
def send_ticket_email(ticket_id):
    """
    Send an email about a specific ticket
    Required fields in request body:
    - from_email: Sender email address
    - to_email: Recipient email address
    - subject: Email subject (optional, will use ticket subject if not provided)
    - html_content: Email body in HTML format (optional, will use ticket details if not provided)
    """
    data = request.json

    # Validate required fields
    if not all(k in data for k in ['from_email', 'to_email']):
        return jsonify({"error": "Missing required fields: from_email and to_email"}), 400

    # Get ticket details
    ticket = Ticket.query.get_or_404(ticket_id)

    # Get Resend API key from environment variable
    resend_api_key = os.environ.get('RESEND_API_KEY')
    if not resend_api_key:
        return jsonify({"error": "Resend API key not configured"}), 500

    # Initialize Resend client
    resend.api_key = resend_api_key

    # Use provided subject or default to ticket subject
    subject = data.get('subject', f"Ticket #{ticket.id}: {ticket.subject}")

    # Use provided HTML content or generate from ticket details
    html_content = data.get('html_content', generate_ticket_email_content(ticket))

    # Extract display name and email for reply-to
    from_email = data['from_email']
    reply_to_email = data.get('reply_to', from_email)
    display_name = ""

    # Check if the email contains a display name
    if '<' in from_email and '>' in from_email:
        display_name = from_email.split('<')[0].strip()
        email_part = from_email.split('<')[1].split('>')[0].strip()
        # Use the verified domain but keep the display name
        from_email = f'"{display_name}" <noreply@xavierai.site>'
    else:
        # No display name, just use the verified domain with the email as the name
        from_email = f'"{from_email}" <noreply@xavierai.site>'

    payload = {
        'from': from_email,
        'to': data['to_email'],
        'reply_to': reply_to_email,  # Set the reply-to address to the original email
        'subject': subject,
        'html': html_content
    }

    # Send the email using Resend
    try:
        response = resend.Emails.send(payload)
        return jsonify({"message": "Email sent successfully", "data": response}), 200
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

def generate_ticket_email_content(ticket):
    """Generate HTML content for ticket email"""
    status_color = {
        'open': '#3b82f6',  # blue
        'in_progress': '#8b5cf6',  # purple
        'resolved': '#10b981',  # green
        'closed': '#6b7280'  # gray
    }

    priority_color = {
        'high': '#ef4444',  # red
        'medium': '#f59e0b',  # yellow
        'low': '#10b981'  # green
    }

    ticket_status = ticket.status.lower()
    ticket_priority = ticket.priority.lower()

    status_bg_color = status_color.get(ticket_status, '#6b7280')
    priority_bg_color = priority_color.get(ticket_priority, '#6b7280')

    # Format created_at date
    created_at = ticket.created_at.strftime('%B %d, %Y at %I:%M %p')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ margin-bottom: 20px; }}
            .ticket-info {{ margin-bottom: 30px; }}
            .badge {{ display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; color: white; margin-right: 10px; }}
            .status {{ background-color: {status_bg_color}; }}
            .priority {{ background-color: {priority_bg_color}; }}
            .details {{ background-color: #f9fafb; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Ticket #{ticket.id}: {ticket.subject}</h2>
            </div>

            <div class="ticket-info">
                <p>
                    <span class="badge status">{ticket.status.title()}</span>
                    <span class="badge priority">{ticket.priority.title()}</span>
                </p>
                <p><strong>Created:</strong> {created_at}</p>

                <div class="details">
                    <h3>Description</h3>
                    <p>{ticket.description}</p>

                    <h3>Account Details</h3>
                    <p>{ticket.account_details or 'No account details provided'}</p>
                </div>
            </div>

            <div class="footer">
                <p>This is an automated message regarding your support ticket. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html
