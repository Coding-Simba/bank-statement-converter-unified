#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Debugging Cloudflare/Nginx Issues"
echo "================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Testing locally on server (bypassing Cloudflare)..."
echo "===================================================="

# Test API directly
echo "API test (localhost):"
curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool

# Test through nginx locally
echo -e "\nNginx test (localhost):"
curl -s http://localhost/v2/api/auth/csrf -H "Host: bankcsvconverter.com" | head -20

# Test pages
echo -e "\n2. Checking if pages exist..."
echo "============================"
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "signup.html|login.html|index.html"

# Check nginx access logs
echo -e "\n3. Recent nginx access logs..."
echo "============================="
sudo tail -10 /var/log/nginx/access.log | grep -v "kube-probe"

# Check nginx error logs
echo -e "\n4. Recent nginx error logs..."
echo "==========================="
sudo tail -10 /var/log/nginx/error.log

# Test direct IP access
echo -e "\n5. Testing direct IP access (bypassing Cloudflare DNS)..."
echo "======================================================"
echo "Note: This uses the server's direct IP"
curl -sI http://3.235.19.83/v2/api/auth/csrf

# Check nginx SSL config again
echo -e "\n6. Verifying nginx is listening on 443..."
echo "======================================="
sudo netstat -tlnp | grep -E ":80|:443"

# Check current nginx config
echo -e "\n7. Current active nginx configuration..."
echo "======================================"
sudo nginx -T 2>/dev/null | grep -E "server_name|listen|location /v2" -A 2 | head -30

# Cloudflare check
echo -e "\n8. Testing with Cloudflare headers..."
echo "==================================="
curl -s https://bankcsvconverter.com/v2/api/auth/csrf \
    -H "CF-Connecting-IP: 1.2.3.4" \
    -H "X-Forwarded-For: 1.2.3.4" \
    -H "Accept: application/json" \
    -v 2>&1 | grep -E "< HTTP|< Location|csrf_token" | head -20

EOF

echo -e "\n✅ Debug information collected!"