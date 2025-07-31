#!/usr/bin/env python3
"""
Test the new cookie-based authentication system
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"  # Change to production URL when testing live
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123!"

class TestCookieAuth:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        
    def test_csrf_token(self):
        """Test getting CSRF token"""
        print("\n1. Testing CSRF token endpoint...")
        response = self.session.get(f"{BASE_URL}/api/auth/csrf")
        
        if response.status_code == 200:
            data = response.json()
            self.csrf_token = data.get('csrf_token')
            print(f"   ✓ Got CSRF token: {self.csrf_token[:10]}...")
            
            # Check if cookie was set
            csrf_cookie = self.session.cookies.get('csrf_token')
            if csrf_cookie:
                print(f"   ✓ CSRF cookie set: {csrf_cookie[:10]}...")
            else:
                print("   ✗ CSRF cookie not set")
            return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            return False
    
    def test_register(self):
        """Test user registration"""
        print("\n2. Testing user registration...")
        
        # Add timestamp to make email unique
        unique_email = f"test_{int(datetime.now().timestamp())}@example.com"
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/register",
            headers={"X-CSRF-Token": self.csrf_token},
            json={
                "email": unique_email,
                "password": TEST_PASSWORD,
                "full_name": "Test User",
                "company_name": "Test Company"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Registration successful")
            print(f"   ✓ User ID: {data['user']['id']}")
            print(f"   ✓ Email: {data['user']['email']}")
            
            # Check for cookies
            access_cookie = self.session.cookies.get('access_token')
            refresh_cookie = self.session.cookies.get('refresh_token')
            
            if access_cookie:
                print(f"   ✓ Access token cookie set")
            else:
                print("   ✗ Access token cookie not set")
                
            if refresh_cookie:
                print(f"   ✓ Refresh token cookie set")
            else:
                print("   ✗ Refresh token cookie not set")
                
            return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            try:
                print(f"   ✗ Error: {response.json()}")
            except:
                print(f"   ✗ Response: {response.text}")
            return False
    
    def test_check_auth(self):
        """Test authentication check"""
        print("\n3. Testing authentication check...")
        
        response = self.session.get(f"{BASE_URL}/api/auth/check")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('authenticated'):
                print(f"   ✓ Authentication valid")
                print(f"   ✓ User: {data['user']['email']}")
                return True
            else:
                print("   ✗ Not authenticated")
                return False
        else:
            print(f"   ✗ Failed: {response.status_code}")
            return False
    
    def test_logout(self):
        """Test logout"""
        print("\n4. Testing logout...")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"X-CSRF-Token": self.csrf_token}
        )
        
        if response.status_code == 200:
            print("   ✓ Logout successful")
            
            # Check if cookies were cleared
            if not self.session.cookies.get('access_token'):
                print("   ✓ Access token cookie cleared")
            else:
                print("   ✗ Access token cookie still present")
                
            return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            return False
    
    def test_login(self):
        """Test login with existing user"""
        print("\n5. Testing login...")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            headers={"X-CSRF-Token": self.csrf_token},
            json={
                "email": "test@example.com",
                "password": "test123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Login successful")
            print(f"   ✓ User: {data['user']['email']}")
            
            # Check for cookies
            if self.session.cookies.get('access_token'):
                print(f"   ✓ Access token cookie set")
            if self.session.cookies.get('refresh_token'):
                print(f"   ✓ Refresh token cookie set")
                
            return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            try:
                print(f"   ✗ Error: {response.json()}")
            except:
                pass
            return False
    
    def test_refresh_token(self):
        """Test token refresh"""
        print("\n6. Testing token refresh...")
        
        # First login to get tokens
        self.test_login()
        
        # Now test refresh
        response = self.session.post(
            f"{BASE_URL}/api/auth/refresh",
            headers={"X-CSRF-Token": self.csrf_token}
        )
        
        if response.status_code == 200:
            print("   ✓ Token refresh successful")
            
            # Check if new cookies were set
            if self.session.cookies.get('access_token'):
                print("   ✓ New access token cookie set")
            if self.session.cookies.get('refresh_token'):
                print("   ✓ New refresh token cookie set")
                
            return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*60)
        print("Testing Cookie-Based Authentication System")
        print("="*60)
        
        results = []
        
        # Run tests in order
        results.append(("CSRF Token", self.test_csrf_token()))
        results.append(("Registration", self.test_register()))
        results.append(("Auth Check", self.test_check_auth()))
        results.append(("Logout", self.test_logout()))
        results.append(("Login", self.test_login()))
        results.append(("Token Refresh", self.test_refresh_token()))
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary:")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name:<20} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        print("="*60)
        
        return passed == total

if __name__ == "__main__":
    tester = TestCookieAuth()
    success = tester.run_all_tests()
    exit(0 if success else 1)