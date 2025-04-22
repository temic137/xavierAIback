from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from extensions import db
import os
import logging
from logging_config import configure_logging
from flask_migrate import Migrate
from models import User  # Add this import
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS with all necessary settings
    CORS(app,
         resources={
             # For public endpoints (widget, static files, etc.)
             r"/static/*": {
                 "origins": "*",  # Allow all origins for static resources
                 "methods": ["GET"],
                 "supports_credentials": False,  # No credentials needed for static resources
                 "max_age": 86400
             },
             r"/get_chatbot_script/*": {
                 "origins": "*",  # Allow all origins for the script
                 "methods": ["GET"],
                 "supports_credentials": False,
                 "max_age": 86400
             },
             # For authenticated endpoints
             r"/*": {
                 "origins": [
                    "http://localhost:4200",  # Angular dev server
                    "http://localhost:5000",  # Flask dev server
                    "https://xavierai-m-2.vercel.app",  # Production frontend
                 ],
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

    # Try to initialize Firebase, but continue if it fails
    try:
        from firebase_config import initialize_firebase
        initialize_firebase()
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")

    # Try to register blueprints, but continue if they fail
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp)
        print("Auth blueprint registered")
    except Exception as e:
        print(f"Error registering auth blueprint: {str(e)}")
        
        # Add a minimal auth endpoint
        @app.route('/api/auth/status', methods=['GET'])
        def auth_status():
            return jsonify({"status": "minimal", "message": "Running in minimal mode"})

    try:
        from routes.chatbot import chatbot_bp
        app.register_blueprint(chatbot_bp)
        print("Chatbot blueprint registered")
    except Exception as e:
        print(f"Error registering chatbot blueprint: {str(e)}")
        
        # Add a minimal chatbot endpoint
        @app.route('/api/chatbot/ask', methods=['POST'])
        def chatbot_ask():
            return jsonify({"response": "I'm running in minimal mode due to deployment issues. Please try again later."})

    try:
        from routes.analytics import analytics_bp
        app.register_blueprint(analytics_bp)
        print("Analytics blueprint registered")
    except Exception as e:
        print(f"Error registering analytics blueprint: {str(e)}")

    try:
        from routes.leads import leads_bp
        app.register_blueprint(leads_bp)
        print("Leads blueprint registered")
    except Exception as e:
        print(f"Error registering leads blueprint: {str(e)}")

    try:
        from routes.email_service import email_bp
        app.register_blueprint(email_bp, url_prefix='/email')
        print("Email blueprint registered")
    except Exception as e:
        print(f"Error registering email blueprint: {str(e)}")

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

    # Add a health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok", "message": "Server is running"})

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
