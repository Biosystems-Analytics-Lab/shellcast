#!/usr/bin/env python3
"""
Test script to verify the web unsubscribe endpoint works correctly.
This script will test the API endpoint without needing the full web server.
"""

import requests
import json


def test_unsubscribe_api():
    """Test the unsubscribe API endpoint."""
    print("🧪 Testing Web Unsubscribe API")
    print("=" * 50)
    
    # Test data
    test_email = "test@example.com"
    
    # Test 1: Valid unsubscribe request
    print("\n--- Test 1: Valid Unsubscribe Request ---")
    try:
        response = requests.post(
            "http://localhost:3361/api/unsubscribe",
            json={"email": test_email},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Unsubscribe API working correctly!")
        else:
            print("❌ Unsubscribe API returned error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web server")
        print("   Make sure your Flask app is running on port 3361")
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Test 2: Missing email
    print("\n--- Test 2: Missing Email ---")
    try:
        response = requests.post(
            "http://localhost:3361/api/unsubscribe",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ API correctly handles missing email")
        else:
            print("❌ API should return 400 for missing email")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web server")
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Test 3: Invalid email format
    print("\n--- Test 3: Invalid Email Format ---")
    try:
        response = requests.post(
            "http://localhost:3361/api/unsubscribe",
            json={"email": "invalid-email"},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 404:
            print("✅ API correctly handles invalid email (user not found)")
        else:
            print("❌ API should return 404 for invalid email")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web server")
    except Exception as e:
        print(f"❌ Error testing API: {e}")


def test_unsubscribe_page():
    """Test the unsubscribe page accessibility."""
    print("\n🧪 Testing Unsubscribe Page")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:3361/unsubscribe")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Unsubscribe page accessible!")
            
            # Check if page contains expected content
            content = response.text
            if "unsubscribe" in content.lower():
                print("✅ Page contains unsubscribe content")
            else:
                print("❌ Page missing unsubscribe content")
                
        else:
            print("❌ Unsubscribe page not accessible")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to web server")
        print("   Make sure your Flask app is running on port 3361")
    except Exception as e:
        print(f"❌ Error testing page: {e}")


if __name__ == "__main__":
    print("🧪 Testing ShellCast Web Unsubscribe System")
    print("=" * 50)
    
    # Test the web unsubscribe page
    test_unsubscribe_page()
    
    # Test the API endpoint
    test_unsubscribe_api()
    
    print("\n" + "=" * 50)
    print("🎯 Testing Complete!")
    print("\nTo test the full flow:")
    print("1. Make sure your web app is running (python main.py)")
    print("2. Send a test email from your analysis script")
    print("3. Click the unsubscribe link in the email")
    print("4. Verify the unsubscribe process works")
