#!/bin/bash

# Redeploy Frontend with Fixed Auth
echo "🚀 Redeploying Frontend with Fixed Auth"
echo "======================================="
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

echo "1. Checking current auth-unified.js on server..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
echo "Checking for v2 in auth-unified.js:"
grep -c "/v2/api/auth" /home/ubuntu/bank-statement-converter/js/auth-unified.js || echo "0 occurrences"
ENDSSH

echo -e "\n2. Uploading corrected auth-unified.js..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-unified.js \
    "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/js/"

echo -e "\n3. Verifying the update..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "Checking updated file:"
grep -c "/v2/api/auth" js/auth-unified.js && echo "❌ Still has v2 paths!" || echo "✓ v2 paths removed"

echo -e "\nFirst few auth endpoints in file:"
grep -n "fetch.*api/auth" js/auth-unified.js | head -5

echo -e "\n4. Clearing browser cache by updating timestamp..."
touch js/auth-unified.js

echo -e "\n5. Also checking if there are other auth files being used..."
find . -name "*.js" -type f -exec grep -l "v2/api/auth" {} \; | head -10

echo -e "\n6. Testing with correct endpoints..."
echo "Testing login endpoint directly:"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\nStatus: %{http_code}\n" -s | jq '.' 2>/dev/null || cat

ENDSSH

echo ""
echo -e "${GREEN}✓ Frontend redeployed!${NC}"
echo ""
echo "Clear your browser cache (Cmd+Shift+R or Ctrl+Shift+R) and try again at:"
echo "https://bankcsvconverter.com/login.html"