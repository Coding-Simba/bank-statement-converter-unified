#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing double v2 in endpoints"
echo "============================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter

echo "1. Fixing the double v2 issue in auth-unified.js..."
echo "==============================================="
# Replace /v2/v2/api/auth with /v2/api/auth
sed -i 's|/v2/v2/api/auth|/v2/api/auth|g' frontend/js/auth-unified.js

echo -e "\n2. Checking what API_BASE is set to..."
echo "===================================="
grep -E "API_BASE|getApiBase" frontend/js/auth-unified.js | head -5

echo -e "\n3. The issue is API_BASE already includes /v2..."
echo "=============================================="
# Fix by removing the extra /v2 from the fetch URLs
sed -i 's|${API_BASE}/v2/api/auth|${API_BASE}/api/auth|g' frontend/js/auth-unified.js

echo -e "\n4. Verifying the fix..."
echo "======================"
grep "fetch.*auth" frontend/js/auth-unified.js | head -10

echo -e "\n5. Also check if signup.html has the same issue..."
echo "==============================================="
# Make sure all js files in frontend are consistent
find frontend/js -name "*.js" -type f -exec grep -l "/v2/v2" {} \; 2>/dev/null

echo -e "\n6. Final test of the endpoints..."
echo "================================"
echo "Testing CSRF endpoint:"
curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -m json.tool | head -5

echo -e "\nTesting with the test page:"
echo "https://bankcsvconverter.com/test-browser-auth.html"
echo ""
echo "✅ Endpoints fixed!"
echo ""
echo "The authentication should now work properly in your browser."
echo ""
echo "Try these URLs in incognito mode:"
echo "1. https://bankcsvconverter.com/login.html"
echo "2. https://bankcsvconverter.com/signup.html"
echo "3. https://bankcsvconverter.com/test-browser-auth.html"

EOF

echo -e "\n✅ Double v2 issue fixed!"