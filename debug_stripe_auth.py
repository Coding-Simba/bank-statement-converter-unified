#!/usr/bin/env python3
"""Debug Stripe authentication issue"""

import sys
import os
sys.path.append('backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

# Test the token validation
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImV4cCI6MTc1NDEyMjg0NSwidHlwZSI6ImFjY2VzcyJ9.ovWO94nXxArUXwsVgByMBeLM0ZxMGEPfliqg2l-ZSVA"

print("Testing token validation...")

# Import auth utilities
from backend.utils.auth import decode_token, SECRET_KEY

print(f"SECRET_KEY being used: {repr(SECRET_KEY)}")

try:
    payload = decode_token(token)
    print("✓ Token is valid!")
    print(f"  User ID: {payload.get('sub')}")
    print(f"  Email: {payload.get('email')}")
except Exception as e:
    print(f"✗ Token validation failed: {e}")
    
    # Try to recreate the token with the same payload
    from backend.utils.auth import create_access_token
    from datetime import datetime, timedelta
    
    test_token = create_access_token({"sub": 1, "email": "test@example.com"})
    print(f"\nTest token created with current SECRET_KEY:")
    print(f"  {test_token}")
    
    try:
        test_payload = decode_token(test_token)
        print("✓ Test token validates successfully")
    except Exception as e2:
        print(f"✗ Even test token fails: {e2}")