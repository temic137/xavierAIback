from flask import Flask
from config import Config
from extensions import db
import logging

def run_migration():
    """
    Fix the password_hash column to be nullable
    """
    try:
        # Use SQLAlchemy 2.0 compatible approach with connection
        with db.engine.connect() as conn:
            # Create a temporary table with the correct schema
            conn.execute(db.text('''
                CREATE TABLE user_new (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(128) NOT NULL UNIQUE,
                    password_hash VARCHAR(256),
                    email VARCHAR(128) UNIQUE,
                    firebase_uid VARCHAR(128) UNIQUE,
                    profile_picture VARCHAR(512),
                    auth_provider VARCHAR(20) DEFAULT 'local'
                )
            '''))

            # Copy data from the old table to the new table
            conn.execute(db.text('''
                INSERT INTO user_new (id, username, password_hash, email, firebase_uid, profile_picture, auth_provider)
                SELECT id, username, password_hash, email, firebase_uid, profile_picture, auth_provider FROM user
            '''))

            # Drop the old table
            conn.execute(db.text('DROP TABLE user'))

            # Rename the new table to the original name
            conn.execute(db.text('ALTER TABLE user_new RENAME TO user'))

            # Commit the transaction
            conn.commit()

        logging.info("Successfully fixed password_hash column to be nullable")
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
