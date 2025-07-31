#!/usr/bin/env python3
"""
Test authentication flow for BankCSVConverter Stripe integration
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://bankcsvconverter.com"

def test_auth_flow():
    """Test the authentication and Stripe flow"""
    
    print(f"\n{'='*60}")
    print(f"Testing Auth Flow - {datetime.now()}")
    print(f"{'='*60}\n")
    
    # Test 1: Check if API endpoints are accessible
    print("1. Testing API endpoints...")
    endpoints = [
        "/api/auth/check",
        "/api/auth/verify",
        "/api/user",
        "/api/stripe/create-checkout-session"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: ERROR - {str(e)}")
    
    # Test 2: Check pricing page
    print("\n2. Checking pricing page...")
    try:
        response = requests.get(f"{BASE_URL}/pricing.html", timeout=10)
        print(f"   Status: {response.status_code}")
        
        # Check for auth scripts
        auth_scripts = [
            "auth-fixed.js",
            "stripe-complete-fix.js",
            "force-auth-storage.js"
        ]
        
        for script in auth_scripts:
            if script in response.text:
                print(f"   ✓ Found {script}")
            else:
                print(f"   ✗ Missing {script}")
                
    except Exception as e:
        print(f"   ERROR: {str(e)}")
    
    # Test 3: Check login page
    print("\n3. Checking login page...")
    try:
        response = requests.get(f"{BASE_URL}/login.html", timeout=10)
        print(f"   Status: {response.status_code}")
        
        # Check for auth scripts
        login_scripts = [
            "auth.js",
            "auth-login-fix.js",
            "force-auth-storage.js"
        ]
        
        for script in login_scripts:
            if script in response.text:
                print(f"   ✓ Found {script}")
            else:
                print(f"   ✗ Missing {script}")
                
    except Exception as e:
        print(f"   ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print("Manual Testing Required:")
    print("1. Open https://bankcsvconverter.com/pricing.html in incognito")
    print("2. Open DevTools Console (Cmd+Option+J)")
    print("3. Click any 'Buy' button")
    print("4. Check console for [Force Auth], [Stripe Complete] messages")
    print("5. Login if redirected")
    print("6. Verify redirect back to pricing page")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_auth_flow()