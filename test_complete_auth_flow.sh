#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Testing Complete Authentication Flow"
echo "==================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Testing Registration Flow"
echo "============================"

# Get CSRF token
echo "a) Getting CSRF token..."
CSRF_RESPONSE=$(curl -s -c cookies.txt https://bankcsvconverter.com/v2/api/auth/csrf)
CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

if [ -n "$CSRF_TOKEN" ]; then
    echo "✅ Got CSRF token: ${CSRF_TOKEN:0:20}..."
else
    echo "❌ Failed to get CSRF token"
    echo "Response: $CSRF_RESPONSE"
    exit 1
fi

# Try to register a test user
echo -e "\nb) Attempting to register test user..."
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"

REGISTER_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -b cookies.txt -c cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"TestPass123!\",
        \"full_name\": \"Test User\",
        \"company_name\": \"Test Company\"
    }" \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$REGISTER_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$REGISTER_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//')

echo "Registration Response (Status: $HTTP_STATUS):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Registration successful!"
else
    echo "❌ Registration failed with status $HTTP_STATUS"
fi

echo -e "\n2. Testing Login Flow"
echo "===================="

# Get fresh CSRF token
echo "a) Getting fresh CSRF token..."
CSRF_RESPONSE=$(curl -s -c cookies2.txt https://bankcsvconverter.com/v2/api/auth/csrf)
CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

echo -e "\nb) Attempting to login..."
LOGIN_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/login \
    -b cookies2.txt -c cookies2.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"TestPass123!\",
        \"remember_me\": true
    }" \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$LOGIN_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$LOGIN_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//')

echo "Login Response (Status: $HTTP_STATUS):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Login successful!"
    
    # Check cookies
    echo -e "\nc) Checking cookies set..."
    echo "Cookies received:"
    cat cookies2.txt | grep -E "access_token|refresh_token|csrf_token" || echo "No auth cookies found"
else
    echo "❌ Login failed with status $HTTP_STATUS"
fi

echo -e "\n3. Testing Auth Check"
echo "===================="

CHECK_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/check \
    -b cookies2.txt \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$CHECK_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$CHECK_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//')

echo "Auth Check Response (Status: $HTTP_STATUS):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo -e "\n4. Testing Profile Access"
echo "======================="

PROFILE_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/profile \
    -b cookies2.txt \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$PROFILE_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$PROFILE_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//')

echo "Profile Response (Status: $HTTP_STATUS):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo -e "\n5. Testing Logout"
echo "================"

LOGOUT_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/logout \
    -b cookies2.txt -c cookies2.txt \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$LOGOUT_RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$LOGOUT_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*//')

echo "Logout Response (Status: $HTTP_STATUS):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

# Clean up
rm -f cookies.txt cookies2.txt

echo -e "\n6. Checking Frontend Integration"
echo "================================"

# Test if login page loads
echo "a) Testing login page loads..."
LOGIN_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/login.html)
if [ "$LOGIN_PAGE_STATUS" = "200" ]; then
    echo "✅ Login page loads successfully"
else
    echo "❌ Login page failed to load (Status: $LOGIN_PAGE_STATUS)"
fi

# Test if signup page loads
echo -e "\nb) Testing signup page loads..."
SIGNUP_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/signup.html)
if [ "$SIGNUP_PAGE_STATUS" = "200" ]; then
    echo "✅ Signup page loads successfully"
else
    echo "❌ Signup page failed to load (Status: $SIGNUP_PAGE_STATUS)"
fi

# Check for JavaScript errors
echo -e "\nc) Checking for auth script..."
curl -s https://bankcsvconverter.com/js/auth-unified.js | head -5 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ auth-unified.js is accessible"
else
    echo "❌ auth-unified.js not found"
fi

EOF

echo -e "\n✅ Complete Authentication Flow Test Finished!"