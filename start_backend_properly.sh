#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Starting backend properly"
echo "========================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Killing any existing backend processes..."
pkill -f "uvicorn main:app" || true
sleep 2

echo -e "\n2. Starting backend in background..."
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &

echo "Waiting for backend to start..."
sleep 5

echo -e "\n3. Verifying backend is running..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running!"
    echo "Process info:"
    ps aux | grep "uvicorn main:app" | grep -v grep
    
    echo -e "\n4. Testing authentication endpoints..."
    
    echo -e "\na) Getting CSRF token:"
    CSRF_RESPONSE=$(curl -s http://localhost:5000/v2/api/auth/csrf)
    echo "$CSRF_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CSRF_RESPONSE"
    
    echo -e "\nb) Testing register endpoint exists:"
    curl -I http://localhost:5000/v2/api/auth/register 2>/dev/null | head -1
    
    echo -e "\nc) Testing login endpoint exists:"
    curl -I http://localhost:5000/v2/api/auth/login 2>/dev/null | head -1
    
    echo -e "\nd) Listing all available routes:"
    echo "Auth routes:"
    curl -s http://localhost:5000/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for path, methods in data.get('paths', {}).items():
    if '/auth' in path:
        print(f'{path}: {list(methods.keys())}')
" 2>/dev/null || echo "Could not parse routes"

    echo -e "\n5. Testing from external (through nginx):"
    echo "Testing https://bankcsvconverter.com/v2/api/auth/csrf"
    curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -m json.tool 2>/dev/null || echo "Failed to get CSRF token"
    
else
    echo "❌ Backend is not running!"
    echo "Last 30 lines of server.log:"
    tail -30 server.log
fi

EOF

echo -e "\n✅ Backend deployment complete!"
echo "================================"
echo "Test signup at: https://bankcsvconverter.com/signup.html"