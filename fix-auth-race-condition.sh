#!/bin/bash

# Fix Authentication Race Condition
# This fixes the login redirect issue by addressing the race condition

echo "🔧 Fixing Authentication Race Condition"
echo "====================================="
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

echo "1. The issue identified:"
echo "   - Dashboard checks auth before UnifiedAuth is initialized"
echo "   - This causes redirect loop: login → dashboard → login"
echo "   - auth-unified.js has race condition with dashboard.js"
echo ""

echo "2. Deploying fixes..."

# Upload fixed files
echo "   Uploading fixed JavaScript files..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-unified-fix.js \
    js/dashboard-fix.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "   Backing up current files..."
cd /home/ubuntu/bank-statement-converter/js
cp auth-unified.js auth-unified-backup-$(date +%Y%m%d-%H%M%S).js
cp dashboard.js dashboard-backup-$(date +%Y%m%d-%H%M%S).js

echo "   Applying fixes..."
cp /tmp/auth-unified-fix.js auth-unified.js
cp /tmp/dashboard-fix.js dashboard.js

echo "   Setting permissions..."
chmod 644 auth-unified.js dashboard.js

echo "   Cleaning up..."
rm -f /tmp/auth-unified-fix.js /tmp/dashboard-fix.js

# Clear any browser cache by updating version
echo "   Updating cache version..."
timestamp=$(date +%s)
find /home/ubuntu/bank-statement-converter -name "*.html" -type f -exec sed -i "s/auth-unified\.js/auth-unified.js?v=$timestamp/g" {} \;
find /home/ubuntu/bank-statement-converter -name "*.html" -type f -exec sed -i "s/dashboard\.js/dashboard.js?v=$timestamp/g" {} \;

echo "✓ Fixes deployed successfully!"
ENDSSH

echo -e "${GREEN}✓ Authentication race condition fix deployed!${NC}"

echo ""
echo "3. What was fixed:"
echo "   ✅ Added initialization wait in dashboard.js"
echo "   ✅ Fixed redirect parameter handling (dashboard → /dashboard.html)"
echo "   ✅ Added proper authentication state checking"
echo "   ✅ Added cache busting to force reload"
echo ""

echo "4. Testing the fix..."
echo "   Clear your browser cache and try logging in again."
echo "   The login flow should now work correctly:"
echo "   1. Login at /login.html?redirect=dashboard"
echo "   2. After successful login → redirect to /dashboard.html"
echo "   3. Dashboard loads with user data"
echo ""

echo "5. Manual testing steps:"
echo "   a) Open browser in incognito/private mode"
echo "   b) Go to https://bankcsvconverter.com/dashboard.html"
echo "   c) You should be redirected to login with ?redirect=dashboard"
echo "   d) Login with your credentials"
echo "   e) You should land on the dashboard successfully"
echo ""

echo -e "${YELLOW}⚠️  Important: Clear browser cache or use incognito mode to test!${NC}"