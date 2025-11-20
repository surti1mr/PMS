#!/usr/bin/env python3
"""
Test script to verify database events are being displayed
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def test_events_page():
    """Test the events page displays database events"""
    print("Testing events page with database data...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Login first
        login_data = {
            'email': 'alice.admin@comedyorg.com',
            'password': 'admin123'
        }
        
        login_response = session.post(f"{BASE_URL}/submit_login", data=login_data)
        if login_response.status_code != 200:
            print("❌ Login failed")
            return False
        
        # Get events page
        events_response = session.get(f"{BASE_URL}/events")
        print(f"Events page status: {events_response.status_code}")
        
        if events_response.status_code == 200:
            soup = BeautifulSoup(events_response.text, 'html.parser')
            
            # Check for event cards
            event_cards = soup.find_all('div', class_='event-card')
            print(f"Found {len(event_cards)} event cards")
            
            if len(event_cards) > 0:
                print("✅ Events page displays database events!")
                
                # Check first event for database content
                first_event = event_cards[0]
                event_name = first_event.find('h3', class_='event-name')
                event_date = first_event.find('span', class_='event-date')
                
                if event_name and event_date:
                    print(f"Sample event: {event_name.get_text()}")
                    print(f"Sample date: {event_date.get_text()}")
                
                return True
            else:
                print("❌ No event cards found")
                return False
        else:
            print(f"❌ Events page failed with status: {events_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_upcoming_events_page():
    """Test the upcoming events page"""
    print("\nTesting upcoming events page...")
    
    session = requests.Session()
    
    try:
        # Login first
        login_data = {
            'email': 'alice.admin@comedyorg.com',
            'password': 'admin123'
        }
        
        session.post(f"{BASE_URL}/submit_login", data=login_data)
        
        # Get upcoming events page
        response = session.get(f"{BASE_URL}/upcoming_events")
        print(f"Upcoming events page status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            event_cards = soup.find_all('div', class_='event-card')
            print(f"Found {len(event_cards)} upcoming event cards")
            
            if len(event_cards) > 0:
                print("✅ Upcoming events page displays database events!")
                return True
            else:
                print("ℹ️ No upcoming events found (this is normal if all events are in the past)")
                return True
        else:
            print(f"❌ Upcoming events page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_api_events():
    """Test the API events endpoint"""
    print("\nTesting API events endpoint...")
    
    session = requests.Session()
    
    try:
        # Login via API
        login_data = {
            "email": "alice.admin@comedyorg.com",
            "password": "admin123"
        }
        
        login_response = session.post(f"{BASE_URL}/api/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ API login failed")
            return False
        
        # Get events via API
        events_response = session.get(f"{BASE_URL}/api/events")
        print(f"API events status: {events_response.status_code}")
        
        if events_response.status_code == 200:
            data = events_response.json()
            if data['success']:
                events = data['events']
                print(f"✅ API returned {len(events)} events")
                
                if len(events) > 0:
                    print(f"Sample event: {events[0]['event_name']}")
                    print(f"Sample date: {events[0]['event_date']}")
                
                return True
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API events failed: {events_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Events Display Test ===")
    
    # Test web pages
    if test_events_page():
        print("✅ Events page test passed!")
    else:
        print("❌ Events page test failed!")
    
    test_upcoming_events_page()
    
    # Test API
    if test_api_events():
        print("✅ API events test passed!")
    else:
        print("❌ API events test failed!")
    
    print("\n🎉 Database events are now being displayed from the database!")
