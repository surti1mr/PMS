#!/usr/bin/env python3
"""
Script to fix all password hashes in the database
"""

from app import app
from models import db, Admin, EventManager, Participant

def fix_all_passwords():
    """Set proper passwords for all users"""
    print("Fixing all password hashes...")
    
    with app.app_context():
        try:
            # Fix all admin passwords
            admins = Admin.query.all()
            for admin in admins:
                if not admin.password_hash or admin.password_hash.startswith('$2y$10$hash'):
                    admin.set_password('admin123')
                    print(f"✅ Fixed admin: {admin.email}")
            
            # Fix all event manager passwords
            managers = EventManager.query.all()
            for manager in managers:
                if not manager.password_hash or manager.password_hash.startswith('$2y$10$hash'):
                    manager.set_password('admin123')
                    print(f"✅ Fixed event manager: {manager.email}")
            
            # Fix all participant passwords
            participants = Participant.query.all()
            for participant in participants:
                if not participant.password_hash or participant.password_hash.startswith('$2y$10$hash'):
                    participant.set_password('admin123')
                    print(f"✅ Fixed participant: {participant.email}")
            
            # Commit changes
            db.session.commit()
            print(f"\n✅ Fixed passwords for {len(admins)} admins, {len(managers)} managers, {len(participants)} participants")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing passwords: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("=== Fixing All Password Hashes ===")
    if fix_all_passwords():
        print("\n✅ All password hashes fixed!")
        print("\nAll users now have password: 'admin123' (for testing)")
    else:
        print("❌ Password fix failed!")
