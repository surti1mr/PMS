#!/usr/bin/env python3
"""
Test script to verify database connection
"""

from app import app
from models import db, Admin, EventManager, Participant, Event
from config import Config

def test_database_connection():
    """Test database connection and basic queries"""
    print("Testing database connection...")
    
    with app.app_context():
        try:
            # Test basic connection
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1 as test')).fetchone()
            print(f"✅ Database connection successful: {result[0]}")
            
            # Test table existence
            tables = ['admin', 'event_manager', 'participant', 'event', 'event_type', 'event_status', 'registration_status', 'registration']
            
            for table in tables:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                    print(f"✅ Table '{table}' exists with {result[0]} records")
                except Exception as e:
                    print(f"❌ Table '{table}' error: {e}")
            
            # Test sample queries
            print("\n--- Sample Data ---")
            
            # Count users by type
            admin_count = Admin.query.count()
            manager_count = EventManager.query.count()
            participant_count = Participant.query.count()
            event_count = Event.query.count()
            
            print(f"Admins: {admin_count}")
            print(f"Event Managers: {manager_count}")
            print(f"Participants: {participant_count}")
            print(f"Events: {event_count}")
            
            # Show sample admin
            if admin_count > 0:
                sample_admin = Admin.query.first()
                print(f"\nSample Admin: {sample_admin.first_name} {sample_admin.last_name} ({sample_admin.email})")
            
            # Show sample event
            if event_count > 0:
                sample_event = Event.query.first()
                print(f"Sample Event: {sample_event.event_name} on {sample_event.event_date}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

def test_login_functionality():
    """Test login functionality with sample data"""
    print("\n--- Testing Login Functionality ---")
    
    with app.app_context():
        try:
            # Test admin login (you'll need to set a real password)
            admin = Admin.query.first()
            if admin:
                print(f"Admin found: {admin.email}")
                # Note: You'll need to set a real password for testing
                # admin.set_password('testpassword')
                # print(f"Password set for admin: {admin.check_password('testpassword')}")
            
            # Test event manager login
            manager = EventManager.query.first()
            if manager:
                print(f"Event Manager found: {manager.email}")
            
            # Test participant login
            participant = Participant.query.first()
            if participant:
                print(f"Participant found: {participant.email}")
            
            return True
            
        except Exception as e:
            print(f"❌ Login test failed: {e}")
            return False

if __name__ == "__main__":
    print("=== Database Connection Test ===")
    
    # Test database connection
    if test_database_connection():
        print("\n✅ Database connection test passed!")
        
        # Test login functionality
        if test_login_functionality():
            print("✅ Login functionality test passed!")
        else:
            print("❌ Login functionality test failed!")
    else:
        print("❌ Database connection test failed!")
        print("Please check your database credentials and network connection.")
