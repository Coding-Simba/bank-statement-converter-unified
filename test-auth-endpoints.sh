#!/bin/bash

# Test Authentication Endpoints
echo "🔍 Testing Authentication Endpoints"
echo "==================================="
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

# Test via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking backend process..."
ps aux | grep -E "uvicorn|python.*main:app" | grep -v grep | head -3

echo -e "\n2. Checking available endpoints in main.py..."
cd /home/ubuntu/backend
grep -E "(app.include_router|@app|@router)" main.py | head -20

echo -e "\n3. Testing different endpoint variations..."
echo -e "\n   Testing /api/auth/login (no v2):"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\n   Status: %{http_code}\n" -s | head -5

echo -e "\n   Testing /v2/auth/login (no api):"
curl -X POST http://localhost:5000/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\n   Status: %{http_code}\n" -s | head -5

echo -e "\n   Testing /auth/login (no prefix):"
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\n   Status: %{http_code}\n" -s | head -5

echo -e "\n4. Getting all available routes..."
cd /home/ubuntu/backend
cat > list_routes.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from main import app

print("Available routes:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {route.methods} {route.path}")
EOF

python3 list_routes.py | grep -E "(auth|login)" | head -20

echo -e "\n5. Checking nginx proxy configuration..."
grep -A 5 -B 2 "location.*api" /etc/nginx/sites-enabled/bank-statement-converter | head -20

echo -e "\n6. Testing through nginx (public endpoint)..."
curl -X POST https://bankcsvconverter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\n   Status: %{http_code}\n" -s -k | head -5

echo -e "\n7. Checking backend logs for recent requests..."
tail -30 backend.log | grep -E "(POST|GET|auth|login)" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Endpoint testing complete!${NC}"