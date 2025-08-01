#!/bin/bash

# Debug Registration Issue
echo "🔍 Debugging Registration Issue"
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

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Checking if backend is running..."
ps aux | grep -E "uvicorn|python.*main" | grep -v grep | head -3

echo -e "\n2. Testing registration endpoint directly..."
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "TestPass123",
    "full_name": "Test User",
    "company_name": "Test Company"
  }' \
  -w "\nStatus: %{http_code}\n" -s | head -20

echo -e "\n3. Checking recent backend logs for errors..."
tail -50 backend_clean.log | grep -E "(register|Register|ERROR|error)" | tail -20

echo -e "\n4. Checking auth.py for register endpoint..."
grep -A 20 "@router.post(\"/register" api/auth.py | head -30

echo -e "\n5. Testing which endpoints are available..."
curl -s http://localhost:5000/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Available auth endpoints:')
for path in data.get('paths', {}):
    if '/auth/' in path:
        methods = list(data['paths'][path].keys())
        print(f'  {methods} {path}')
" 2>/dev/null || echo "Could not parse OpenAPI spec"

echo -e "\n6. Checking signup.html to see what endpoint it's calling..."
cd /home/ubuntu/bank-statement-converter
grep -E "fetch.*register|api/auth/register|v2/api" signup.html | head -10

echo -e "\n7. Checking which JS file is loaded in signup.html..."
grep -E '<script.*auth.*\.js' signup.html | head -10

echo -e "\n8. Looking at recent nginx access logs for register attempts..."
sudo tail -50 /var/log/nginx/access.log | grep -E "register|signup" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"