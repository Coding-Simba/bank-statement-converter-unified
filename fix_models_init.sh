#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing models/__init__.py syntax error"
echo "====================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Fixing models/__init__.py..."
cat > models/__init__.py << 'PYTHON'
"""Database models package."""
from .session import Session
PYTHON

echo "2. Verifying the fix..."
python3 -m py_compile models/__init__.py && echo "✅ Syntax is now valid" || echo "❌ Still has syntax error"

echo -e "\n3. Restarting backend..."
pkill -f "uvicorn main:app" || true
sleep 2

source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &

sleep 5

echo -e "\n4. Checking if backend is running..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running!"
    
    echo -e "\n5. Testing endpoints..."
    echo "Testing /v2/api/auth/register:"
    curl -X POST http://localhost:5000/v2/api/auth/register \
         -H "Content-Type: application/json" \
         -d '{}' \
         -w "\nStatus: %{http_code}\n" \
         2>/dev/null || echo "Failed"
         
    echo -e "\nTesting /v2/api/auth/csrf:"
    curl -s http://localhost:5000/v2/api/auth/csrf -w "\nStatus: %{http_code}\n" || echo "Failed"
else
    echo "❌ Backend failed to start"
    echo "Error log:"
    tail -30 server.log
fi

EOF