#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx port configuration"
echo "=============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking current nginx configuration..."
echo "========================================"
sudo grep -n "proxy_pass" /etc/nginx/sites-available/bank-converter | grep -E "8000|5000"

echo -e "\n2. Fixing ALL proxy_pass directives to use port 5000..."
echo "===================================================="
sudo sed -i 's/http:\/\/localhost:8000/http:\/\/localhost:5000/g' /etc/nginx/sites-available/bank-converter
sudo sed -i 's/http:\/\/127.0.0.1:8000/http:\/\/localhost:5000/g' /etc/nginx/sites-available/bank-converter

echo -e "\n3. Verifying the changes..."
echo "=========================="
sudo grep -n "proxy_pass" /etc/nginx/sites-available/bank-converter

echo -e "\n4. Testing nginx configuration..."
echo "================================"
sudo nginx -t

echo -e "\n5. Reloading nginx..."
echo "===================="
sudo systemctl reload nginx

echo -e "\n6. Testing authentication endpoints..."
echo "===================================="

# Wait a moment for nginx to reload
sleep 2

# Test CSRF endpoint
echo "a) Testing CSRF endpoint:"
CSRF_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" https://bankcsvconverter.com/v2/api/auth/csrf)
HTTP_CODE=$(echo "$CSRF_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY=$(echo "$CSRF_RESPONSE" | sed 's/HTTP_CODE:[0-9]*//')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ CSRF endpoint working!"
    echo "$BODY" | python3 -m json.tool
else
    echo "❌ CSRF endpoint failed (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

# Quick registration test
echo -e "\nb) Testing registration endpoint:"
TIMESTAMP=$(date +%s)
TEST_EMAIL="nginxfix${TIMESTAMP}@example.com"
CSRF_TOKEN=$(echo "$BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('csrf_token',''))" 2>/dev/null)

if [ -n "$CSRF_TOKEN" ]; then
    REGISTER_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Nginx Test\"}" \
        -w "\nHTTP_CODE:%{http_code}")
    
    HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Registration endpoint working!"
    else
        echo "❌ Registration failed (HTTP $HTTP_CODE)"
    fi
fi

echo -e "\n7. Complete flow test..."
echo "======================="

# New test user
TIMESTAMP=$(date +%s)
TEST_EMAIL="flowtest${TIMESTAMP}@example.com"

# Get CSRF
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

# Register
echo "Registering $TEST_EMAIL..."
curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -c nginx_test_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Flow Test\"}" \
    | python3 -m json.tool | grep -E "email|id" || echo "Registration failed"

# Check auth
echo -e "\nChecking authentication..."
AUTH_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b nginx_test_cookies.txt)
if echo "$AUTH_RESPONSE" | grep -q '"authenticated":true'; then
    echo "✅ Authentication is working!"
    echo "$AUTH_RESPONSE" | python3 -m json.tool | head -10
else
    echo "❌ Authentication check failed"
    echo "$AUTH_RESPONSE"
fi

# Cleanup
rm -f nginx_test_cookies.txt

EOF

echo -e "\n✅ Nginx port configuration fixed!"