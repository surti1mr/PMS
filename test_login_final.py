#!/usr/bin/env python3
"""
Test script to verify login functionality with real passwords
"""

import requests
import json

BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_login(email, password, user_type):
    """Test login for a specific user type"""
    print(f"\nTesting {user_type} login: {email}")
    try:
        data = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{API_BASE}/login", json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"User: {result['user']['name']} ({result['user']['type']})")
            return response.cookies
        else:
            print(f"❌ Login failed: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_protected_endpoint(cookies, endpoint_name):
    """Test a protected endpoint with cookies"""
    print(f"\nTesting {endpoint_name} with authentication...")
    try:
        response = requests.get(f"{API_BASE}/{endpoint_name}", cookies=cookies)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {endpoint_name} accessible")
            return True
        else:
            print(f"❌ {endpoint_name} failed: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ {endpoint_name} test failed: {e}")
        return False

def main():
    print("=== Login Functionality Test ===")
    
    # Test credentials
    test_users = [
        ("alice.admin@comedyorg.com", "admin123", "Admin"),
        ("aaron.manager@comedyorg.com", "manager123", "Event Manager"),
        ("emily.johnson@domain.com", "participant123", "Participant")
    ]
    
    for email, password, user_type in test_users:
        cookies = test_login(email, password, user_type)
        
        if cookies:
            # Test protected endpoints
            test_protected_endpoint(cookies, "profile")
            test_protected_endpoint(cookies, "events")
            
            if user_type == "Participant":
                test_protected_endpoint(cookies, "my-registrations")

if __name__ == "__main__":
    main()
