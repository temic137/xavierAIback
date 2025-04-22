from flask import session, jsonify, request
from functools import wraps
import logging

def login_required(f):
    """
    Decorator to check if user is logged in.
    Works with both traditional session-based auth and Firebase auth.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if 'user_id' not in session:
            # If not in session, check for Firebase token in Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Unauthorized"}), 401
            
            # At this point, we would verify the Firebase token
            # But since we're already verifying tokens at login and storing user_id in session,
            # we don't need to verify the token again here
            return jsonify({"error": "Session expired. Please log in again."}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to check if user is an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Then check if user is an admin
        # This would require adding an 'is_admin' field to the User model
        # For now, we'll just return unauthorized
        return jsonify({"error": "Admin access required"}), 403
        
        # Uncomment when admin field is added to User model
        # from models import User
        # user = User.query.get(session['user_id'])
        # if not user or not user.is_admin:
        #     return jsonify({"error": "Admin access required"}), 403
        
        return f(*args, **kwargs)
    return decorated_function
