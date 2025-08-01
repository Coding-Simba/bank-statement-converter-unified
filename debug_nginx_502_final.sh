#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Final nginx 502 debugging"
echo "========================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Current nginx error log..."
echo "==========================="
sudo tail -10 /var/log/nginx/error.log

echo -e "\n2. Testing direct backend connection..."
echo "====================================="
curl -v http://localhost:5000/v2/api/auth/csrf 2>&1 | grep -E "Connected|HTTP|csrf"

echo -e "\n3. Checking all location blocks in nginx..."
echo "========================================"
sudo grep -B2 -A10 "location.*{" /etc/nginx/sites-available/bank-converter | grep -A12 "/v2/"

echo -e "\n4. Let's try a simpler nginx config for /v2..."
echo "============================================="

# Backup current config
sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.backup.v2

# Create a test with the simplest possible v2 config
sudo tee /tmp/nginx_v2_simple.conf << 'NGINX'
    location /v2/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
NGINX

# Check if we need to update the v2 location
echo -e "\n5. Current proxy_pass for /v2/..."
sudo grep -A5 "location /v2/" /etc/nginx/sites-available/bank-converter | grep proxy_pass

echo -e "\n6. Testing with curl through localhost nginx..."
echo "=============================================="
# Test nginx locally
curl -s http://localhost/v2/api/auth/csrf -H "Host: bankcsvconverter.com" 2>&1 || echo "Local nginx test failed"

echo -e "\n7. Checking if it's an IPv6 issue..."
echo "==================================="
# Try with IPv4 explicitly
curl -4 -s https://bankcsvconverter.com/v2/api/auth/csrf 2>&1 | head -20

echo -e "\n8. Let's check the actual nginx config being used..."
echo "=================================================="
sudo nginx -T 2>/dev/null | grep -A20 "location /v2/" | head -30

echo -e "\n9. Simple connectivity test..."
echo "============================="
# Can nginx reach the backend?
sudo -u www-data curl -s http://localhost:5000/v2/api/auth/csrf 2>&1 || echo "www-data user cannot reach backend"

EOF