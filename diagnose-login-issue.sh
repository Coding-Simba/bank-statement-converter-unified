#!/bin/bash

# Diagnose Login Issue Script
# Checks what's happening with the login flow

echo "🔍 Diagnosing Login Issue"
echo "========================"
echo ""

# Test credentials (you'll need to update these)
TEST_EMAIL="test@example.com"
TEST_PASSWORD="TestPassword123!"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "1. Testing authentication endpoints..."

# Get CSRF token
echo "   Getting CSRF token..."
csrf_response=$(curl -s -c cookies.txt https://bankcsvconverter.com/v2/api/auth/csrf)
csrf_token=$(echo "$csrf_response" | grep -o '"csrf_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$csrf_token" ]; then
    echo -e "${GREEN}✓ CSRF token obtained: ${csrf_token:0:20}...${NC}"
else
    echo -e "${RED}✗ Failed to get CSRF token${NC}"
    exit 1
fi

echo ""
echo "2. Testing login endpoint directly..."

# Test login
login_response=$(curl -s -w "\n%{http_code}" -X POST https://bankcsvconverter.com/v2/api/auth/login \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $csrf_token" \
    -b cookies.txt \
    -c cookies.txt \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"remember_me\":false}")

http_code=$(echo "$login_response" | tail -n1)
response_body=$(echo "$login_response" | head -n-1)

echo "   HTTP Status: $http_code"
echo "   Response: $response_body"

echo ""
echo "3. Checking authentication status..."

# Check auth
auth_check=$(curl -s -b cookies.txt https://bankcsvconverter.com/v2/api/auth/check)
echo "   Auth check response: $auth_check"

echo ""
echo "4. Testing dashboard access..."

# Try to access dashboard
dashboard_response=$(curl -s -o /dev/null -w "%{http_code}" -b cookies.txt https://bankcsvconverter.com/dashboard.html)
echo "   Dashboard access: HTTP $dashboard_response"

echo ""
echo "5. Checking redirect behavior..."

# Test login page with redirect
redirect_test=$(curl -s -I "https://bankcsvconverter.com/login.html?redirect=dashboard" | grep -i location || echo "No redirect")
echo "   Login page redirect test: $redirect_test"

echo ""
echo "6. Cookie inspection..."
echo "   Cookies set:"
cat cookies.txt | grep -E "(access_token|refresh_token|csrf_token)" | while read line; do
    if [[ $line == *"access_token"* ]]; then
        echo -e "   ${GREEN}✓ access_token cookie found${NC}"
    elif [[ $line == *"refresh_token"* ]]; then
        echo -e "   ${GREEN}✓ refresh_token cookie found${NC}"
    elif [[ $line == *"csrf_token"* ]]; then
        echo -e "   ${GREEN}✓ csrf_token cookie found${NC}"
    fi
done

echo ""
echo "7. JavaScript console test..."
echo "   To test in browser console:"
echo ""
echo "   // Check if UnifiedAuth is loaded"
echo "   console.log('UnifiedAuth exists:', typeof window.UnifiedAuth);"
echo ""
echo "   // Check authentication status"
echo "   console.log('Is authenticated:', window.UnifiedAuth.isAuthenticated());"
echo ""
echo "   // Check user data"
echo "   console.log('User data:', window.UnifiedAuth.getUser());"
echo ""
echo "   // Test login function"
echo "   await window.UnifiedAuth.login('$TEST_EMAIL', '$TEST_PASSWORD', false);"
echo ""

echo "8. Common issues to check:"
echo "   - Is the auth-unified.js script loading?"
echo "   - Are cookies being set with correct domain?"
echo "   - Is CSRF token being included in requests?"
echo "   - Is the redirect parameter being handled?"
echo "   - Are there any JavaScript errors in console?"

# Clean up
rm -f cookies.txt

echo ""
echo -e "${YELLOW}⚠️  Note: Update TEST_EMAIL and TEST_PASSWORD in this script with valid credentials${NC}"