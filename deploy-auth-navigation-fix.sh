#!/bin/bash

# Deploy Complete Auth Navigation Fix
echo "🔧 Deploying Complete Auth Navigation Fix"
echo "========================================="
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

echo "1. Uploading improved auth navigation..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-navigation-complete.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter

echo "2. Backing up current auth navigation..."
if [ -f auth-navigation.js ]; then
    cp auth-navigation.js auth-navigation-backup-$(date +%Y%m%d-%H%M%S).js
fi

echo "3. Installing new auth navigation..."
cp /tmp/auth-navigation-complete.js auth-navigation.js
chmod 644 auth-navigation.js
rm -f /tmp/auth-navigation-complete.js

echo "4. Ensuring auth navigation loads AFTER UnifiedAuth..."
# Update script load order in HTML files
for html_file in *.html; do
    if [ -f "$html_file" ]; then
        # Remove existing auth-navigation script tag
        sed -i '/<script src="\/auth-navigation\.js/d' "$html_file"
        
        # Add auth-navigation after auth-unified
        if grep -q "auth-unified.js" "$html_file"; then
            # Add right after auth-unified.js
            sed -i '/auth-unified\.js/a <script src="/auth-navigation.js"></script>' "$html_file"
        else
            # Add before closing body tag
            sed -i '/<\/body>/i <script src="/auth-navigation.js"></script>' "$html_file"
        fi
    fi
done

echo "5. Adding cache busting..."
timestamp=$(date +%s)
find . -name "*.html" -type f -exec sed -i "s|auth-navigation\.js\"|auth-navigation.js?v=$timestamp\"|g" {} \;
find . -name "*.html" -type f -exec sed -i "s|auth-unified\.js\"|auth-unified.js?v=$timestamp\"|g" {} \;

echo "✓ Auth navigation fix deployed!"
ENDSSH

echo ""
echo -e "${GREEN}✓ Complete auth navigation fix deployed!${NC}"
echo ""
echo "What was fixed:"
echo "   ✅ Navigation now shows user email when logged in"
echo "   ✅ Dashboard link appears instead of 'Log In'"
echo "   ✅ User dropdown with Dashboard, Settings, and Log Out"
echo "   ✅ Mobile menu also updates correctly"
echo "   ✅ Proper load order ensures UnifiedAuth initializes first"
echo ""
echo "Features added:"
echo "   • User dropdown with email display"
echo "   • Quick access to Dashboard and Settings"
echo "   • Styled dropdown menu with icons"
echo "   • Mobile responsive design"
echo ""
echo "Test it:"
echo "   1. Clear browser cache (Ctrl+Shift+R)"
echo "   2. Visit https://bankcsvconverter.com"
echo "   3. Login with your account"
echo "   4. You should see:"
echo "      - 'Dashboard' link instead of 'Log In'"
echo "      - User dropdown with your email"
echo "      - Dropdown menu with Dashboard, Settings, Log Out"
echo ""
echo -e "${YELLOW}⚠️  Clear your browser cache to see the changes!${NC}"