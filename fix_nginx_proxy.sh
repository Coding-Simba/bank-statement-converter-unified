#!/bin/bash

# Fix Nginx Proxy Configuration for API

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Nginx Proxy Configuration"
echo "================================"

# SSH to server and fix nginx
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking current nginx configuration..."
sudo cat /etc/nginx/sites-available/default | grep -A 10 "location"

echo "2. Creating proper nginx configuration..."
sudo tee /etc/nginx/sites-available/bank-converter << 'NGINX'
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com 3.235.19.83;

    # Frontend
    location / {
        root /home/ubuntu/bank-statement-converter-unified/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # File upload settings
        client_max_body_size 50M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:5000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
NGINX

echo "3. Enabling the site..."
sudo ln -sf /etc/nginx/sites-available/bank-converter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null

echo "4. Testing nginx configuration..."
sudo nginx -t

echo "5. Reloading nginx..."
sudo systemctl reload nginx

echo "6. Testing API endpoints..."
echo "Testing /health endpoint:"
curl -s http://localhost/health | python3 -m json.tool || echo "Health endpoint failed"

echo -e "\nTesting /api endpoint:"
curl -s http://localhost/api | python3 -m json.tool || echo "API endpoint failed"

echo -e "\n7. Testing from external IP:"
echo "You can now test: http://$SERVER_IP/health"

echo -e "\n8. Final service status check:"
sudo systemctl status nginx --no-pager | head -5
sudo systemctl status bank-converter-backend --no-pager | head -5

echo -e "\n9. Checking for any errors in logs:"
sudo tail -5 /var/log/nginx/error.log 2>/dev/null || echo "No nginx errors"

echo -e "\nDone! The API should now be accessible at:"
echo "- http://bankcsvconverter.com/api"
echo "- http://3.235.19.83/api"

EOF