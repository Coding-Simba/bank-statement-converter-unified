#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Final Complete Authentication Test"
echo "================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Backend Status Check"
echo "====================="
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend not running - starting it..."
    source venv/bin/activate
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
    sleep 5
fi

echo -e "\n2. Complete Authentication Flow Test"
echo "===================================="

# Generate unique test email
TIMESTAMP=$(date +%s)
TEST_EMAIL="complete${TIMESTAMP}@example.com"
TEST_PASSWORD="CompleteTest123!"

echo "Test user: $TEST_EMAIL"

# Step 1: Get CSRF Token
echo -e "\n📍 Step 1: Getting CSRF token..."
CSRF_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf)
CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
if [ -n "$CSRF_TOKEN" ]; then
    echo "✅ Got CSRF token: ${CSRF_TOKEN:0:30}..."
else
    echo "❌ Failed to get CSRF token"
    echo "Response: $CSRF_RESPONSE"
    exit 1
fi

# Step 2: Register User
echo -e "\n📍 Step 2: Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -c auth_test_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"full_name\": \"Complete Test User\",
        \"company_name\": \"Test Corp\"
    }" \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY=$(echo "$REGISTER_RESPONSE" | sed 's/HTTP_CODE:[0-9]*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Registration successful"
    echo "$BODY" | python3 -m json.tool | grep -E "email|id|account_type"
else
    echo "❌ Registration failed (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

# Step 3: Check Cookies
echo -e "\n📍 Step 3: Verifying cookies..."
echo "Cookies set after registration:"
if [ -f auth_test_cookies.txt ]; then
    grep -E "access_token|refresh_token|csrf_token" auth_test_cookies.txt | while read line; do
        DOMAIN=$(echo "$line" | awk '{print $1}')
        PATH=$(echo "$line" | awk '{print $3}')
        NAME=$(echo "$line" | awk '{print $6}')
        VALUE=$(echo "$line" | awk '{print $7}')
        echo "  $NAME: domain=$DOMAIN, path=$PATH, value=${VALUE:0:50}..."
    done
    
    # Check if refresh_token has correct path
    if grep "refresh_token" auth_test_cookies.txt | grep -q "/v2/api/auth/refresh"; then
        echo "✅ Refresh token has correct path (/v2/api/auth/refresh)"
    else
        echo "❌ Refresh token has wrong path"
        grep "refresh_token" auth_test_cookies.txt
    fi
fi

# Step 4: Test Auth Check
echo -e "\n📍 Step 4: Testing auth check endpoint..."
AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check \
    -b auth_test_cookies.txt \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$AUTH_CHECK" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY=$(echo "$AUTH_CHECK" | sed 's/HTTP_CODE:[0-9]*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Auth check endpoint responded"
    if echo "$BODY" | grep -q '"authenticated":true'; then
        echo "✅ User is authenticated!"
        echo "$BODY" | python3 -m json.tool | grep -A10 "authenticated"
    else
        echo "❌ User NOT authenticated"
        echo "$BODY"
    fi
else
    echo "❌ Auth check failed (HTTP $HTTP_CODE)"
fi

# Step 5: Test Profile Access
echo -e "\n📍 Step 5: Testing profile endpoint..."
PROFILE=$(curl -s https://bankcsvconverter.com/v2/api/auth/profile \
    -b auth_test_cookies.txt \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$PROFILE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY=$(echo "$PROFILE" | sed 's/HTTP_CODE:[0-9]*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Profile access successful"
    echo "$BODY" | python3 -m json.tool | grep -E "email|full_name|account_type"
else
    echo "❌ Profile access failed (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

# Step 6: Test Logout
echo -e "\n📍 Step 6: Testing logout..."
LOGOUT=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/logout \
    -b auth_test_cookies.txt \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$LOGOUT" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Logout successful"
else
    echo "❌ Logout failed (HTTP $HTTP_CODE)"
fi

# Step 7: Verify logout worked
echo -e "\n📍 Step 7: Verifying user is logged out..."
AUTH_CHECK_AFTER=$(curl -s https://bankcsvconverter.com/v2/api/auth/check \
    -b auth_test_cookies.txt)
if echo "$AUTH_CHECK_AFTER" | grep -q '"authenticated":false'; then
    echo "✅ User successfully logged out"
else
    echo "❌ User still authenticated after logout"
fi

# Cleanup
rm -f auth_test_cookies.txt

echo -e "\n3. Summary"
echo "========="
echo "Authentication system test complete!"

EOF

echo -e "\n✅ Complete authentication test finished!"