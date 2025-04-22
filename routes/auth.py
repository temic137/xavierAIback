from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db
from firebase_config import verify_firebase_token
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({"message": "Logged in successfully"}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return jsonify({"message": "Logged out successfully"}), 200
    return jsonify({"message": "No user to log out"}), 200

@auth_bp.route('/verify-firebase-token', methods=['POST'])
def verify_token():
    try:
        data = request.json
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "No token provided"}), 400

        # Verify the token with Firebase
        user_info = verify_firebase_token(id_token)

        if not user_info.get('verified'):
            return jsonify({"error": "Invalid token"}), 401

        # Check if user exists in our database
        firebase_uid = user_info.get('uid')
        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            # Create a new user
            email = user_info.get('email')
            name = user_info.get('name') or email.split('@')[0]  # Use part of email as username if name not available
            picture = user_info.get('picture')

            # Check if username already exists
            existing_user = User.query.filter_by(username=name).first()
            if existing_user:
                # Append a number to make username unique
                base_name = name
                counter = 1
                while User.query.filter_by(username=name).first():
                    name = f"{base_name}{counter}"
                    counter += 1

            # Create new user
            user = User(
                username=name,
                password_hash=None,  # Explicitly set to None for Firebase users
                email=email,
                firebase_uid=firebase_uid,
                profile_picture=picture,
                auth_provider='google'
            )
            db.session.add(user)
            db.session.commit()
            logging.info(f"Created new user from Firebase: {email}")

        # Set session
        session['user_id'] = user.id

        return jsonify({
            "message": "Authentication successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_picture": user.profile_picture
            }
        }), 200
    except Exception as e:
        logging.error(f"Firebase authentication error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500

@auth_bp.route('/current-user', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "auth_provider": user.auth_provider
        }
    }), 200