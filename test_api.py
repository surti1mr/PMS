#!/usr/bin/env python3
"""
Test script to verify API endpoints
"""

import requests
import json
import time

# Wait a moment for the server to start
time.sleep(3)

BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_health():
    """Test API health endpoint"""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_login():
    """Test login functionality"""
    print("\nTesting login...")
    try:
        # Test with sample admin email (you'll need to set a real password)
        data = {
            "email": "alice.admin@comedyorg.com",
            "password": "password123"  # This will fail since we need to set real passwords
        }
        response = requests.post(f"{API_BASE}/login", json=data)
        print(f"Login status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

def test_events():
    """Test events endpoint (should fail without authentication)"""
    print("\nTesting events endpoint...")
    try:
        response = requests.get(f"{API_BASE}/events")
        print(f"Events status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 401  # Should fail without auth
    except Exception as e:
        print(f"Events test failed: {e}")
        return False

def main():
    print("=== API Endpoint Test ===")
    
    # Test health
    if test_health():
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        return
    
    # Test login (will likely fail due to password)
    if test_login():
        print("✅ Login test passed")
    else:
        print("❌ Login test failed (expected if password not set)")
    
    # Test protected endpoint
    if test_events():
        print("✅ Events endpoint correctly requires authentication")
    else:
        print("❌ Events endpoint test failed")

if __name__ == "__main__":
    main()
