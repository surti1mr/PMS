#!/usr/bin/env python3
"""
Script to set real passwords for testing
"""

from app import app
from models import db, Admin, EventManager, Participant

def set_test_passwords():
    """Set test passwords for sample users"""
    print("Setting test passwords for sample users...")
    
    with app.app_context():
        try:
            # Set password for first admin
            admin = Admin.query.first()
            if admin:
                admin.set_password('admin123')
                print(f"✅ Set password for admin: {admin.email}")
            
            # Set password for first event manager
            manager = EventManager.query.first()
            if manager:
                manager.set_password('admin123')
                print(f"✅ Set password for event manager: {manager.email}")
            
            # Set password for first participant
            participant = Participant.query.first()
            if participant:
                participant.set_password('admin123')
                print(f"✅ Set password for participant: {participant.email}")
            
            # Commit changes
            db.session.commit()
            print("✅ All passwords set successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting passwords: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("=== Setting Test Passwords ===")
    if set_test_passwords():
        print("\n✅ Password setup completed!")
        print("\nTest credentials:")
        print("Admin: alice.admin@comedyorg.com / admin123")
        print("Event Manager: aaron.manager@comedyorg.com / admin123")
        print("Participant: emily.johnson@domain.com / admin123")
    else:
        print("❌ Password setup failed!")
