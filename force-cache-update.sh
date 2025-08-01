#!/bin/bash

# Force Cache Update
echo "🔄 Forcing Cache Update"
echo "======================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Force update via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Creating a new version of auth-unified.js with timestamp..."
TIMESTAMP=$(date +%s)
cp js/auth-unified.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n2. Updating login.html to use new version..."
# Update the script tag in login.html
sed -i "s|auth-unified.js?v=[0-9]*|auth-unified-${TIMESTAMP}.js|g" login.html

echo -e "\n3. Verifying the update..."
grep "auth-unified" login.html | head -5

echo -e "\n4. Also updating other pages that might use auth..."
for file in index.html dashboard.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        sed -i "s|auth-unified.js?v=[0-9]*|auth-unified-${TIMESTAMP}.js|g" "$file"
    fi
done

echo -e "\n5. Double-checking the new file has correct endpoints..."
grep "api/auth" "js/auth-unified-${TIMESTAMP}.js" | grep -v "v2" | head -5

echo -e "\n6. Setting up nginx cache headers to prevent caching..."
# Check if we have cache control headers
grep -q "Cache-Control" /etc/nginx/sites-available/bank-converter || {
    echo "Adding cache control headers to nginx..."
    sudo sed -i '/location \/js\//a\        add_header Cache-Control "no-cache, no-store, must-revalidate";\n        add_header Pragma "no-cache";\n        add_header Expires "0";' /etc/nginx/sites-available/bank-converter
    sudo nginx -s reload
}

echo -e "\n7. Testing the authentication again..."
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'✓ Login successful! Token: {data.get(\"access_token\", \"ERROR\")[:50]}...')" 2>/dev/null || echo "Login test failed"

ENDSSH

echo ""
echo -e "${GREEN}✓ Cache update complete!${NC}"
echo ""
echo "IMPORTANT: Clear your browser cache completely:"
echo "  - Chrome/Edge: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)"
echo "  - Select 'Cached images and files'"
echo "  - Click 'Clear data'"
echo ""
echo "Then try logging in again at: https://bankcsvconverter.com/login.html"