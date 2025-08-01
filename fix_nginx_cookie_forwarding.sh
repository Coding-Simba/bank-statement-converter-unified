#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx cookie forwarding"
echo "============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Backing up current nginx config..."
sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.backup.$(date +%Y%m%d_%H%M%S)

echo -e "\n2. Checking current v2 location block..."
sudo grep -A15 "location /v2/" /etc/nginx/sites-available/bank-converter

echo -e "\n3. Updating nginx configuration..."
# We need to ensure cookies are properly forwarded
sudo tee /tmp/nginx_v2_fix.conf << 'NGINX'
    # V2 API routes for cookie auth
    location /v2/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Important for cookies - must pass all headers
        proxy_set_header Cookie $http_cookie;
        proxy_pass_header Set-Cookie;
        proxy_pass_request_headers on;
        
        # Ensure proper cookie domain handling
        proxy_cookie_domain localhost $host;
        proxy_cookie_path / /;
    }
NGINX

# Replace the v2 location block
echo -e "\n4. Applying the fix..."
# First, remove the old v2 location block if it exists
sudo sed -i '/location \/v2\//,/^[[:space:]]*}$/d' /etc/nginx/sites-available/bank-converter

# Add the new v2 location block before the last closing brace
sudo sed -i '/^}$/i\
\
    # V2 API routes for cookie auth\
    location /v2/ {\
        proxy_pass http://localhost:5000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection '"'"'upgrade'"'"';\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_cache_bypass $http_upgrade;\
        \
        # Important for cookies - must pass all headers\
        proxy_set_header Cookie $http_cookie;\
        proxy_pass_header Set-Cookie;\
        proxy_pass_request_headers on;\
        \
        # Ensure proper cookie domain handling\
        proxy_cookie_domain localhost $host;\
        proxy_cookie_path / /;\
    }' /etc/nginx/sites-available/bank-converter

echo -e "\n5. Testing nginx configuration..."
sudo nginx -t

echo -e "\n6. Reloading nginx..."
sudo systemctl reload nginx

echo -e "\n7. Testing authentication flow again..."
echo "======================================="

# Quick test
TIMESTAMP=$(date +%s)
TEST_EMAIL="nginxtest${TIMESTAMP}@example.com"

# Get CSRF
echo "a) Getting CSRF token..."
CSRF_TOKEN=$(curl -s -c test_cookies.txt https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
echo "CSRF: ${CSRF_TOKEN:0:20}..."

# Register
echo -e "\nb) Registering test user..."
curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -b test_cookies.txt -c test_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Test\"}" \
    | python3 -m json.tool | head -10

# Check auth
echo -e "\nc) Testing auth check..."
AUTH_RESP=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b test_cookies.txt)
echo "Auth check response: $AUTH_RESP"

if echo "$AUTH_RESP" | grep -q '"authenticated":true'; then
    echo "✅ Authentication is working!"
else
    echo "❌ Authentication still not working"
    
    # Debug with direct backend call
    echo -e "\nd) Testing direct backend call..."
    ACCESS_TOKEN=$(grep "access_token" test_cookies.txt | awk '{print $7}')
    curl -s http://localhost:5000/v2/api/auth/check -H "Cookie: access_token=$ACCESS_TOKEN" | python3 -m json.tool
fi

rm -f test_cookies.txt

EOF

echo -e "\n✅ Nginx configuration updated!"