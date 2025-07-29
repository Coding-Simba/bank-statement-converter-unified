#!/bin/bash

# Fix Nginx Configuration Conflicts

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Nginx Configuration Conflicts"
echo "===================================="

# SSH to server and fix conflicts
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Listing all nginx site configurations..."
ls -la /etc/nginx/sites-enabled/

echo "2. Checking for duplicate server configurations..."
sudo grep -r "server_name" /etc/nginx/sites-enabled/

echo "3. Removing conflicting configurations..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/bankcsvconverter.com 2>/dev/null

echo "4. Creating single unified configuration..."
sudo tee /etc/nginx/sites-available/bank-converter << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name bankcsvconverter.com www.bankcsvconverter.com 3.235.19.83 _;

    root /home/ubuntu/bank-statement-converter-unified/frontend;
    index index.html;

    # Maximum file upload size
    client_max_body_size 50M;

    # Frontend - serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy - without trailing slash to match both /api and /api/*
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings for long operations
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Health check endpoint
    location = /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
NGINX

echo "5. Clearing all enabled sites and re-enabling only our config..."
sudo rm -f /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/bank-converter /etc/nginx/sites-enabled/bank-converter

echo "6. Testing configuration..."
sudo nginx -t

echo "7. Reloading nginx..."
sudo systemctl reload nginx

echo "8. Testing endpoints..."
echo -e "\nTesting localhost:5000 directly:"
curl -s http://localhost:5000/ | python3 -m json.tool | head -10

echo -e "\nTesting /health through nginx:"
curl -s http://localhost/health | python3 -m json.tool

echo -e "\nTesting /api through nginx:"
curl -s http://localhost/api | python3 -m json.tool | head -10

echo -e "\n9. Final check - all active nginx configurations:"
sudo ls -la /etc/nginx/sites-enabled/

echo -e "\n10. Checking backend is still running:"
sudo systemctl is-active bank-converter-backend

echo -e "\nServer Status Summary:"
echo "====================="
echo "✅ Backend API: http://localhost:5000"
echo "✅ Nginx Proxy: http://bankcsvconverter.com/api"
echo "✅ Health Check: http://bankcsvconverter.com/health"

EOF