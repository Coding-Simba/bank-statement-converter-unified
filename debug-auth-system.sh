#!/bin/bash

# Debug Auth System
echo "🔍 Debugging Authentication System"
echo "=================================="
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

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Checking if backend is running..."
ps aux | grep -E "uvicorn|python.*main" | grep -v grep | head -3

echo -e "\n2. Checking recent backend logs..."
tail -20 backend.log

echo -e "\n3. Looking at auth.py implementation..."
echo "Login endpoint:"
grep -A 30 "@router.post(\"/login\")" api/auth.py | head -40

echo -e "\n4. Checking for cookie imports..."
grep -E "(set_cookie|delete_cookie|Response|JSONResponse)" api/auth.py

echo -e "\n5. Testing with verbose output..."
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies_test.txt \
  -v 2>&1 | grep -E "(< HTTP|< Set-Cookie|{)" | head -20

echo -e "\n6. Checking nginx configuration for cookie forwarding..."
grep -A 10 -B 5 "proxy_pass" /etc/nginx/sites-available/default | grep -E "(proxy_pass|proxy_set_header|Cookie)" | head -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"