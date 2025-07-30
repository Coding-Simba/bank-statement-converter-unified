#!/bin/bash

# Fix Cloudflare 521 Error

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Cloudflare 521 Error"
echo "==========================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Updating nginx to accept Cloudflare IPs..."

# Create Cloudflare IP list
sudo tee /etc/nginx/conf.d/cloudflare.conf << 'CLOUDFLARE'
# Cloudflare IP ranges
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 131.0.72.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;

# IPv6
set_real_ip_from 2400:cb00::/32;
set_real_ip_from 2606:4700::/32;
set_real_ip_from 2803:f800::/32;
set_real_ip_from 2405:b500::/32;
set_real_ip_from 2405:8100::/32;
set_real_ip_from 2a06:98c0::/29;
set_real_ip_from 2c0f:f248::/32;

real_ip_header CF-Connecting-IP;
CLOUDFLARE

echo "2. Updating nginx configuration to handle Cloudflare..."
sudo tee /etc/nginx/sites-available/bank-converter << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    # Accept connections from anywhere (including Cloudflare)
    server_name bankcsvconverter.com www.bankcsvconverter.com 3.235.19.83 _;

    root /home/ubuntu/bank-statement-converter/frontend;
    index index.html;

    # Maximum file upload size
    client_max_body_size 50M;

    # Cloudflare specific settings
    # Increase timeouts for Cloudflare
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Disable buffering for Cloudflare
    proxy_buffering off;
    
    # Handle Cloudflare headers
    proxy_set_header CF-Connecting-IP $remote_addr;
    proxy_set_header CF-IPCountry $http_cf_ipcountry;
    proxy_set_header CF-RAY $http_cf_ray;
    proxy_set_header CF-Visitor $http_cf_visitor;

    # Frontend - serve static files
    location / {
        try_files $uri $uri/ /index.html;
        
        # Allow Cloudflare caching
        add_header Cache-Control "public, max-age=3600";
    }

    # API proxy to backend on port 8000
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

    # Security headers (Cloudflare compatible)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
NGINX

echo "3. Testing nginx configuration..."
sudo nginx -t

echo "4. Reloading nginx..."
sudo systemctl reload nginx

echo "5. Ensuring services are running..."
sudo systemctl restart bankconverter
sudo systemctl status nginx --no-pager | head -5
sudo systemctl status bankconverter --no-pager | head -5

echo "6. Testing HTTP response..."
curl -I http://localhost/ 2>&1 | head -5

echo "7. Checking if firewall allows HTTP/HTTPS..."
sudo ufw status 2>/dev/null || echo "UFW not active"

echo -e "\n✅ Done! The server should now accept Cloudflare connections."
echo "If still getting 521, check in Cloudflare dashboard:"
echo "1. DNS record points to: 3.235.19.83"
echo "2. Proxy status is 'Proxied' (orange cloud)"
echo "3. SSL/TLS mode is set to 'Flexible' or 'Full'"

EOF