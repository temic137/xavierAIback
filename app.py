
from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from extensions import db
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.analytics import analytics_bp
from routes.leads import leads_bp
from routes.email_service import email_bp
import os
import logging
from logging_config import configure_logging
from flask_migrate import Migrate
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql
from models import User  # Add this import
from werkzeug.middleware.proxy_fix import ProxyFix
from firebase_config import initialize_firebase

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration is loaded from Config class

    # Configure CORS with all necessary settings
    CORS(app,
         resources={
             # For public endpoints (widget, static files, etc.)
             r"/static/*": {
                 "origins": ["https://xavierai.site","https://xavierai-m-2.vercel.app"],  # Allow all origins for static resources
                 "methods": ["GET"],
                 "supports_credentials": False,  # No credentials needed for static resources
                 "max_age": 86400
             },
             r"/get_chatbot_script/*": {
                 "origins":["https://xavierai.site","https://xavierai-m-2.vercel.app"],  # Allow all origins for the script
                 "methods": ["GET"],
                 "supports_credentials": False,
                 "max_age": 86400
             },
             # For authenticated endpoints
             r"/*": {
                 "origins": ["https://xavierai.site","https://xavierai-m-2.vercel.app"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                 "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken", "User-ID"],
                 "expose_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
                 "supports_credentials": True,
                 "max_age": 86400
             }
         })

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize Firebase
    try:
        initialize_firebase()
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(email_bp, url_prefix='/email')

    # Create database tables and default user
    with app.app_context():
        try:
            db.create_all()
            # Check if default user exists
            default_user = User.query.get(4269)
            if not default_user:
                default_user = User(
                    id=4269,
                    username='default_ticket_user',
                    password_hash='default_not_used'
                )
                db.session.add(default_user)
                db.session.commit()
                print("Default user created successfully")
            else:
                print("Default user already exists")
        except Exception as e:
            print(f"Database initialization error: {e}")
            db.session.rollback()

    return app

# Create the app instance for Gunicorn
app = create_app()

# Configure logging
configure_logging(app)

# Import the SSL error filter to hide SSL handshake errors
try:
    from xavier_back import ssl_filter
except ImportError:
    try:
        import ssl_filter
    except ImportError:
        print("Warning: SSL filter not loaded, SSL handshake errors will be visible in logs")

# Run database migrations
with app.app_context():
    try:
        # Run the migration to add notes column to lead table
        from migrations.add_notes_to_lead import run_migration as add_notes_migration
        add_notes_migration()

        # Run the migration to add Firebase auth fields to User model
        from migrations.add_firebase_auth_to_user import run_migration as add_firebase_auth_migration
        add_firebase_auth_migration()

        # Run the migration to fix password_hash nullable issue
        from migrations.fix_password_hash_nullable import run_migration as fix_password_hash_migration
        fix_password_hash_migration()

        print("Database migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

