#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing nginx v2 routes..."

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
# Check if v2 location already exists
if ! sudo grep -q "location /v2/" /etc/nginx/sites-available/bank-converter; then
    # Find the last location block and add v2 before the closing brace
    sudo sed -i '/location \/api\//,/^[[:space:]]*}/ { 
        /^[[:space:]]*}/ i\
\
    # V2 API routes for cookie auth\
    location /v2/ {\
        proxy_pass http://localhost:5000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_cache_bypass $http_upgrade;\
        proxy_set_header Cookie $http_cookie;\
        proxy_pass_header Set-Cookie;\
    }
    }' /etc/nginx/sites-available/bank-converter
    
    echo "Added v2 location block"
else
    echo "v2 location block already exists"
fi

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
echo "Nginx configuration updated"
EOF