#!/usr/bin/env python3
"""Test environment loading on server"""

import os
import sys

# First check raw environment
print("=== RAW ENVIRONMENT ===")
print(f"JWT_SECRET_KEY from env: {os.environ.get('JWT_SECRET_KEY')}")
print(f"SECRET_KEY from env: {os.environ.get('SECRET_KEY')}")

# Load dotenv
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"\n=== LOADING DOTENV from {dotenv_path} ===")
load_dotenv(dotenv_path)

print(f"JWT_SECRET_KEY after dotenv: {os.environ.get('JWT_SECRET_KEY')}")
print(f"SECRET_KEY after dotenv: {os.environ.get('SECRET_KEY')}")

# Import auth module
print("\n=== IMPORTING AUTH MODULE ===")
from utils.auth import SECRET_KEY, create_access_token, decode_token

print(f"SECRET_KEY in auth module: {SECRET_KEY}")

# Test token creation and validation
print("\n=== TESTING TOKEN CREATION ===")
test_token = create_access_token({"sub": 1, "email": "test@example.com"})
print(f"Created token: {test_token[:50]}...")

try:
    payload = decode_token(test_token)
    print("✓ Token validates with same module")
except Exception as e:
    print(f"✗ Token validation failed: {e}")