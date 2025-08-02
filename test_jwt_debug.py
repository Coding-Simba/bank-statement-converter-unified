#!/usr/bin/env python3
"""Debug JWT token validation"""

import sys
import os
import jwt
from datetime import datetime

# Add backend to path
sys.path.append('backend')

# Load environment
from dotenv import load_dotenv
load_dotenv('backend/.env')

# Import auth utilities
from backend.utils.auth import decode_token, SECRET_KEY, ALGORITHM

print(f"SECRET_KEY: {SECRET_KEY}")
print(f"ALGORITHM: {ALGORITHM}")

# Test token from the login response
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImV4cCI6MTc1NDIwNzg2MiwidHlwZSI6ImFjY2VzcyJ9.so3pK_1QmTxDy7yGw1lkjRc2MlEHcu7vCXROVZVgoeM"

print(f"\nDecoding token...")
try:
    payload = decode_token(test_token)
    print(f"✓ Token decoded successfully!")
    print(f"  User ID: {payload.get('sub')}")
    print(f"  Email: {payload.get('email')}")
    print(f"  Type: {payload.get('type')}")
    
    # Check expiration
    exp = payload.get('exp')
    if exp:
        exp_date = datetime.fromtimestamp(exp)
        print(f"  Expires: {exp_date}")
        print(f"  Expired: {exp_date < datetime.now()}")
        
except Exception as e:
    print(f"✗ Token decode failed: {e}")
    
    # Try manual decode without validation to see the payload
    try:
        unverified = jwt.decode(test_token, options={"verify_signature": False})
        print(f"\nUnverified payload:")
        for key, value in unverified.items():
            print(f"  {key}: {value}")
    except:
        pass