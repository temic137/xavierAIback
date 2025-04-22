"""
Migration script to add notes column to lead table
"""
from extensions import db
from flask import current_app
from sqlalchemy import text
import logging

def run_migration():
    """
    Add notes column to lead table if it doesn't exist
    """
    try:
        # Check if the column exists
        with db.engine.connect() as conn:
            # For PostgreSQL
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'lead' AND column_name = 'notes'
            """))
            column_exists = result.fetchone() is not None

            if not column_exists:
                current_app.logger.info("Adding notes column to lead table")
                conn.execute(text("ALTER TABLE lead ADD COLUMN notes TEXT"))
                conn.commit()
                current_app.logger.info("Successfully added notes column to lead table")
            else:
                current_app.logger.info("Notes column already exists in lead table")

    except Exception as e:
        current_app.logger.error(f"Error adding notes column to lead table: {str(e)}")
        raise
