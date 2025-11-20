#!/usr/bin/env python3
"""
Test script to verify web login functionality
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def test_web_login():
    """Test the web login form"""
    print("Testing web login functionality...")
    
    try:
        # Get the login page
        response = requests.get(f"{BASE_URL}/")
        print(f"Login page status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Could not access login page")
            return False
        
        # Test login with form data
        login_data = {
            'email': 'alice.admin@comedyorg.com',
            'password': 'admin123'
        }
        
        # Submit login form
        login_response = requests.post(f"{BASE_URL}/submit_login", data=login_data, allow_redirects=False)
        print(f"Login submission status: {login_response.status_code}")
        
        if login_response.status_code == 302:  # Redirect after successful login
            print("✅ Login successful - redirected to home page")
            return True
        elif login_response.status_code == 200:
            # Check if there's an error message
            soup = BeautifulSoup(login_response.text, 'html.parser')
            error_div = soup.find('div', class_='error')
            if error_div:
                print(f"❌ Login failed: {error_div.get_text()}")
            else:
                print("❌ Login failed - no redirect and no error message")
            return False
        else:
            print(f"❌ Login failed with status: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_different_users():
    """Test login with different user types"""
    print("\nTesting different user types...")
    
    test_users = [
        ("alice.admin@comedyorg.com", "admin123", "Admin"),
        ("aaron.manager@comedyorg.com", "admin123", "Event Manager"),
        ("emily.johnson@domain.com", "admin123", "Participant")
    ]
    
    for email, password, user_type in test_users:
        print(f"\nTesting {user_type}: {email}")
        try:
            login_data = {
                'email': email,
                'password': password
            }
            
            response = requests.post(f"{BASE_URL}/submit_login", data=login_data, allow_redirects=False)
            
            if response.status_code == 302:
                print(f"✅ {user_type} login successful")
            else:
                print(f"❌ {user_type} login failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {user_type} test failed: {e}")

if __name__ == "__main__":
    print("=== Web Login Test ===")
    
    if test_web_login():
        print("\n✅ Web login is working!")
    else:
        print("\n❌ Web login failed!")
    
    test_different_users()
