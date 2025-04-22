from flask import Flask
from config import Config
from extensions import db
from sqlalchemy import Column, String, Boolean
import logging

def run_migration():
    """
    Add Firebase authentication fields to User model
    """
    try:
        # Check if columns already exist
        columns = db.inspect(db.engine).get_columns('user')
        column_names = [col['name'] for col in columns]

        # Use SQLAlchemy 2.0 compatible approach with connection
        with db.engine.connect() as conn:
            # Add email column if it doesn't exist
            if 'email' not in column_names:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN email VARCHAR(128)'))
                logging.info("Added email column to user table")

            # Add firebase_uid column if it doesn't exist
            if 'firebase_uid' not in column_names:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(128)'))
                logging.info("Added firebase_uid column to user table")

            # Add profile_picture column if it doesn't exist
            if 'profile_picture' not in column_names:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN profile_picture VARCHAR(512)'))
                logging.info("Added profile_picture column to user table")

            # Add auth_provider column if it doesn't exist
            if 'auth_provider' not in column_names:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN auth_provider VARCHAR(20) DEFAULT 'local'"))
                logging.info("Added auth_provider column to user table")

            # SQLite doesn't support ALTER TABLE ... DROP NOT NULL
            # We'll handle this differently in the model definition

            # Commit the transaction
            conn.commit()

        return True
    except Exception as e:
        logging.error(f"Error in migration: {str(e)}")
        return False

if __name__ == "__main__":
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        success = run_migration()
        if success:
            print("Migration completed successfully")
        else:
            print("Migration failed")
