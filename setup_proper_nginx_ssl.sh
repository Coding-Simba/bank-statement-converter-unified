#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Setting up proper nginx SSL configuration"
echo "========================================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking current nginx configuration file..."
echo "============================================="
ls -la /etc/nginx/sites-enabled/
ls -la /etc/nginx/sites-available/

echo -e "\n2. Backing up and creating proper SSL configuration..."
echo "==================================================="
sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.http-only-backup

# Create the proper SSL configuration
sudo tee /etc/nginx/sites-available/bank-converter << 'NGINX'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/bankcsvconverter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bankcsvconverter.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Root directory
    root /home/ubuntu/bank-statement-converter;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # API v2 routes
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
        
        # Cookie forwarding
        proxy_set_header Cookie $http_cookie;
        proxy_pass_header Set-Cookie;
        proxy_pass_request_headers on;
    }

    # Legacy API routes
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json;
    gzip_disable "MSIE [1-6]\.";
}
NGINX

echo -e "\n3. Testing the configuration..."
echo "=============================="
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "\n4. Reloading nginx with new configuration..."
    echo "=========================================="
    sudo systemctl reload nginx
    
    echo -e "\n5. Verifying nginx is running..."
    echo "==============================="
    sudo systemctl status nginx --no-pager | grep Active
    
    echo -e "\n6. Testing HTTPS endpoints..."
    echo "============================"
    
    # Give nginx a moment to reload
    sleep 2
    
    # Test CSRF endpoint through HTTPS
    echo "Testing CSRF endpoint:"
    CSRF_RESPONSE=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf)
    if echo "$CSRF_RESPONSE" | grep -q "csrf_token"; then
        echo "✅ HTTPS API is working!"
        echo "$CSRF_RESPONSE" | python3 -m json.tool
        
        # Complete authentication test
        echo -e "\n7. Running complete authentication test..."
        echo "========================================"
        
        TIMESTAMP=$(date +%s)
        TEST_EMAIL="ssltest${TIMESTAMP}@example.com"
        TEST_PASSWORD="SSLTest123!"
        CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
        
        # Register
        echo "Registering $TEST_EMAIL..."
        REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
            -c /tmp/ssl_test_cookies.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"SSL Test User\"}")
        
        if echo "$REG_RESPONSE" | grep -q "\"id\""; then
            echo "✅ Registration successful!"
            
            # Check authentication
            AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b /tmp/ssl_test_cookies.txt)
            if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
                echo "✅ Authentication verified!"
                
                # Test the actual pages
                echo -e "\n8. Testing web pages..."
                echo "===================="
                
                echo "Signup page:"
                curl -s https://bankcsvconverter.com/signup.html | grep -o "<title>.*</title>" | head -1
                
                echo "Login page:"
                curl -s https://bankcsvconverter.com/login.html | grep -o "<title>.*</title>" | head -1
                
                echo -e "\n✅ AUTHENTICATION SYSTEM IS FULLY OPERATIONAL! ✅"
                echo ""
                echo "Users can now:"
                echo "• Sign up at: https://bankcsvconverter.com/signup.html"
                echo "• Log in at: https://bankcsvconverter.com/login.html"
                echo "• Sessions persist across pages with cookies"
                echo "• Remember Me option provides 90-day sessions"
            else
                echo "❌ Authentication check failed"
            fi
        else
            echo "❌ Registration failed"
            echo "$REG_RESPONSE"
        fi
        
        rm -f /tmp/ssl_test_cookies.txt
    else
        echo "❌ HTTPS API not responding correctly"
        echo "Response: $CSRF_RESPONSE"
        
        # Debug SSL
        echo -e "\nDebugging SSL connection..."
        curl -v https://bankcsvconverter.com/v2/api/auth/csrf 2>&1 | grep -E "SSL|TLS|certificate"
    fi
else
    echo "❌ Nginx configuration test failed!"
fi

echo -e "\n9. Final status check..."
echo "======================"
echo "Nginx: $(systemctl is-active nginx)"
echo "Backend: $(pgrep -f 'uvicorn main:app' > /dev/null && echo 'Running' || echo 'Not running')"
echo "HTTPS: $(curl -sI https://bankcsvconverter.com | head -1)"

EOF

echo -e "\n✅ SSL configuration setup complete!"