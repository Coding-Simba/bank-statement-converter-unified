#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing auth check logic and restarting backend"
echo "============================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. First, let's debug why auth check is failing..."
echo "================================================"

# Create a debug script to test token validation
cat > debug_auth_check.py << 'PYTHON'
import sys
sys.path.append('.')
from utils.auth import decode_token
from models.database import get_db, User
from sqlalchemy.orm import Session

# Test token
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjksImVtYWlsIjoiZmluYWwxNzU0MDQxMDU0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzU0MTI3NDU1LCJ0eXBlIjoiYWNjZXNzIn0.LNmtbxYjnr_0CnfExQ8TMcO3lPdm0PeKJSBi95D6Hn0"

try:
    # Decode token
    payload = decode_token(test_token)
    print(f"Token decoded: {payload}")
    
    # Check user in DB
    db = next(get_db())
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        print(f"User found: {user.email}")
        print(f"User active: {user.is_active if hasattr(user, 'is_active') else 'No is_active field'}")
    else:
        print(f"User with ID {user_id} not found in database")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON

python3 debug_auth_check.py

echo -e "\n2. Let's check the actual auth_cookie.py on server..."
echo "===================================================="
# Make sure we have the latest version
grep -n "def check_auth" api/auth_cookie.py -A 20

echo -e "\n3. Deploying the fixed auth_cookie.py again..."
echo "=============================================="
EOF

# Copy the file again to make sure
scp -i "$KEY_PATH" backend/api/auth_cookie.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo -e "\n4. Restarting backend properly..."
echo "================================="
pkill -f "uvicorn main:app" || true
sleep 3

source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &

echo "Waiting for backend to fully start..."
sleep 8

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running"
    
    # Test immediately
    echo -e "\n5. Testing auth flow immediately after restart..."
    echo "==============================================="
    
    # Create fresh user
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="restart${TIMESTAMP}@example.com"
    
    # Get CSRF
    CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
    
    # Register
    echo "a) Registering user: $TEST_EMAIL"
    curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c restart_cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Restart Test\"}" \
        | python3 -m json.tool | grep -E "email|id"
    
    # Check cookies - especially the paths
    echo -e "\nb) Checking cookie paths:"
    cat restart_cookies.txt | grep -E "refresh_token|access_token"
    
    # Test auth check
    echo -e "\nc) Testing auth check:"
    curl -s https://bankcsvconverter.com/v2/api/auth/check -b restart_cookies.txt | python3 -m json.tool
    
    # Clean up
    rm -f restart_cookies.txt
else
    echo "❌ Backend failed to start!"
    echo "Last 30 lines of log:"
    tail -30 server.log
fi

# Clean up debug script
rm -f debug_auth_check.py

EOF

echo -e "\n✅ Backend restarted with auth fixes!"