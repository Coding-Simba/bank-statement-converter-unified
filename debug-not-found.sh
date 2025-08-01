#!/bin/bash

# Debug Not Found Error
echo "🔍 Debugging Not Found Error"
echo "============================"
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

echo "1. Checking backend status..."
ps aux | grep -E "uvicorn|python.*main" | grep -v grep | head -3

echo -e "\n2. Testing all auth endpoints directly..."
echo "GET /api/auth/profile:"
curl -s http://localhost:5000/api/auth/profile -w "\nStatus: %{http_code}\n" | head -5

echo -e "\nPOST /api/auth/login:"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}' \
  -w "\nStatus: %{http_code}\n" -s | head -5

echo -e "\n3. Listing ALL available routes..."
cd /home/ubuntu/backend
cat > show_all_routes.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from main import app

print("=== ALL AVAILABLE ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"{route.methods} {route.path}")
EOF

python3 show_all_routes.py

echo -e "\n4. Checking nginx configuration..."
echo "Nginx sites-enabled:"
ls -la /etc/nginx/sites-enabled/

echo -e "\nNginx proxy configuration:"
grep -A 10 "location" /etc/nginx/sites-available/default | grep -E "(location|proxy_pass)" | head -20

echo -e "\n5. Testing through nginx (localhost)..."
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}' \
  -w "\nStatus: %{http_code}\n" -s | head -5

echo -e "\n6. Checking backend logs for 404 errors..."
tail -50 /home/ubuntu/backend/backend_clean.log | grep -E "(404|Not Found|path)" | tail -10

echo -e "\n7. Checking if auth router is properly included..."
grep -E "(auth|router)" /home/ubuntu/backend/main.py | head -20

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"