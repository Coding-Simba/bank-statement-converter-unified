#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Final auth debugging"
echo "==================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking what cookies are actually being set..."
echo "================================================"

# Test complete flow with verbose output
TIMESTAMP=$(date +%s)
TEST_EMAIL="final${TIMESTAMP}@example.com"

# Get CSRF with verbose
echo "a) Getting CSRF (verbose)..."
curl -v -c final_cookies.txt https://bankcsvconverter.com/v2/api/auth/csrf 2>&1 | grep -E "Set-Cookie|csrf_token" | tail -10

# Login instead of register (to test with known user)
echo -e "\nb) Testing login with known user..."
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

# First create the user
curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Test\"}" > /dev/null

# Now login with verbose to see cookies
echo -e "\nc) Login with verbose cookie output..."
curl -v -X POST https://bankcsvconverter.com/v2/api/auth/login \
    -c login_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"remember_me\":false}" 2>&1 | grep -E "Set-Cookie|{" | tail -20

echo -e "\nd) Checking cookies file..."
echo "Cookies saved:"
cat login_cookies.txt

echo -e "\ne) Testing auth check with exact cookie..."
ACCESS_TOKEN=$(grep "access_token" login_cookies.txt | awk '{print $7}')
if [ -n "$ACCESS_TOKEN" ]; then
    echo "Using token: ${ACCESS_TOKEN:0:50}..."
    
    # Test with curl and explicit cookie
    echo -e "\nWith curl:"
    curl -s https://bankcsvconverter.com/v2/api/auth/check \
        -H "Cookie: access_token=$ACCESS_TOKEN" | python3 -m json.tool
    
    # Test direct to backend
    echo -e "\nDirect to backend:"
    curl -s http://localhost:5000/v2/api/auth/check \
        -H "Cookie: access_token=$ACCESS_TOKEN" | python3 -m json.tool
fi

echo -e "\n2. Checking if it's a path issue..."
echo "==================================="

# Check the actual cookie path in auth_cookie.py
echo "Current cookie paths in auth_cookie.py:"
grep -E "path=|PATH" api/auth_cookie.py | grep -v "import"

echo -e "\n3. Let me trace the request through the system..."
echo "==============================================="

# Enable debug logging temporarily
python3 << 'PYTHON'
import requests
import json

# Get CSRF
resp = requests.get("https://bankcsvconverter.com/v2/api/auth/csrf")
csrf_token = resp.json()["csrf_token"]
print(f"CSRF token: {csrf_token[:20]}...")

# Login
login_data = {
    "email": "trace@example.com",
    "password": "Test123!",
    "remember_me": False
}

# Register first
requests.post(
    "https://bankcsvconverter.com/v2/api/auth/register",
    json={**login_data, "full_name": "Trace Test"},
    headers={"X-CSRF-Token": csrf_token}
)

# Now login
session = requests.Session()
login_resp = session.post(
    "https://bankcsvconverter.com/v2/api/auth/login",
    json=login_data,
    headers={"X-CSRF-Token": csrf_token}
)

print(f"\nLogin status: {login_resp.status_code}")
print(f"Cookies after login: {dict(session.cookies)}")

# Check auth
check_resp = session.get("https://bankcsvconverter.com/v2/api/auth/check")
print(f"\nAuth check response: {check_resp.json()}")

# Check what cookies requests is sending
print(f"\nCookies being sent: {session.cookies}")
for cookie in session.cookies:
    print(f"  {cookie.name}: domain={cookie.domain}, path={cookie.path}, secure={cookie.secure}")
PYTHON

# Clean up
rm -f final_cookies.txt login_cookies.txt

echo -e "\n4. Checking production flag..."
echo "=============================="

grep -n "production" api/auth_cookie.py | head -10

EOF