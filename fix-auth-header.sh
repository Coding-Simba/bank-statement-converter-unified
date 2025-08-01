#!/bin/bash

# Fix Auth Header
echo "🔧 Fixing Auth Header for API Requests"
echo "====================================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Updating auth-unified.js to include Authorization header..."
# Create a fixed version
python3 << 'EOF'
import re

# Read the current file
with open('js/auth-unified-1754069674.js', 'r') as f:
    content = f.read()

# Find the makeAuthenticatedRequest method and update it
# Look for the pattern and replace
pattern = r'(async makeAuthenticatedRequest\(url, options = \{\}\) \{[^}]*?)(const response = await fetch\(fullUrl, \{[^}]*?\})'

def replacement(match):
    method_start = match.group(1)
    fetch_call = match.group(2)
    
    # Check if we need to add the Authorization header logic
    if 'Authorization' not in fetch_call:
        # Add logic to include Authorization header if we have a token
        new_code = method_start + '''// Add Authorization header if we have a token
            const authHeaders = {...options.headers};
            if (this.user && localStorage.getItem('access_token')) {
                authHeaders['Authorization'] = 'Bearer ' + localStorage.getItem('access_token');
            }
            
            ''' + fetch_call.replace('headers: {', 'headers: {').replace('...options.headers,', '...authHeaders,')
        return new_code
    return match.group(0)

# Apply the fix
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Also update the retry logic after token refresh
retry_pattern = r'(// Retry request\s*return fetch\(fullUrl, \{[^}]*?)(credentials: \'include\',)'

def retry_replacement(match):
    before = match.group(1)
    credentials = match.group(2)
    
    if 'Authorization' not in before:
        return before + '''...options,
                        ''' + credentials + '''
                        headers: {
                            ...authHeaders,
                            'X-CSRF-Token': this.csrfToken
                        }'''
    return match.group(0)

content = re.sub(retry_pattern, retry_replacement, content, flags=re.DOTALL)

# Write the updated file
with open('js/auth-unified-1754069674.js', 'w') as f:
    f.write(content)

print("✓ Updated makeAuthenticatedRequest to include Authorization header")
EOF

echo -e "\n2. Also updating the login method to store the access token..."
# Ensure access token is stored in localStorage
sed -i '/this\.user = data\.user;/a\            localStorage.setItem('"'"'access_token'"'"', data.access_token);' js/auth-unified-1754069674.js

echo -e "\n3. Verifying the changes..."
grep -A 15 "makeAuthenticatedRequest" js/auth-unified-1754069674.js | head -20

echo -e "\n4. Clearing cache by updating version..."
TIMESTAMP=$(date +%s)
find . -name "*.html" -type f -exec sed -i "s|auth-unified-1754069674\.js|auth-unified-1754069674.js?v=${TIMESTAMP}|g" {} \;

echo -e "\n5. Testing the fix..."
# Restart backend to ensure clean state
pkill -f "uvicorn main:app" || true
sleep 2
cd /home/ubuntu/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
sleep 5

echo -e "\n6. Manual test with proper headers..."
# Login and test
LOGIN_RESPONSE=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "Testing Stripe with auth header:"
    curl -X POST http://localhost:5000/api/stripe/create-checkout-session \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"price_id": "price_1RqZtaKwQLBjGTW9w20V3Hst"}' \
      -s | python3 -c "import sys, json; d=json.load(sys.stdin); print('✓ Success!' if 'checkout_url' in d else '✗ Failed')"
fi

ENDSSH

echo ""
echo -e "${GREEN}✓ Auth header fix complete!${NC}"
echo ""
echo "The API requests now properly include the Authorization header."
echo "Clear your browser cache and try again at: https://bankcsvconverter.com/pricing.html"