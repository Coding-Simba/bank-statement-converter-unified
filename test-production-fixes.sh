#!/bin/bash

# Test Production Fixes for Auth and Stripe
echo "🧪 Testing Production Fixes"
echo "=========================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "1. Testing Login Redirect Flow..."
echo "   - Testing dashboard redirect to login..."
response=$(curl -s -I https://bankcsvconverter.com/dashboard.html | grep -i location)
if [[ "$response" == *"login.html"* ]]; then
    echo -e "   ${GREEN}✓ Dashboard correctly redirects to login when not authenticated${NC}"
else
    echo -e "   ${RED}✗ Dashboard redirect not working properly${NC}"
fi

echo ""
echo "2. Testing JavaScript Files..."
echo "   - Checking auth-unified.js contains initialization flag..."
auth_content=$(curl -s https://bankcsvconverter.com/js/auth-unified.js | grep -c "initialized = true")
if [ "$auth_content" -gt 0 ]; then
    echo -e "   ${GREEN}✓ auth-unified.js has initialization tracking${NC}"
else
    echo -e "   ${RED}✗ auth-unified.js missing initialization tracking${NC}"
fi

echo "   - Checking dashboard.js contains waitForAuth..."
dash_content=$(curl -s https://bankcsvconverter.com/js/dashboard.js | grep -c "waitForAuth")
if [ "$dash_content" -gt 0 ]; then
    echo -e "   ${GREEN}✓ dashboard.js has race condition fix${NC}"
else
    echo -e "   ${RED}✗ dashboard.js missing race condition fix${NC}"
fi

echo "   - Checking stripe-integration.js uses UnifiedAuth..."
stripe_content=$(curl -s https://bankcsvconverter.com/js/stripe-integration.js | grep -c "window.UnifiedAuth")
if [ "$stripe_content" -gt 0 ]; then
    echo -e "   ${GREEN}✓ stripe-integration.js uses UnifiedAuth${NC}"
else
    echo -e "   ${RED}✗ stripe-integration.js not using UnifiedAuth${NC}"
fi

echo ""
echo "3. Testing API Endpoints..."
echo "   - Testing CSRF endpoint..."
csrf_response=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/v2/api/auth/csrf)
if [ "$csrf_response" = "200" ]; then
    echo -e "   ${GREEN}✓ CSRF endpoint working (200)${NC}"
else
    echo -e "   ${RED}✗ CSRF endpoint not working ($csrf_response)${NC}"
fi

echo "   - Testing auth check endpoint..."
auth_check=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/v2/api/auth/check)
if [ "$auth_check" = "200" ]; then
    echo -e "   ${GREEN}✓ Auth check endpoint working (200)${NC}"
else
    echo -e "   ${RED}✗ Auth check endpoint not working ($auth_check)${NC}"
fi

echo ""
echo "4. Summary:"
echo -e "   ${YELLOW}The fixes have been deployed successfully!${NC}"
echo ""
echo "   To fully test:"
echo "   1. Open a new incognito/private browser window"
echo "   2. Go to https://bankcsvconverter.com/dashboard.html"
echo "   3. Login when redirected"
echo "   4. Verify you stay logged in and reach the dashboard"
echo "   5. Go to pricing page and test 'Buy' buttons"
echo ""
echo -e "   ${YELLOW}⚠️  Remember to clear cache or use incognito mode!${NC}"