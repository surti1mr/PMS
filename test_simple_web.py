#!/usr/bin/env python3
"""
Simple test for web login
"""

import requests

BASE_URL = "http://localhost:5000"

def test_simple_login():
    """Test simple web login"""
    print("Testing simple web login...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Get login page
        response = session.get(f"{BASE_URL}/")
        print(f"Login page: {response.status_code}")
        
        # Test admin login
        login_data = {
            'email': 'alice.admin@comedyorg.com',
            'password': 'admin123'
        }
        
        response = session.post(f"{BASE_URL}/submit_login", data=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            # Check if we're on the home page
            if 'home' in response.url or 'Welcome' in response.text:
                print("✅ Admin login successful!")
                return True
            else:
                print("❌ Login failed - not redirected to home")
                return False
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Simple Web Login Test ===")
    test_simple_login()
