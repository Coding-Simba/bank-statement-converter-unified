#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Debugging HTTP 500 Errors"
echo "========================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking nginx error logs..."
echo "=============================="
sudo tail -20 /var/log/nginx/error.log | grep -E "500|error|crit|alert|emerg"

echo -e "\n2. Checking nginx access logs for 500 errors..."
echo "============================================="
sudo tail -50 /var/log/nginx/access.log | grep " 500 "

echo -e "\n3. Testing direct file access..."
echo "================================"
# Check if files exist
echo "Files in root directory:"
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "\.html|\.js"

echo -e "\nFiles in frontend directory:"
ls -la /home/ubuntu/bank-statement-converter/frontend/ | grep -E "\.html|\.js" | head -10

echo -e "\n4. Testing simple static file..."
echo "==============================="
# Create a test file
echo "<html><body>Test</body></html>" | sudo tee /home/ubuntu/bank-statement-converter/test.html > /dev/null
curl -s http://localhost/test.html | head -5

echo -e "\n5. Checking nginx configuration for static files..."
echo "================================================="
sudo grep -A10 "location /" /etc/nginx/sites-available/bank-converter | head -20

echo -e "\n6. Testing frontend directory access..."
echo "====================================="
# Test accessing files from frontend directory
curl -sI http://localhost/frontend/index.html | head -5

echo -e "\n7. Checking file permissions..."
echo "==============================="
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "frontend|js"
ls -la /home/ubuntu/bank-statement-converter/frontend/ | head -10

echo -e "\n8. Quick fix - Creating symlinks for missing files..."
echo "==================================================="
cd /home/ubuntu/bank-statement-converter/

# Create symlinks if files are in frontend directory
if [ -f frontend/index.html ] && [ ! -f index.html ]; then
    echo "Creating symlink for index.html..."
    sudo ln -sf frontend/index.html index.html
fi

if [ -f frontend/pricing.html ] && [ ! -f pricing.html ]; then
    echo "Creating symlink for pricing.html..."
    sudo ln -sf frontend/pricing.html pricing.html
fi

if [ -f frontend/dashboard.html ] && [ ! -f dashboard.html ]; then
    echo "Creating symlink for dashboard.html..."
    sudo ln -sf frontend/dashboard.html dashboard.html
fi

if [ -f frontend/converter.html ] && [ ! -f converter.html ]; then
    echo "Creating symlink for converter.html..."
    sudo ln -sf frontend/converter.html converter.html
fi

# Check what we have now
echo -e "\nFiles after creating symlinks:"
ls -la /home/ubuntu/bank-statement-converter/ | grep -E "\.html"

echo -e "\n9. Testing pages again..."
echo "========================"
for page in index.html pricing.html login.html signup.html; do
    STATUS=$(curl -sI http://localhost/$page | head -1 | awk '{print $2}')
    echo "$page: HTTP $STATUS"
done

echo -e "\n10. Checking for any JavaScript errors..."
echo "======================================="
# Check if auth scripts are accessible
curl -sI http://localhost/js/auth-unified.js | head -5

EOF

echo -e "\n✅ Debug complete!"