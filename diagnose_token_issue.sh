#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Diagnosing token validation issue"
echo "================================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking JWT secret configuration..."
echo "====================================="

# Check if SECRET_KEY is set
if grep -q "SECRET_KEY" .env 2>/dev/null; then
    echo "✅ SECRET_KEY found in .env"
else
    echo "❌ SECRET_KEY not found in .env"
    echo "Checking if it's hardcoded..."
    grep -n "SECRET_KEY" utils/auth.py || echo "No SECRET_KEY in auth.py"
fi

echo -e "\n2. Testing token validation directly..."
echo "======================================"

python3 << 'PYTHON'
import sys
sys.path.append('.')

try:
    from utils.auth import create_access_token, decode_token
    from datetime import datetime, timedelta
    
    # Create a test token
    test_data = {"sub": 999, "email": "test@example.com"}
    token = create_access_token(test_data)
    print(f"Created test token: {token[:50]}...")
    
    # Try to decode it
    decoded = decode_token(token)
    print(f"✅ Token decoded successfully: {decoded}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON

echo -e "\n3. Checking auth middleware..."
echo "==============================="

# Check get_current_user_cookie implementation
echo "Checking get_current_user_cookie function:"
grep -A20 "get_current_user_cookie" api/auth_cookie.py

echo -e "\n4. Testing with manual cookie header..."
echo "========================================"

# Create a test token and use it
python3 << 'PYTHON'
import subprocess
import json
from utils.auth import create_access_token

# Create token for existing user
token = create_access_token({"sub": 7, "email": "debug1754040881@example.com"})
print(f"Test token: {token[:50]}...")

# Test auth check with explicit cookie header
cmd = f'curl -s http://localhost:5000/v2/api/auth/check -H "Cookie: access_token={token}"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("\nAuth check with manual cookie:")
print(result.stdout)

# Test profile with explicit cookie header  
cmd = f'curl -s http://localhost:5000/v2/api/auth/profile -H "Cookie: access_token={token}"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("\nProfile with manual cookie:")
print(result.stdout)
PYTHON

echo -e "\n5. Checking cookie parsing..."
echo "============================"

# Test if FastAPI is parsing cookies correctly
python3 << 'PYTHON'
from fastapi import Request
from fastapi.testclient import TestClient
import sys
sys.path.append('.')

try:
    from main import app
    from utils.auth import create_access_token
    
    client = TestClient(app)
    
    # Create a test token
    token = create_access_token({"sub": 7, "email": "test@example.com"})
    
    # Test with cookies
    response = client.get("/v2/api/auth/check", cookies={"access_token": token})
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
PYTHON

echo -e "\n6. Checking backend logs for errors..."
echo "====================================="
tail -30 server.log | grep -E "ERROR|error|Error|Exception|Traceback" || echo "No recent errors in logs"

EOF