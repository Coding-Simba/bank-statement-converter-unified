#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx duplicate server configuration"
echo "=========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking for duplicate nginx configurations..."
echo "==============================================="
sudo ls -la /etc/nginx/sites-enabled/

echo -e "\n2. Removing backup files that cause conflicts..."
echo "=============================================="
# Remove any .bak files in sites-enabled
sudo rm -f /etc/nginx/sites-enabled/*.bak
sudo rm -f /etc/nginx/sites-available/*.bak

echo -e "\n3. Checking for multiple enabled site configs..."
echo "==============================================="
# List all enabled sites
ls -1 /etc/nginx/sites-enabled/

echo -e "\n4. Ensuring only bank-converter is enabled..."
echo "==========================================="
# Remove default if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Ensure bank-converter is the only enabled site
if [ ! -L /etc/nginx/sites-enabled/bank-converter ]; then
    sudo ln -sf /etc/nginx/sites-available/bank-converter /etc/nginx/sites-enabled/
fi

echo -e "\n5. Fixing port configuration one more time..."
echo "==========================================="
# Ensure all proxy_pass directives use port 5000
sudo sed -i 's/:8000/:5000/g' /etc/nginx/sites-available/bank-converter

echo -e "\n6. Verifying configuration..."
echo "============================"
sudo grep -n "proxy_pass" /etc/nginx/sites-available/bank-converter

echo -e "\n7. Testing nginx configuration..."
echo "================================"
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "\n8. Restarting nginx..."
    echo "===================="
    sudo systemctl restart nginx
    
    echo -e "\n9. Verifying nginx is running..."
    echo "==============================="
    sudo systemctl status nginx | grep Active
    
    echo -e "\n10. Starting backend if not running..."
    echo "===================================="
    cd /home/ubuntu/bank-statement-converter/backend
    
    # Check if backend is running
    if ! pgrep -f "uvicorn main:app" > /dev/null; then
        echo "Backend not running, starting it..."
        source venv/bin/activate
        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
        sleep 5
    fi
    
    echo -e "\n11. Testing authentication endpoints..."
    echo "====================================="
    
    # Test CSRF endpoint
    echo "Testing CSRF endpoint:"
    CSRF_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf)
    if echo "$CSRF_RESPONSE" | grep -q "csrf_token"; then
        echo "✅ CSRF endpoint working!"
        CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
        
        # Test registration
        TIMESTAMP=$(date +%s)
        TEST_EMAIL="authtest${TIMESTAMP}@example.com"
        
        echo -e "\nTesting registration for $TEST_EMAIL..."
        REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
            -c auth_test_cookies.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Auth Test\"}")
        
        if echo "$REG_RESPONSE" | grep -q "\"id\""; then
            echo "✅ Registration working!"
            
            # Test auth check
            AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b auth_test_cookies.txt)
            if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
                echo "✅ Authentication working!"
                echo ""
                echo "🎉 AUTHENTICATION SYSTEM IS FULLY OPERATIONAL! 🎉"
                echo ""
                echo "Users can now:"
                echo "✅ Sign up at https://bankcsvconverter.com/signup.html"
                echo "✅ Log in at https://bankcsvconverter.com/login.html"
                echo "✅ Stay logged in across pages"
                echo "✅ Use Remember Me for extended sessions"
            else
                echo "❌ Auth check failed"
            fi
        else
            echo "❌ Registration failed"
            echo "$REG_RESPONSE"
        fi
        
        rm -f auth_test_cookies.txt
    else
        echo "❌ CSRF endpoint not working"
        echo "$CSRF_RESPONSE"
    fi
else
    echo "❌ Nginx configuration test failed!"
    echo "Please check the error messages above"
fi

EOF

echo -e "\n✅ Nginx configuration fix complete!"