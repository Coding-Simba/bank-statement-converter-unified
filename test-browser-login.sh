#!/bin/bash

# Test Browser Login
echo "🌐 Testing Browser Login"
echo "======================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

echo "1. Testing through public URL (simulating browser)..."
# Test with user agent and accept headers like a browser
curl -X POST https://bankcsvconverter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Origin: https://bankcsvconverter.com" \
  -H "Referer: https://bankcsvconverter.com/login.html" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies_browser.txt \
  -w "\nStatus: %{http_code}\n" \
  -k -s | jq '.' 2>/dev/null || cat

echo -e "\n2. Checking cookies set by server..."
cat cookies_browser.txt | grep -v "^#" | grep -v "^$"

echo -e "\n3. Testing authenticated request..."
curl -X GET https://bankcsvconverter.com/api/auth/profile \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Referer: https://bankcsvconverter.com/dashboard.html" \
  -b cookies_browser.txt \
  -w "\nStatus: %{http_code}\n" \
  -k -s | jq '.' 2>/dev/null || cat

echo -e "\n4. Checking backend logs for login attempts..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend
echo "Recent login attempts:"
tail -50 backend.log | grep -E "(login|auth|POST.*200|POST.*401)" | tail -10
ENDSSH

echo ""
echo -e "${GREEN}✓ Browser login test complete!${NC}"
echo ""
echo "Test the login yourself at:"
echo "  URL: https://bankcsvconverter.com/login.html"
echo "  Email: test@example.com"
echo "  Password: test123"
echo ""
echo "The auth system should now:"
echo "  ✓ Accept login credentials"
echo "  ✓ Set authentication cookies"
echo "  ✓ Redirect to dashboard after login"
echo "  ✓ Maintain session across pages"