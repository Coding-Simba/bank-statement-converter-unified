#!/bin/bash

# Check Login Page
echo "🔍 Checking Login Page Configuration"
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

# Check via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking which JS files are loaded in login.html..."
grep -E '<script.*src.*\.js' login.html | grep -v "<!--" | head -20

echo -e "\n2. Checking if there's a different auth script being used..."
grep -E 'auth.*\.js|login.*\.js' login.html | head -10

echo -e "\n3. Looking for hardcoded API endpoints in login.html..."
grep -E "fetch.*api|/v2/api|/api/auth" login.html | head -10

echo -e "\n4. Checking inline scripts in login.html..."
sed -n '/<script>/,/<\/script>/p' login.html | grep -E "fetch|api/auth|v2/api" | head -20

echo -e "\n5. Finding all files with v2/api references..."
grep -r "v2/api/auth" . --include="*.js" --include="*.html" --exclude-dir="node_modules" --exclude-dir=".git" | grep -v ".old" | head -20

echo -e "\n6. Checking the actual auth-unified.js being served..."
ls -la js/auth-unified.js
head -20 js/auth-unified.js | grep -n "v2"

echo -e "\n7. Testing login with curl to confirm backend works..."
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s | jq '.access_token' | cut -c1-50

ENDSSH

echo ""
echo -e "${GREEN}✓ Check complete!${NC}"