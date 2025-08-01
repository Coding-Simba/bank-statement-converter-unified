#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Checking backend routes configuration"
echo "===================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking if auth_cookie.py exists..."
if [ -f "api/auth_cookie.py" ]; then
    echo "✅ auth_cookie.py exists"
    echo "Checking register endpoint:"
    grep -n "register" api/auth_cookie.py | head -5
else
    echo "❌ auth_cookie.py not found!"
fi

echo -e "\n2. Checking main.py for v2 auth routes..."
if [ -f "main.py" ]; then
    echo "Checking auth imports:"
    grep -E "auth_cookie|auth" main.py | grep import
    echo -e "\nChecking router includes:"
    grep -E "include_router.*auth" main.py
else
    echo "❌ main.py not found!"
fi

echo -e "\n3. Checking if backend is running..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running"
    echo "Process info:"
    ps aux | grep -E "uvicorn main:app" | grep -v grep
else
    echo "❌ Backend is not running!"
fi

echo -e "\n4. Checking nginx configuration for v2 routes..."
if sudo grep -q "location /v2/" /etc/nginx/sites-available/bank-converter; then
    echo "✅ Nginx has v2 location block"
    sudo grep -A10 "location /v2/" /etc/nginx/sites-available/bank-converter
else
    echo "❌ Nginx missing v2 location block"
fi

echo -e "\n5. Testing the register endpoint directly..."
echo "Testing: http://localhost:5000/api/auth/register"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5000/api/auth/register || echo "Failed to connect"

echo -e "\nTesting: http://localhost:5000/v2/api/auth/register"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5000/v2/api/auth/register || echo "Failed to connect"

echo -e "\n6. Checking server logs for errors..."
if [ -f "server.log" ]; then
    echo "Recent errors in server.log:"
    tail -20 server.log | grep -E "ERROR|error|Error|Exception" || echo "No recent errors"
fi

EOF