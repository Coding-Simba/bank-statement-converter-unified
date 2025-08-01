#!/bin/bash

# Fix Signup Page
echo "🔧 Fixing Signup Page"
echo "===================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking current signup.html script references..."
echo "Current auth script in signup.html:"
grep "auth-unified" signup.html

echo -e "\n2. Getting the latest auth script version..."
LATEST_AUTH=$(ls -t js/auth-unified-*.js 2>/dev/null | head -1 | xargs basename)
if [ -z "$LATEST_AUTH" ]; then
    echo "No timestamped auth file found, using original"
    LATEST_AUTH="auth-unified.js"
fi
echo "Latest auth script: $LATEST_AUTH"

echo -e "\n3. Updating signup.html to use the latest auth script..."
# Update signup.html
sed -i "s|auth-unified\.js[^\"]*|${LATEST_AUTH}|g" signup.html

echo -e "\n4. Verifying the update..."
echo "Updated auth script in signup.html:"
grep "auth-unified" signup.html

echo -e "\n5. Double-checking all pages are updated..."
for page in login.html index.html dashboard.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$page" ]; then
        echo -n "$page: "
        grep -o "auth-unified[^\"]*\.js" "$page" | head -1
    fi
done

echo -e "\n6. Testing registration endpoint..."
echo "Testing registration with new user:"
TIMESTAMP=$(date +%s)
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"test${TIMESTAMP}@example.com\",
    \"password\": \"TestPass123\",
    \"full_name\": \"Test User ${TIMESTAMP}\",
    \"company_name\": \"Test Company\"
  }" \
  -w "\nStatus: %{http_code}\n" -s | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'access_token' in data:
        print('✓ Registration successful!')
        print(f'  User ID: {data[\"user\"][\"id\"]}')
        print(f'  Email: {data[\"user\"][\"email\"]}')
    else:
        print('✗ Registration failed:', data)
except:
    print('✗ Error parsing response')
"

echo -e "\n7. Clearing nginx cache for signup page..."
# Force nginx to not cache these files
sudo touch /home/ubuntu/bank-statement-converter/signup.html
sudo nginx -s reload

ENDSSH

echo ""
echo -e "${GREEN}✓ Signup page fixed!${NC}"
echo ""
echo "IMPORTANT: Clear your browser cache again:"
echo "  - Chrome/Edge: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)"
echo "  - Select 'Cached images and files'"
echo "  - Click 'Clear data'"
echo ""
echo "Then try signing up at: https://bankcsvconverter.com/signup.html"