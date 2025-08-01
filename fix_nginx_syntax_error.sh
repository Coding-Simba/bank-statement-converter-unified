#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx syntax error"
echo "========================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking the nginx configuration around line 89..."
echo "==================================================="
sudo sed -n '85,95p' /etc/nginx/sites-enabled/bank-converter

echo -e "\n2. Looking for the full nginx configuration structure..."
echo "====================================================="
sudo cat /etc/nginx/sites-enabled/bank-converter | grep -n -E "server|location|^[[:space:]]*\}[[:space:]]*$" | tail -20

echo -e "\n3. Creating a corrected nginx configuration..."
echo "============================================"
sudo tee /etc/nginx/sites-available/bank-converter-fixed << 'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/bankcsvconverter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bankcsvconverter.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Root directory
    root /home/ubuntu/bank-statement-converter;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
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

    # Legacy API routes (if any)
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

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json;
    gzip_disable "MSIE [1-6]\.";
}
NGINX

echo -e "\n4. Testing the new configuration..."
echo "=================================="
sudo nginx -t -c /etc/nginx/nginx.conf -g "include /etc/nginx/sites-available/bank-converter-fixed;"

echo -e "\n5. Backing up current config and applying the fix..."
echo "================================================="
sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.broken
sudo cp /etc/nginx/sites-available/bank-converter-fixed /etc/nginx/sites-available/bank-converter

echo -e "\n6. Removing old symlink and creating new one..."
echo "============================================="
sudo rm -f /etc/nginx/sites-enabled/bank-converter
sudo ln -s /etc/nginx/sites-available/bank-converter /etc/nginx/sites-enabled/

echo -e "\n7. Final nginx test..."
echo "===================="
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "\n8. Restarting nginx..."
    echo "===================="
    sudo systemctl restart nginx
    
    echo -e "\n9. Verifying nginx is running..."
    echo "==============================="
    sudo systemctl status nginx | grep Active
    
    echo -e "\n10. Testing authentication system..."
    echo "==================================="
    
    # Quick test
    CSRF_RESPONSE=$(curl -s -m 10 https://bankcsvconverter.com/v2/api/auth/csrf)
    if echo "$CSRF_RESPONSE" | grep -q "csrf_token"; then
        echo "✅ Authentication API is accessible!"
        echo "$CSRF_RESPONSE" | python3 -m json.tool
        
        # Full test
        TIMESTAMP=$(date +%s)
        TEST_EMAIL="nginxfix${TIMESTAMP}@example.com"
        CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])")
        
        echo -e "\nTesting full registration flow..."
        curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
            -c /tmp/nginx_auth_test.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Nginx Fix Test\"}" \
            | python3 -m json.tool | grep -E "email|id"
        
        # Check authentication
        AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b /tmp/nginx_auth_test.txt)
        if echo "$AUTH_CHECK" | grep -q '"authenticated":true'; then
            echo -e "\n✅ AUTHENTICATION SYSTEM IS WORKING! ✅"
            echo "Users can now sign up and log in successfully!"
        fi
        
        rm -f /tmp/nginx_auth_test.txt
    else
        echo "❌ Authentication API not responding"
        echo "Response: $CSRF_RESPONSE"
        
        # Check if backend is running
        echo -e "\nChecking backend status..."
        ps aux | grep uvicorn | grep -v grep || echo "Backend not running!"
    fi
else
    echo "❌ Nginx configuration still has errors!"
fi

EOF

echo -e "\n✅ Script execution complete!"