#!/bin/bash

# Fix Nginx to Use Original Backend

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Nginx to Use Original Backend"
echo "===================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Updating nginx to proxy to original backend on port 8000..."
sudo tee /etc/nginx/sites-available/bank-converter << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name bankcsvconverter.com www.bankcsvconverter.com 3.235.19.83 _;

    root /home/ubuntu/bank-statement-converter/frontend;
    index index.html;

    # Maximum file upload size
    client_max_body_size 50M;

    # Frontend - serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to original backend on port 8000
    location /api {
        proxy_pass http://127.0.0.1:8000;
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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
NGINX

echo "2. Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo "3. Stopping the new backend service..."
sudo systemctl stop bank-converter-backend
sudo systemctl disable bank-converter-backend

echo "4. Enabling original backend service..."
sudo systemctl enable bankconverter
sudo systemctl restart bankconverter

echo "5. Testing API endpoints..."
sleep 3

echo -e "\nTesting /api/upload:"
curl -X POST http://localhost/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=test" 2>/dev/null | python3 -m json.tool | head -10 || echo "Upload test"

echo -e "\nTesting /api/convert (the main endpoint):"
curl -s http://localhost/api/convert || echo ""

echo -e "\n6. Checking service status:"
echo "Original backend (bankconverter):" $(sudo systemctl is-active bankconverter)
echo "New backend (bank-converter-backend):" $(sudo systemctl is-active bank-converter-backend)

echo -e "\n7. Frontend directory check:"
echo "Original frontend: $(ls -la /home/ubuntu/bank-statement-converter/frontend 2>/dev/null | wc -l) files"
echo "New frontend: $(ls -la /home/ubuntu/bank-statement-converter-unified/frontend 2>/dev/null | wc -l) files"

echo -e "\nDone! The original backend should now be working again."
echo "API is running on port 8000 and proxied through nginx on port 80."

EOF