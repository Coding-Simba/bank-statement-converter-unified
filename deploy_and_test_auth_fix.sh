#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying auth fixes and testing"
echo "================================"

# Deploy the fixed auth_cookie.py
echo "1. Deploying fixed auth_cookie.py..."
scp -i "$KEY_PATH" backend/api/auth_cookie.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo -e "\n2. Restarting backend..."
pkill -f "uvicorn main:app" || true
sleep 2
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
sleep 5

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend restarted successfully"
else
    echo "❌ Backend failed to start"
    tail -20 server.log
    exit 1
fi

echo -e "\n3. Testing auth flow with detailed debugging..."
echo "=============================================="

# Test with new user
TIMESTAMP=$(date +%s)
TEST_EMAIL="debug${TIMESTAMP}@example.com"

# Get CSRF
echo "a) Getting CSRF token..."
CSRF_FULL=$(curl -s -v -c debug_cookies.txt https://bankcsvconverter.com/v2/api/auth/csrf 2>&1)
CSRF_TOKEN=$(echo "$CSRF_FULL" | grep -o '"csrf_token":"[^"]*"' | cut -d'"' -f4)
echo "CSRF Token: ${CSRF_TOKEN:0:20}..."

# Register
echo -e "\nb) Registering user..."
REGISTER_RESP=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -b debug_cookies.txt -c debug_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"TestPass123!\",
        \"full_name\": \"Debug User\"
    }")
echo "Register response:"
echo "$REGISTER_RESP" | python3 -m json.tool

# Check cookies after registration
echo -e "\nc) Cookies after registration:"
cat debug_cookies.txt

# Test auth check with cookies
echo -e "\nd) Testing auth check..."
AUTH_CHECK=$(curl -s -v https://bankcsvconverter.com/v2/api/auth/check \
    -b debug_cookies.txt 2>&1)
echo "Auth check response:"
echo "$AUTH_CHECK" | grep -A50 "authenticated" | grep -B50 "}" | tail -20

# Check the access token directly on backend
echo -e "\ne) Checking token validation directly..."
ACCESS_TOKEN=$(grep "access_token" debug_cookies.txt | awk '{print $7}')
if [ -n "$ACCESS_TOKEN" ]; then
    echo "Access token found: ${ACCESS_TOKEN:0:50}..."
    
    # Decode token locally
    python3 << PYTHON
import jwt
import json

token = "$ACCESS_TOKEN"
try:
    # Decode without verification to see payload
    payload = jwt.decode(token, options={"verify_signature": False})
    print("Token payload:")
    print(json.dumps(payload, indent=2))
except Exception as e:
    print(f"Error decoding token: {e}")
PYTHON
fi

# Test profile endpoint
echo -e "\nf) Testing profile endpoint..."
PROFILE_RESP=$(curl -s https://bankcsvconverter.com/v2/api/auth/profile \
    -b debug_cookies.txt \
    -H "Cookie: access_token=$ACCESS_TOKEN")
echo "Profile response:"
echo "$PROFILE_RESP"

# Clean up
rm -f debug_cookies.txt

echo -e "\n4. Checking for common issues..."
echo "================================"

# Check if decode_token is working
echo "a) Testing decode_token function..."
python3 << 'PYTHON'
import sys
sys.path.append('.')
try:
    from utils.auth import decode_token
    print("✅ decode_token import successful")
except Exception as e:
    print(f"❌ decode_token import failed: {e}")
PYTHON

# Check User model
echo -e "\nb) Checking User model has is_active..."
if grep -q "is_active" models/database.py; then
    echo "✅ User model has is_active field"
else
    echo "❌ User model missing is_active field"
    echo "Adding is_active field..."
    sed -i '/email_verified = Column/a\    is_active = Column(Boolean, default=True)' models/database.py
fi

EOF

echo -e "\n✅ Auth fix deployment and testing complete!"