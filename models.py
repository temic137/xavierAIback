from extensions import db
from sqlalchemy.dialects.postgresql import JSON  # Import JSON type if using PostgreSQL
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import datetime as dt
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
import uuid
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # Can be null for Firebase users
    email = db.Column(db.String(128), unique=True, nullable=True)  # For Firebase users
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True)  # Firebase User ID
    profile_picture = db.Column(db.String(512), nullable=True)  # Profile picture URL
    auth_provider = db.Column(db.String(20), default='local')  # 'local', 'firebase', 'google'
    chatbots = db.relationship('Chatbot', backref='owner', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)
    leads = db.relationship('Lead', backref='owner', lazy=True)


class Chatbot(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(JSON)  # JSON column to store both PDF and database data
    feedbacks = db.relationship(
        'Feedback',
        backref='chatbot',
        lazy=True,
        cascade="all, delete-orphan"
    )
    leads = db.relationship(
        'Lead',
        backref='chatbot',
        lazy=True,
        cascade="all, delete-orphan"
    )


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    feedback = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime)


class QuestionAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))
    question_metadata = db.Column(db.JSON)


#------------------------------------------------
# START  OF NEW MODELS
#----------------------------------------------
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc), onupdate=lambda: datetime.now(dt.timezone.utc))
    account_details = db.Column(db.JSON)

class TicketResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))

#----------------------------------------
# END OF NEW MODELS
#------------------------------------------


# Removed duplicate import

class GmailIntegration(db.Model):
    __tablename__ = 'gmail_integration'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))



class SentimentAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    user_sentiment = db.Column(db.Boolean, nullable=False)  # True for positive, False for negative
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))
    conversation_id = db.Column(db.String(36), nullable=True)  # To track specific conversations


class ConversationMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), nullable=False, index=True)  # Group messages by conversation
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)  # User's message
    response = db.Column(db.Text, nullable=False)  # Chatbot's response
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))

    # Define relationship with Chatbot
    chatbot = db.relationship('Chatbot', backref=db.backref('conversation_messages', lazy=True))


# Live chat feature has been removed


class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=True)
    chatbot_id = db.Column(db.String(36), db.ForeignKey('chatbot.id'), nullable=False)
    # Make user_id nullable to match existing schema
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(dt.timezone.utc))
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, converted, etc.
    notes = db.Column(db.Text, nullable=True)