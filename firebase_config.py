import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Firebase service account credentials from environment variables
SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "xavierai-754e3",
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL'),
    "universe_domain": "googleapis.com"
}

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize with service account
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred)

    return firebase_admin.get_app()

def verify_firebase_token(id_token):
    """Verify Firebase ID token and return user info"""
    try:
        # Initialize Firebase if not already initialized
        initialize_firebase()

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)

        # Get user info
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')

        return {
            'uid': uid,
            'email': email,
            'name': name,
            'picture': picture,
            'verified': True
        }
    except Exception as e:
        print(f"Error verifying Firebase token: {str(e)}")
        return {'verified': False, 'error': str(e)}
