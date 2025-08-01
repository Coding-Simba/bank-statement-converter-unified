#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying auth endpoint fixes"
echo "============================"

# Deploy the fixed auth-unified.js
echo "1. Deploying fixed auth-unified.js..."
scp -i "$KEY_PATH" js/auth-unified.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Verify the deployment
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

echo -e "\n2. Verifying endpoint fixes..."
echo "Checking auth endpoints in auth-unified.js:"
grep -n "/v2/api/auth" js/auth-unified.js | head -10

echo -e "\n3. Testing authentication flow..."

# Test CSRF endpoint
echo -e "\na) Testing CSRF endpoint from localhost:"
CSRF_TOKEN=$(curl -s http://localhost:5000/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
if [ -n "$CSRF_TOKEN" ]; then
    echo "✅ Got CSRF token: ${CSRF_TOKEN:0:20}..."
else
    echo "❌ Failed to get CSRF token"
fi

# Test login endpoint structure
echo -e "\nb) Testing login endpoint accepts POST:"
curl -X POST http://localhost:5000/v2/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"wrong"}' \
     -w "\nStatus: %{http_code}\n" \
     2>/dev/null

echo -e "\nc) Checking backend is still running:"
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running!"
fi

EOF

echo -e "\n✅ Auth endpoint fixes deployed!"
echo "================================"
echo "The authentication endpoints are now correctly configured:"
echo "- Login: /v2/api/auth/login"
echo "- Register: /v2/api/auth/register"
echo "- CSRF: /v2/api/auth/csrf"
echo ""
echo "Test at:"
echo "- Login: https://bankcsvconverter.com/login.html"
echo "- Signup: https://bankcsvconverter.com/signup.html"