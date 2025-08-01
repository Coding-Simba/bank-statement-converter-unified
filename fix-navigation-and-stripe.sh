#!/bin/bash

# Fix Navigation and Stripe Return URL Issues
echo "🔧 Fixing Navigation and Stripe Issues"
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

echo "1. Issues being fixed:"
echo "   - Navigation not updating when logged in"
echo "   - Stripe return URL pointing to localhost"
echo "   - Dashboard link pointing to old dashboard"
echo ""

echo "2. Uploading fixes..."

# Upload auth navigation fix
echo "   Uploading auth-navigation-fix.js..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-navigation-fix.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "3. Backing up files..."
cd /home/ubuntu/bank-statement-converter

# Backup auth-navigation.js if it exists
if [ -f "auth-navigation.js" ]; then
    cp auth-navigation.js auth-navigation-backup-$(date +%Y%m%d-%H%M%S).js
fi

echo "4. Applying navigation fix..."
cp /tmp/auth-navigation-fix.js auth-navigation.js
chmod 644 auth-navigation.js

echo "5. Checking environment variables..."
cd /home/ubuntu/bank-statement-converter/backend

# Check if FRONTEND_URL is set correctly
if grep -q "FRONTEND_URL=https://bankcsvconverter.com" .env.production; then
    echo "   ✓ FRONTEND_URL already set correctly in .env.production"
else
    echo "   Updating FRONTEND_URL in .env.production..."
    if [ -f .env.production ]; then
        sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://bankcsvconverter.com|g' .env.production
    else
        echo "FRONTEND_URL=https://bankcsvconverter.com" >> .env.production
    fi
fi

# Also check the main .env file used by the service
if [ -f .env ]; then
    echo "   Checking main .env file..."
    if grep -q "FRONTEND_URL=http://localhost" .env; then
        echo "   Updating FRONTEND_URL in .env..."
        sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://bankcsvconverter.com|g' .env
    fi
fi

echo "6. Adding auth navigation script to all HTML pages..."
cd /home/ubuntu/bank-statement-converter

# Add auth-navigation.js to all HTML files that don't already have it
for html_file in *.html; do
    if [ -f "$html_file" ]; then
        # Check if auth-navigation.js is already included
        if ! grep -q "auth-navigation.js" "$html_file"; then
            # Add before closing body tag
            sed -i '/<\/body>/i <script src="/auth-navigation.js"></script>' "$html_file"
            echo "   Added auth-navigation.js to $html_file"
        fi
    fi
done

echo "7. Updating dashboard links to use new dashboard..."
# Update any links pointing to old dashboard
find . -name "*.html" -type f -exec sed -i 's|href="/dashboard-old.html"|href="/dashboard.html"|g' {} \;
find . -name "*.js" -type f -exec sed -i 's|/dashboard-old.html|/dashboard.html|g' {} \;

echo "8. Restarting backend service..."
sudo systemctl restart bank-statement-backend

echo "9. Adding cache busting..."
timestamp=$(date +%s)
find . -name "*.html" -type f -exec sed -i "s|auth-navigation\.js|auth-navigation.js?v=$timestamp|g" {} \;

echo "✓ All fixes applied successfully!"
ENDSSH

echo ""
echo -e "${GREEN}✓ Navigation and Stripe fixes deployed!${NC}"
echo ""
echo "What was fixed:"
echo "   ✅ Navigation now updates based on auth status"
echo "   ✅ Dashboard link shows when logged in"
echo "   ✅ Sign Up becomes Log Out when authenticated"
echo "   ✅ Stripe return URLs now use production domain"
echo "   ✅ Backend FRONTEND_URL updated to https://bankcsvconverter.com"
echo ""
echo "Testing instructions:"
echo "   1. Clear browser cache or use incognito mode"
echo "   2. Visit https://bankcsvconverter.com"
echo "   3. Login and verify navigation shows 'Dashboard' and 'Log Out'"
echo "   4. Try Stripe checkout - back button should stay on bankcsvconverter.com"
echo ""
echo -e "${YELLOW}⚠️  Backend was restarted - monitor for any issues${NC}"