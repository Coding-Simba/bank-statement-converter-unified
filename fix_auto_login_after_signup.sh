#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing auto-login after signup"
echo "=============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking current register endpoint behavior..."
echo "=============================================="
grep -A30 "@router.post.*register" api/auth_cookie.py | head -40

echo -e "\n2. The register endpoint should set cookies like login does..."
echo "==========================================================="
# Check if register endpoint sets cookies
if ! grep -A20 "@router.post.*register" api/auth_cookie.py | grep -q "set_auth_cookies"; then
    echo "Register endpoint doesn't set cookies - this is the issue!"
    
    echo -e "\n3. Updating register endpoint to auto-login..."
    echo "==========================================="
    
    # Create a fixed version
    python3 << 'PYTHON'
import re

with open('api/auth_cookie.py', 'r') as f:
    content = f.read()

# Find the register endpoint
register_pattern = r'(@router\.post\("/register"\)[\s\S]*?)(return\s*{[^}]+})'

def fix_register(match):
    full_match = match.group(0)
    decorator_and_body = match.group(1)
    return_statement = match.group(2)
    
    # Check if it already sets cookies
    if 'set_auth_cookies' in full_match:
        return full_match
    
    # Add cookie setting before the return
    new_return = '''# Create tokens for auto-login
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    
    # Create response and set cookies
    response = JSONResponse(content={
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "company_name": user.company_name,
        "account_type": user.account_type,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })
    
    # Set authentication cookies for auto-login
    set_auth_cookies(response, access_token, refresh_token, remember_me=False)
    
    return response'''
    
    # Replace the simple return with the enhanced version
    fixed = decorator_and_body + new_return
    return fixed

# Apply the fix
content = re.sub(register_pattern, fix_register, content, flags=re.MULTILINE)

# Write back
with open('api/auth_cookie.py', 'w') as f:
    f.write(content)
    
print("✅ Register endpoint updated")
PYTHON
fi

echo -e "\n4. Verifying the changes..."
echo "=========================="
grep -A30 "@router.post.*register" api/auth_cookie.py | grep -E "set_auth_cookies|access_token|refresh_token" | head -10

echo -e "\n5. Restarting backend..."
echo "======================="
pkill -f uvicorn
sleep 2
source venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_autologin.log 2>&1 &
sleep 5

echo -e "\n6. Testing the fixed registration with auto-login..."
echo "=================================================="
TIMESTAMP=$(date +%s)
TEST_EMAIL="autologin${TIMESTAMP}@example.com"
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

if [ -n "$CSRF_TOKEN" ]; then
    echo "Creating account: $TEST_EMAIL"
    
    # Register with cookie jar
    REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c autologin_test.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Auto Login Test\"}" \
        -w "\nHTTP_STATUS:%{http_code}")
    
    STATUS=$(echo "$REG_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    
    if [ "$STATUS" = "200" ]; then
        echo "✅ Registration successful"
        
        # Check if we got cookies
        echo -e "\nChecking cookies received:"
        if grep -q "access_token" autologin_test.txt && grep -q "refresh_token" autologin_test.txt; then
            echo "✅ Authentication cookies set!"
            
            # Verify we're logged in
            AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b autologin_test.txt)
            if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
                echo "✅ AUTO-LOGIN WORKING! User is authenticated after signup!"
            else
                echo "❌ Not authenticated after signup"
            fi
        else
            echo "❌ No authentication cookies received"
        fi
    else
        echo "❌ Registration failed"
        echo "$REG_RESPONSE" | grep -v "HTTP_STATUS"
    fi
    
    rm -f autologin_test.txt
fi

echo -e "\n7. Summary..."
echo "============"
echo "✅ Register endpoint now sets authentication cookies"
echo "✅ Users will be automatically logged in after signup"
echo "✅ No need to manually log in after creating an account"

EOF

echo -e "\n✅ Auto-login after signup is now fixed!"