#!/bin/bash

# Deploy Authentication Race Condition and Stripe Integration Fixes
# This fixes both the login redirect loop and Stripe buy button issues

echo "🔧 Deploying Authentication & Stripe Fixes"
echo "=========================================="
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

echo "1. Issues being fixed:"
echo "   - Login redirect loop (auth race condition)"
echo "   - Stripe buy button not working (same race condition)"
echo "   - Both caused by scripts checking auth before UnifiedAuth initializes"
echo ""

echo "2. Deploying fixes..."

# Upload fixed files
echo "   Uploading fixed JavaScript files..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-unified-fix.js \
    js/dashboard-fix.js \
    js/stripe-integration-fix.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "   Backing up current files..."
cd /home/ubuntu/bank-statement-converter/js
cp auth-unified.js auth-unified-backup-$(date +%Y%m%d-%H%M%S).js
cp dashboard.js dashboard-backup-$(date +%Y%m%d-%H%M%S).js
cp stripe-integration.js stripe-integration-backup-$(date +%Y%m%d-%H%M%S).js

echo "   Applying fixes..."
cp /tmp/auth-unified-fix.js auth-unified.js
cp /tmp/dashboard-fix.js dashboard.js
cp /tmp/stripe-integration-fix.js stripe-integration.js

echo "   Setting permissions..."
chmod 644 auth-unified.js dashboard.js stripe-integration.js

echo "   Cleaning up..."
rm -f /tmp/auth-unified-fix.js /tmp/dashboard-fix.js /tmp/stripe-integration-fix.js

# Clear browser cache by updating version
echo "   Updating cache version..."
timestamp=$(date +%s)
find /home/ubuntu/bank-statement-converter -name "*.html" -type f -exec sed -i "s/auth-unified\.js/auth-unified.js?v=$timestamp/g" {} \;
find /home/ubuntu/bank-statement-converter -name "*.html" -type f -exec sed -i "s/dashboard\.js/dashboard.js?v=$timestamp/g" {} \;
find /home/ubuntu/bank-statement-converter -name "*.html" -type f -exec sed -i "s/stripe-integration\.js/stripe-integration.js?v=$timestamp/g" {} \;

echo "✓ All fixes deployed successfully!"
ENDSSH

echo -e "${GREEN}✓ Authentication & Stripe fixes deployed!${NC}"

echo ""
echo "3. What was fixed:"
echo "   ✅ Added initialization wait in dashboard.js"
echo "   ✅ Fixed redirect parameter handling (dashboard → /dashboard.html)"
echo "   ✅ Added initialization wait in stripe-integration.js"
echo "   ✅ Updated all BankAuth references to UnifiedAuth"
echo "   ✅ Added cache busting to force reload"
echo ""

echo "4. Testing the fixes..."
echo ""
echo "   A) Test Login Flow:"
echo "      1. Open incognito/private browser window"
echo "      2. Go to https://bankcsvconverter.com/dashboard.html"
echo "      3. You should be redirected to login with ?redirect=dashboard"
echo "      4. Login with your credentials"
echo "      5. You should land on the dashboard successfully"
echo ""
echo "   B) Test Stripe Integration:"
echo "      1. Go to https://bankcsvconverter.com/pricing.html"
echo "      2. Click any 'Buy' button"
echo "      3. If not logged in → redirect to signup"
echo "      4. If logged in → redirect to Stripe checkout"
echo ""

echo -e "${YELLOW}⚠️  Important: Clear browser cache or use incognito mode to test!${NC}"
echo ""
echo "5. Quick verification commands:"
echo "   curl -I https://bankcsvconverter.com/js/auth-unified.js | grep Last-Modified"
echo "   curl -I https://bankcsvconverter.com/js/stripe-integration.js | grep Last-Modified"