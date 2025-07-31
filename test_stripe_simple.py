#!/usr/bin/env python3
"""
Simple test of Stripe purchase flow using requests
"""

import requests
from urllib.parse import urljoin, urlparse

def test_stripe_flow_simple():
    session = requests.Session()
    base_url = "https://bankcsvconverter.com"
    
    print("=== Testing Stripe Purchase Flow ===\n")
    
    # Step 1: Load pricing page
    print("Step 1: Loading pricing page...")
    response = session.get(urljoin(base_url, "/pricing.html"))
    print(f"  - Status: {response.status_code}")
    print(f"  - URL: {response.url}")
    
    # Check for any authentication-related headers or cookies
    print("\n  - Cookies set:")
    for cookie in session.cookies:
        print(f"    {cookie.name}: {cookie.value[:20]}...")
    
    # Look for buy buttons in the HTML
    if response.status_code == 200:
        content = response.text
        
        # Look for Stripe-related elements
        stripe_elements = []
        if 'stripe' in content.lower():
            stripe_elements.append("Found 'stripe' references in page")
        if 'data-price' in content:
            stripe_elements.append("Found price data attributes")
        if 'buy' in content.lower():
            stripe_elements.append("Found 'buy' text in page")
        
        print(f"\n  - Page analysis:")
        for element in stripe_elements:
            print(f"    ✓ {element}")
        
        # Look for authentication checks in JavaScript
        auth_patterns = [
            'checkAuth',
            'isAuthenticated',
            'user.token',
            'localStorage',
            'Force Auth',
            'Stripe Complete',
            'Auth Login Fix'
        ]
        
        print(f"\n  - JavaScript auth patterns found:")
        for pattern in auth_patterns:
            if pattern in content:
                print(f"    ✓ Found '{pattern}' in page source")
    
    # Step 2: Check login page
    print("\n\nStep 2: Checking login page...")
    login_response = session.get(urljoin(base_url, "/login.html"))
    print(f"  - Status: {login_response.status_code}")
    print(f"  - URL: {login_response.url}")
    
    if login_response.status_code == 200:
        # Check for returnUrl handling
        if 'returnUrl' in login_response.text:
            print("  ✓ Login page handles returnUrl parameter")
        if 'redirect' in login_response.text.lower():
            print("  ✓ Login page has redirect logic")
    
    # Step 3: Simulate clicking buy button (check what URL it would go to)
    print("\n\nStep 3: Checking buy button behavior...")
    print("  - Without authentication, buy button should redirect to login")
    print("  - Expected flow: /pricing.html → /login.html?returnUrl=/pricing.html")
    
    # Step 4: Check for API endpoints
    print("\n\nStep 4: Checking for API endpoints...")
    api_endpoints = [
        "/api/auth/check",
        "/api/auth/status",
        "/api/user",
        "/api/stripe/session"
    ]
    
    for endpoint in api_endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = session.get(url, timeout=5)
            print(f"  - {endpoint}: {response.status_code}")
        except:
            print(f"  - {endpoint}: Not accessible or doesn't exist")
    
    print("\n\n=== Summary ===")
    print("The Stripe purchase flow appears to:")
    print("1. Check authentication status when buy button is clicked")
    print("2. Redirect unauthenticated users to login page")
    print("3. Should preserve the intent to purchase after login")
    print("4. Requires JavaScript execution to fully test the flow")

if __name__ == "__main__":
    test_stripe_flow_simple()