#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx redirect loop"
echo "========================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Backing up current nginx config..."
echo "===================================="
sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.redirect-loop-backup

echo -e "\n2. Creating fixed nginx configuration..."
echo "======================================"
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

    # Frontend static files (HTML)
    location ~* \.(html)$ {
        try_files $uri /frontend$uri =404;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # JavaScript files
    location /js/ {
        alias /home/ubuntu/bank-statement-converter/js/;
        try_files $uri /frontend/js$uri =404;
        add_header Content-Type application/javascript;
        add_header Cache-Control "public, max-age=31536000";
    }

    # CSS files
    location /css/ {
        alias /home/ubuntu/bank-statement-converter/css/;
        try_files $uri /frontend/css$uri =404;
        add_header Cache-Control "public, max-age=31536000";
    }

    # Images and other static assets
    location ~* \.(png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        try_files $uri /frontend$uri =404;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Root location - serve index.html for SPA routing
    location / {
        try_files $uri /frontend$uri /index.html /frontend/index.html =404;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
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

echo -e "\n3. Testing nginx configuration..."
echo "================================"
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "\n4. Reloading nginx..."
    echo "==================="
    sudo systemctl reload nginx
    
    echo -e "\n5. Creating proper directory structure..."
    echo "======================================="
    cd /home/ubuntu/bank-statement-converter/
    
    # Ensure frontend JS is accessible
    if [ -d frontend/js ] && [ ! -L js ]; then
        if [ -d js ]; then
            echo "Moving existing js directory..."
            sudo mv js js.old
        fi
        echo "Creating js symlink to frontend/js..."
        sudo ln -sf frontend/js js
    fi
    
    # Ensure frontend CSS is accessible
    if [ -d frontend/css ] && [ ! -L css ]; then
        echo "Creating css symlink to frontend/css..."
        sudo ln -sf frontend/css css
    fi
    
    echo -e "\n6. Testing pages locally..."
    echo "=========================="
    for page in index.html pricing.html login.html signup.html; do
        echo -n "$page: "
        STATUS=$(curl -sI http://localhost/$page | head -1 | awk '{print $2}')
        if [ "$STATUS" = "200" ]; then
            echo "✅ HTTP $STATUS"
        else
            echo "❌ HTTP $STATUS"
        fi
    done
    
    echo -e "\n7. Testing through HTTPS..."
    echo "=========================="
    # Test main page
    echo -n "Main page: "
    curl -sI https://bankcsvconverter.com/ | head -1
    
    # Test auth pages
    echo -n "Login page: "
    curl -sI https://bankcsvconverter.com/login.html | head -1
    
    echo -n "Signup page: "
    curl -sI https://bankcsvconverter.com/signup.html | head -1
    
    # Test API
    echo -n "API CSRF: "
    curl -s https://bankcsvconverter.com/v2/api/auth/csrf | grep -o "csrf_token" && echo " ✅" || echo " ❌"
else
    echo "❌ Nginx configuration test failed!"
fi

echo -e "\n8. Final file structure check..."
echo "==============================="
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "html|js|css|frontend"

EOF

echo -e "\n✅ Nginx fix complete!"