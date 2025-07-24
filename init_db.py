#!/usr/bin/env python3
"""
Database initialization script for the Adaptive Learning Platform
"""

from app import app, db
from content_manager import get_content_manager

def init_database():
    """Initialize the database with tables and sample content"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Initialize content
        content_mgr = get_content_manager()
        content_mgr.initialize_content()
        print("✅ Sample content and quiz questions initialized!")
        
        print("\n🎉 Database initialization complete!")
        print("You can now run the application with: python3 main.py")

if __name__ == "__main__":
    init_database() 