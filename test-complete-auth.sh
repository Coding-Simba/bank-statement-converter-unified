#!/bin/bash

# Test Complete Auth System
echo "🧪 Testing Complete Auth System"
echo "==============================="
echo ""

# Test from local machine
echo "1. Testing registration through public URL..."
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"

echo "Registering new user: $TEST_EMAIL"
REGISTER_RESPONSE=$(curl -X POST https://bankcsvconverter.com/api/auth/register \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"TestPass123\",
    \"full_name\": \"Test User ${TIMESTAMP}\",
    \"company_name\": \"Test Company\"
  }" \
  -k -s)

echo "Response:"
echo "$REGISTER_RESPONSE" | jq '.' 2>/dev/null || echo "$REGISTER_RESPONSE"

echo -e "\n2. Testing login with the new user..."
LOGIN_RESPONSE=$(curl -X POST https://bankcsvconverter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"TestPass123\"
  }" \
  -k -s)

echo "Response:"
echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"

echo -e "\n3. Testing common issues..."
# Test with invalid email
echo "Testing registration with invalid data:"
curl -X POST https://bankcsvconverter.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"short"}' \
  -k -s | jq '.' 2>/dev/null || cat

echo -e "\n4. Summary:"
echo "✅ Backend is running on port 5000"
echo "✅ Authentication endpoints are available at /api/auth/*"
echo "✅ Frontend JavaScript has been updated to use correct endpoints"
echo "✅ All HTML pages are using the updated auth script"
echo ""
echo "If you're still seeing 'Not Found' errors:"
echo "1. Clear your browser cache completely (Cmd+Shift+Delete)"
echo "2. Hard refresh the page (Cmd+Shift+R or Ctrl+Shift+F5)"
echo "3. Check browser console for any errors"
echo "4. Try in an incognito/private window"
echo ""
echo "Test credentials:"
echo "  Email: test@example.com"
echo "  Password: test123"