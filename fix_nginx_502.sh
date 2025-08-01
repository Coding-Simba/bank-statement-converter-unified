#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx 502 errors"
echo "======================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking nginx error log..."
echo "============================="
sudo tail -20 /var/log/nginx/error.log | grep -E "502|upstream" || echo "No recent 502 errors in nginx log"

echo -e "\n2. Testing backend directly..."
echo "=============================="
curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool || echo "Backend not responding"

echo -e "\n3. Checking backend process..."
echo "============================="
ps aux | grep uvicorn | grep -v grep

echo -e "\n4. Restarting everything properly..."
echo "=================================="

# Kill all uvicorn processes
sudo pkill -f uvicorn || true
sleep 3

# Start backend
cd /home/ubuntu/bank-statement-converter/backend
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > /dev/null 2>&1 &
sleep 5

# Verify it's running
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend started"
    
    # Test directly
    echo -e "\nDirect test:"
    curl -s http://localhost:5000/v2/api/auth/csrf | head -1
else
    echo "❌ Backend failed to start"
fi

echo -e "\n5. Restarting nginx..."
echo "===================="
sudo systemctl restart nginx

echo -e "\n6. Final test through nginx..."
echo "============================="
sleep 2

# Test through nginx
curl -s -m 5 https://bankcsvconverter.com/v2/api/auth/csrf | python3 -m json.tool || echo "Still getting errors"

# If still failing, check if it's the /v2 prefix
echo -e "\n7. Testing without /v2 prefix..."
echo "==============================="
curl -s http://localhost:5000/api/auth/csrf | python3 -m json.tool || echo "No /api/auth/csrf endpoint"

echo -e "\n8. Checking actual routes..."
echo "=========================="
curl -s http://localhost:5000/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Available auth routes:')
for path in sorted(data.get('paths', {}).keys()):
    if 'auth' in path:
        print(f'  {path}')
" 2>/dev/null || echo "Could not get routes"

EOF