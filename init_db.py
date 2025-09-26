#!/usr/bin/env python3
"""
Database initialization script for DigitalOcean deployment
Run this once after deployment to create database tables
"""

import os
os.environ['INIT_DB'] = 'true'

from app import create_app
from models import db

def init_database():
    """Initialize database tables"""
    app = create_app()

    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")

            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {', '.join(tables)}")

        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise

if __name__ == "__main__":
    init_database()