#!/bin/bash

# Test authentication endpoints
echo "🧪 Testing Bank Statement Converter Authentication"
echo "================================================"

API_BASE="https://bankcsvconverter.com/api"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "1. Testing Session Creation (Anonymous User)"
echo "-------------------------------------------"
SESSION_RESPONSE=$(curl -s "$API_BASE/auth/session")
echo "Response: $SESSION_RESPONSE"
if [[ $SESSION_RESPONSE == *"session_id"* ]]; then
    echo -e "${GREEN}✓ Session endpoint working${NC}"
else
    echo -e "${RED}✗ Session endpoint failed${NC}"
fi

echo ""
echo "2. Testing Conversion Limits (Anonymous User)"
echo "--------------------------------------------"
LIMIT_RESPONSE=$(curl -s "$API_BASE/check-limit")
echo "Response: $LIMIT_RESPONSE"
if [[ $LIMIT_RESPONSE == *"daily_limit"* ]]; then
    echo -e "${GREEN}✓ Limit check working${NC}"
    echo "  - Daily limit: $(echo $LIMIT_RESPONSE | grep -o '"daily_limit":[0-9]*' | cut -d: -f2)"
    echo "  - Daily used: $(echo $LIMIT_RESPONSE | grep -o '"daily_used":[0-9]*' | cut -d: -f2)"
else
    echo -e "${RED}✗ Limit check failed${NC}"
fi

echo ""
echo "3. Testing User Registration"
echo "---------------------------"
TEST_EMAIL="test$(date +%s)@example.com"
REGISTER_DATA='{
    "email": "'$TEST_EMAIL'",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "company_name": "Test Company"
}'

echo "Registering user: $TEST_EMAIL"
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d "$REGISTER_DATA")

if [[ $REGISTER_RESPONSE == *"access_token"* ]]; then
    echo -e "${GREEN}✓ Registration successful${NC}"
    ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "  - Token received (first 20 chars): ${ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Registration failed${NC}"
    echo "  - Response: $REGISTER_RESPONSE"
fi

echo ""
echo "4. Testing Login"
echo "---------------"
LOGIN_DATA='{
    "email": "'$TEST_EMAIL'",
    "password": "TestPassword123!"
}'

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA")

if [[ $LOGIN_RESPONSE == *"access_token"* ]]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "  - Response: $LOGIN_RESPONSE"
fi

echo ""
echo "5. Testing Authenticated User Profile"
echo "------------------------------------"
if [ ! -z "$ACCESS_TOKEN" ]; then
    PROFILE_RESPONSE=$(curl -s "$API_BASE/auth/profile" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [[ $PROFILE_RESPONSE == *"email"* ]]; then
        echo -e "${GREEN}✓ Profile access successful${NC}"
        echo "  - User: $(echo $PROFILE_RESPONSE | grep -o '"email":"[^"]*' | cut -d'"' -f4)"
        echo "  - Account type: $(echo $PROFILE_RESPONSE | grep -o '"account_type":"[^"]*' | cut -d'"' -f4)"
    else
        echo -e "${RED}✗ Profile access failed${NC}"
        echo "  - Response: $PROFILE_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ Skipping - No access token available${NC}"
fi

echo ""
echo "6. Testing Conversion Limits (Authenticated User)"
echo "------------------------------------------------"
if [ ! -z "$ACCESS_TOKEN" ]; then
    AUTH_LIMIT_RESPONSE=$(curl -s "$API_BASE/check-limit" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [[ $AUTH_LIMIT_RESPONSE == *"daily_limit"* ]]; then
        echo -e "${GREEN}✓ Authenticated limit check working${NC}"
        echo "  - Daily limit: $(echo $AUTH_LIMIT_RESPONSE | grep -o '"daily_limit":[0-9]*' | cut -d: -f2)"
        echo "  - Account type: $(echo $AUTH_LIMIT_RESPONSE | grep -o '"account_type":"[^"]*' | cut -d'"' -f4)"
    else
        echo -e "${RED}✗ Authenticated limit check failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping - No access token available${NC}"
fi

echo ""
echo "================================================"
echo "📋 Summary"
echo "================================================"
echo ""
echo "Frontend Pages to Test:"
echo "  - Sign Up: https://bankcsvconverter.com/signup.html"
echo "  - Login: https://bankcsvconverter.com/login.html"
echo "  - Dashboard: https://bankcsvconverter.com/dashboard.html"
echo ""
echo "OAuth Endpoints (requires credentials in .env):"
echo "  - Google: https://bankcsvconverter.com/api/auth/google"
echo "  - Microsoft: https://bankcsvconverter.com/api/auth/microsoft"
echo ""
echo -e "${YELLOW}Note: OAuth testing requires valid credentials in the server's .env file${NC}"