from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

db = SQLAlchemy()
# mongo_client = MongoClient('mongodb://localhost:27017/')
# mongo_db = mongo_client['your_database_name']
# inventory_collection = mongo_db['inventory']

def init_db(app):
    # Configure SQLAlchemy pool settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,  # Increased for handling multiple streams
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'max_overflow': 40,
        'pool_pre_ping': True
    }
    
    db.init_app(app)
