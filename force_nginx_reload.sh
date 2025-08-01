#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Forcing nginx to reload with correct config"
echo "=========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Finding ALL nginx config files with port 8000..."
echo "================================================="
sudo grep -r "8000" /etc/nginx/ 2>/dev/null | grep -v "Binary"

echo -e "\n2. Fixing ALL occurrences of port 8000..."
echo "========================================"
sudo find /etc/nginx -type f -name "*.conf" -o -name "bank-converter" | while read file; do
    if sudo grep -q "8000" "$file" 2>/dev/null; then
        echo "Fixing: $file"
        sudo sed -i.bak 's/:8000/:5000/g' "$file"
    fi
done

echo -e "\n3. Verifying no more port 8000 references..."
echo "==========================================="
sudo grep -r "8000" /etc/nginx/ 2>/dev/null | grep -v -E "Binary|\.bak" || echo "✅ No more port 8000 references found"

echo -e "\n4. Checking the specific bank-converter config..."
echo "==============================================="
sudo grep -n "proxy_pass" /etc/nginx/sites-available/bank-converter

echo -e "\n5. Testing nginx config..."
echo "========================"
sudo nginx -t

echo -e "\n6. Force restarting nginx (not just reload)..."
echo "============================================"
sudo systemctl stop nginx
sleep 2
sudo systemctl start nginx
sleep 2

echo -e "\n7. Checking nginx is running..."
echo "============================="
sudo systemctl status nginx | grep Active

echo -e "\n8. Testing the endpoints NOW..."
echo "============================="

# Test CSRF endpoint
echo "Testing CSRF endpoint:"
RESPONSE=$(curl -s -w "\nSTATUS:%{http_code}" https://bankcsvconverter.com/v2/api/auth/csrf)
STATUS=$(echo "$RESPONSE" | grep "STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "STATUS:")

if [ "$STATUS" = "200" ]; then
    echo "✅ CSRF endpoint working! (HTTP $STATUS)"
    echo "$BODY" | python3 -m json.tool
else
    echo "❌ CSRF endpoint failed (HTTP $STATUS)"
    echo "$BODY"
fi

# Quick auth flow test
echo -e "\nQuick auth flow test:"
TIMESTAMP=$(date +%s)
TEST_EMAIL="nginx${TIMESTAMP}@example.com"

if [ "$STATUS" = "200" ]; then
    CSRF_TOKEN=$(echo "$BODY" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
    
    # Register
    REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c nginx_cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Nginx Test\"}" \
        -w "\nSTATUS:%{http_code}")
    
    REG_STATUS=$(echo "$REG_RESPONSE" | grep "STATUS:" | cut -d: -f2)
    
    if [ "$REG_STATUS" = "200" ]; then
        echo "✅ Registration working!"
        
        # Auth check
        AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b nginx_cookies.txt)
        if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
            echo "✅ AUTHENTICATION IS WORKING!"
        else
            echo "❌ Auth check failed"
        fi
    else
        echo "❌ Registration failed (HTTP $REG_STATUS)"
    fi
    
    rm -f nginx_cookies.txt
fi

echo -e "\n9. Final nginx error check..."
echo "============================"
sudo tail -5 /var/log/nginx/error.log | grep -E "connect|upstream" || echo "No recent connection errors"

EOF

echo -e "\n✅ Nginx configuration forced update complete!"