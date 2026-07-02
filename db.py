import mysql.connector
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'changeme'),
    'database': os.environ.get('DB_NAME', 'STRATOS_DB')
}

def get_db():
    """Get a fresh database connection."""
    return mysql.connector.connect(**DB_CONFIG)
