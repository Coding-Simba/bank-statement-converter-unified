#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing file locations and authentication system"
echo "=============================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Finding the actual location of HTML files..."
echo "============================================="
find /home/ubuntu -name "signup.html" -type f 2>/dev/null | head -5
find /home/ubuntu -name "login.html" -type f 2>/dev/null | head -5
find /home/ubuntu -name "index.html" -type f 2>/dev/null | head -5

echo -e "\n2. Checking current nginx root directory..."
echo "========================================="
grep -n "root" /etc/nginx/sites-available/bank-converter

echo -e "\n3. Listing contents of the root directory..."
echo "=========================================="
ls -la /home/ubuntu/bank-statement-converter/ | head -20

echo -e "\n4. Copying unified auth files to the server..."
echo "============================================"
# First, let's ensure the files exist in the right place
if [ ! -f /home/ubuntu/bank-statement-converter/signup.html ]; then
    echo "signup.html is missing, checking for it elsewhere..."
    SIGNUP_PATH=$(find /home/ubuntu -name "signup.html" -type f 2>/dev/null | head -1)
    if [ -n "$SIGNUP_PATH" ]; then
        echo "Found at: $SIGNUP_PATH"
        sudo cp "$SIGNUP_PATH" /home/ubuntu/bank-statement-converter/
    fi
fi

if [ ! -f /home/ubuntu/bank-statement-converter/login.html ]; then
    echo "login.html is missing, checking for it elsewhere..."
    LOGIN_PATH=$(find /home/ubuntu -name "login.html" -type f 2>/dev/null | head -1)
    if [ -n "$LOGIN_PATH" ]; then
        echo "Found at: $LOGIN_PATH"
        sudo cp "$LOGIN_PATH" /home/ubuntu/bank-statement-converter/
    fi
fi

echo -e "\n5. Ensuring js directory exists..."
echo "================================"
mkdir -p /home/ubuntu/bank-statement-converter/js

echo -e "\n6. Checking for auth-unified.js..."
echo "================================="
if [ ! -f /home/ubuntu/bank-statement-converter/js/auth-unified.js ]; then
    echo "auth-unified.js is missing!"
    AUTH_JS_PATH=$(find /home/ubuntu -name "auth-unified.js" -type f 2>/dev/null | head -1)
    if [ -n "$AUTH_JS_PATH" ]; then
        echo "Found at: $AUTH_JS_PATH"
        sudo cp "$AUTH_JS_PATH" /home/ubuntu/bank-statement-converter/js/
    fi
fi

echo -e "\n7. Final file check..."
echo "===================="
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "signup|login|index"
ls -la /home/ubuntu/bank-statement-converter/js/ | grep auth

echo -e "\n8. Testing authentication system again..."
echo "======================================="

# Test direct access
echo "Direct backend test:"
curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool

# Test through nginx using IP
echo -e "\nTesting through nginx (IP):"
curl -s http://3.235.19.83/v2/api/auth/csrf | head -20

# Check if it's a Cloudflare issue
echo -e "\n9. Cloudflare status check..."
echo "============================"
# Try with different user agent
curl -sI https://bankcsvconverter.com/v2/api/auth/csrf \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    | head -10

echo -e "\n10. Checking Cloudflare SSL/TLS settings..."
echo "========================================="
echo "IMPORTANT: You may need to check Cloudflare dashboard:"
echo "1. SSL/TLS -> Overview -> Set to 'Full' or 'Full (strict)'"
echo "2. SSL/TLS -> Edge Certificates -> Always Use HTTPS: ON"
echo "3. Speed -> Optimization -> Auto Minify: OFF for JavaScript"
echo "4. Rules -> Page Rules -> Check for any conflicting rules"

EOF

echo -e "\n✅ File location check complete!"