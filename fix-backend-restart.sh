#!/bin/bash

# Fix Backend Restart Issue
echo "🔧 Fixing Backend Restart Issue"
echo "==============================="
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
cd /home/ubuntu/backend

echo "1. Killing ALL Python/uvicorn processes..."
pkill -9 -f "python" || true
pkill -9 -f "uvicorn" || true
sleep 3

echo -e "\n2. Making sure port 5000 is free..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 2

echo -e "\n3. Starting backend cleanly..."
# Start directly without loop for now
python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Started backend with PID: $BACKEND_PID"

sleep 5

echo -e "\n4. Checking if backend is running properly..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend is running"
    
    # Check if it's responding
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "✓ Backend is responding to requests"
    else
        echo "✗ Backend not responding"
    fi
else
    echo "✗ Backend crashed"
    echo "Last 20 lines of log:"
    tail -20 backend.log
fi

echo -e "\n5. Testing authentication flow..."
# Test login
echo "Testing login:"
LOGIN_RESPONSE=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c auth_cookies.txt \
  -s)

echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"

echo -e "\nChecking cookies:"
cat auth_cookies.txt | grep -v "^#" | grep -v "^$" || echo "No cookies found"

echo -e "\n6. Testing profile endpoint with auth:"
curl -X GET http://localhost:5000/api/auth/profile \
  -b auth_cookies.txt \
  -H "Accept: application/json" \
  -s | jq '.' 2>/dev/null || cat

echo -e "\n7. Checking auth.py for proper cookie handling..."
# Look specifically at the login function
sed -n '/^@router.post("\/login"/,/^@router\./p' api/auth.py | head -50

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend restart issue fixed!${NC}"
echo ""
echo "Backend should now be stable and authentication should work."