"""Simple test script to verify API functionality."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200

def test_registration():
    """Test user registration."""
    data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print("\nRegistration:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print(f"User created: {result['user']['email']}")
        return result['access_token']
    else:
        print("Error:", response.json())
        return None

def test_login(email, password):
    """Test user login."""
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print("\nLogin:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print(f"Logged in as: {result['user']['email']}")
        return result['access_token']
    else:
        print("Error:", response.json())
        return None

def test_check_limit(token=None):
    """Test generation limit check."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.get(f"{BASE_URL}/api/check-limit", headers=headers)
    print("\nGeneration Limit Check:", response.json())
    return response.status_code == 200

def test_profile(token):
    """Test profile endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
    print("\nProfile:", response.json())
    return response.status_code == 200

def main():
    """Run all tests."""
    print("=== Bank Statement Converter API Tests ===\n")
    
    # Test health endpoint
    if not test_health():
        print("❌ Health check failed!")
        return
    print("✅ Health check passed")
    
    # Test registration
    token = test_registration()
    if token:
        print("✅ Registration passed")
    else:
        print("❌ Registration failed!")
        return
    
    # Test check limit (authenticated)
    if test_check_limit(token):
        print("✅ Check limit (authenticated) passed")
    else:
        print("❌ Check limit (authenticated) failed!")
    
    # Test check limit (anonymous)
    if test_check_limit():
        print("✅ Check limit (anonymous) passed")
    else:
        print("❌ Check limit (anonymous) failed!")
    
    # Test profile
    if test_profile(token):
        print("✅ Profile passed")
    else:
        print("❌ Profile failed!")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()