#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Testing Authentication System - Final Check"
echo "=========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking SSL certificate status..."
echo "==================================="
sudo certbot certificates

echo -e "\n2. Checking current nginx configuration..."
echo "========================================"
sudo nginx -t
sudo systemctl status nginx --no-pager | head -10

echo -e "\n3. Testing direct backend access..."
echo "================================="
curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool || echo "Backend not responding"

echo -e "\n4. Testing through HTTP (should redirect)..."
echo "=========================================="
curl -I http://bankcsvconverter.com/v2/api/auth/csrf

echo -e "\n5. Testing through HTTPS..."
echo "=========================="
CSRF_RESPONSE=$(curl -sk https://bankcsvconverter.com/v2/api/auth/csrf)
if echo "$CSRF_RESPONSE" | grep -q "csrf_token"; then
    echo "✅ HTTPS API working!"
    echo "$CSRF_RESPONSE" | python3 -m json.tool
    
    # Full authentication test
    echo -e "\n6. Testing complete authentication flow..."
    echo "========================================"
    
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="finaltest${TIMESTAMP}@example.com"
    TEST_PASSWORD="FinalTest123!"
    
    # Extract CSRF token
    CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
    
    # Register
    echo "Registering $TEST_EMAIL..."
    REG_RESPONSE=$(curl -sk -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c /tmp/auth_final_test.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Final Test User\"}")
    
    if echo "$REG_RESPONSE" | grep -q "\"id\""; then
        echo "✅ Registration successful!"
        echo "$REG_RESPONSE" | python3 -m json.tool | grep -E "email|id|full_name"
        
        # Check authentication
        echo -e "\nChecking authentication status..."
        AUTH_CHECK=$(curl -sk https://bankcsvconverter.com/v2/api/auth/check -b /tmp/auth_final_test.txt)
        if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
            echo "✅ User is authenticated!"
            
            # Test profile access
            echo -e "\nTesting profile access..."
            PROFILE=$(curl -sk https://bankcsvconverter.com/v2/api/auth/profile -b /tmp/auth_final_test.txt)
            if echo "$PROFILE" | grep -q "$TEST_EMAIL"; then
                echo "✅ Profile access working!"
                
                # Test logout
                echo -e "\nTesting logout..."
                LOGOUT=$(curl -sk -X POST https://bankcsvconverter.com/v2/api/auth/logout \
                    -b /tmp/auth_final_test.txt \
                    -H "X-CSRF-Token: $CSRF_TOKEN")
                echo "Logout response: $LOGOUT"
                
                # Verify logged out
                AUTH_CHECK_AFTER=$(curl -sk https://bankcsvconverter.com/v2/api/auth/check -b /tmp/auth_final_test.txt)
                if echo "$AUTH_CHECK_AFTER" | grep -q '"authenticated":false'; then
                    echo "✅ Logout successful!"
                fi
            fi
        else
            echo "❌ Authentication check failed"
            echo "$AUTH_CHECK"
        fi
    else
        echo "❌ Registration failed"
        echo "$REG_RESPONSE"
    fi
    
    rm -f /tmp/auth_final_test.txt
else
    echo "❌ HTTPS API not working"
    echo "Response: $CSRF_RESPONSE"
    
    # Check for SSL issues
    echo -e "\nChecking SSL certificate..."
    openssl s_client -connect bankcsvconverter.com:443 -servername bankcsvconverter.com < /dev/null 2>&1 | grep -E "subject|issuer|Verify return code"
fi

echo -e "\n7. Testing from browser perspective..."
echo "===================================="
# Test the actual pages
echo "Testing signup page:"
curl -sk https://bankcsvconverter.com/signup.html | grep -E "<title>|auth-unified.js" | head -5

echo -e "\nTesting login page:"
curl -sk https://bankcsvconverter.com/login.html | grep -E "<title>|auth-unified.js" | head -5

echo -e "\n================================"
echo "AUTHENTICATION SYSTEM SUMMARY"
echo "================================"
echo "Backend Status: $(pgrep -f 'uvicorn main:app' > /dev/null && echo '✅ Running' || echo '❌ Not running')"
echo "Nginx Status: $(systemctl is-active nginx | grep -q active && echo '✅ Active' || echo '❌ Inactive')"
echo "SSL Status: $(curl -sk https://bankcsvconverter.com 2>&1 | grep -q '200 OK' && echo '✅ Working' || echo '⚠️  Check needed')"
echo ""
echo "If everything is working, users can:"
echo "• Sign up: https://bankcsvconverter.com/signup.html"
echo "• Log in: https://bankcsvconverter.com/login.html"

EOF

echo -e "\n✅ Authentication system test complete!"