#!/usr/bin/env python3
"""
Analyze the Stripe purchase flow by examining the source code
"""

import requests
import re
from bs4 import BeautifulSoup

def analyze_stripe_flow():
    print("=== Analyzing Stripe Purchase Flow ===\n")
    
    # Get the pricing page
    response = requests.get("https://bankcsvconverter.com/pricing.html")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("1. Buy Button Analysis:")
    print("-" * 50)
    
    # Find all buttons that might be buy buttons
    buttons = soup.find_all(['button', 'a'], string=re.compile(r'Buy|Purchase|Get Started', re.I))
    
    for i, button in enumerate(buttons):
        print(f"\nButton {i+1}:")
        print(f"  Tag: {button.name}")
        print(f"  Text: {button.get_text().strip()}")
        
        # Check for onclick handlers
        if button.get('onclick'):
            print(f"  onclick: {button['onclick']}")
        
        # Check for data attributes
        for attr, value in button.attrs.items():
            if attr.startswith('data-'):
                print(f"  {attr}: {value}")
        
        # Check for href (if it's a link)
        if button.get('href'):
            print(f"  href: {button['href']}")
    
    print("\n\n2. JavaScript Analysis:")
    print("-" * 50)
    
    # Find all script tags
    scripts = soup.find_all('script')
    
    auth_code_snippets = []
    stripe_code_snippets = []
    
    for script in scripts:
        if script.string:
            content = script.string
            
            # Look for authentication-related code
            auth_patterns = [
                r'checkAuth\s*\(',
                r'isAuthenticated',
                r'localStorage\.getItem\([\'"]token',
                r'window\.location\.href\s*=\s*[\'"].*login',
                r'\[Force Auth\]',
                r'\[Stripe Complete\]',
                r'\[Auth Login Fix\]',
                r'returnUrl',
                r'forceBuyClick'
            ]
            
            for pattern in auth_patterns:
                matches = re.findall(pattern + r'.*', content, re.IGNORECASE)
                for match in matches:
                    auth_code_snippets.append(match[:200])  # First 200 chars
            
            # Look for Stripe-related code
            stripe_patterns = [
                r'stripe\.',
                r'createCheckoutSession',
                r'redirectToCheckout',
                r'handleBuyClick',
                r'data-price-id'
            ]
            
            for pattern in stripe_patterns:
                matches = re.findall(pattern + r'.*', content, re.IGNORECASE)
                for match in matches:
                    stripe_code_snippets.append(match[:200])  # First 200 chars
    
    print("\nAuthentication-related code found:")
    for snippet in set(auth_code_snippets):
        print(f"  • {snippet}")
    
    print("\nStripe-related code found:")
    for snippet in set(stripe_code_snippets):
        print(f"  • {snippet}")
    
    print("\n\n3. Flow Detection:")
    print("-" * 50)
    
    # Try to identify the purchase flow from the code
    if any('[Force Auth]' in s for s in auth_code_snippets):
        print("✓ Found [Force Auth] logging - auth check is implemented")
    
    if any('returnUrl' in s for s in auth_code_snippets):
        print("✓ Found returnUrl handling - redirect after login is implemented")
    
    if any('forceBuyClick' in s for s in auth_code_snippets):
        print("✓ Found forceBuyClick - auto-click after login is implemented")
    
    if any('localStorage' in s for s in auth_code_snippets):
        print("✓ Found localStorage usage - persistent auth storage")
    
    # Now check the login page
    print("\n\n4. Login Page Analysis:")
    print("-" * 50)
    
    login_response = requests.get("https://bankcsvconverter.com/login.html")
    login_soup = BeautifulSoup(login_response.text, 'html.parser')
    
    # Find login form
    forms = login_soup.find_all('form')
    for form in forms:
        print(f"\nFound form:")
        print(f"  Action: {form.get('action', 'Not specified')}")
        print(f"  Method: {form.get('method', 'Not specified')}")
        
        # Find input fields
        inputs = form.find_all('input')
        for inp in inputs:
            print(f"  Input: type={inp.get('type')}, name={inp.get('name')}, placeholder={inp.get('placeholder')}")

if __name__ == "__main__":
    analyze_stripe_flow()