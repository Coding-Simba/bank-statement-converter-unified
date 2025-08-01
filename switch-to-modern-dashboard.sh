#!/bin/bash

# Switch to Modern Dashboard
echo "🎨 Switching to Modern Dashboard"
echo "================================"
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

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter

echo "1. Backing up current dashboard..."
cp dashboard.html dashboard-old.html
echo "   ✓ Backed up old dashboard to dashboard-old.html"

echo ""
echo "2. Making modern dashboard the main dashboard..."
cp dashboard-modern.html dashboard.html
echo "   ✓ Copied dashboard-modern.html to dashboard.html"

echo ""
echo "3. Updating all dashboard links..."
# Update all references to dashboard.html to ensure they use the modern version
find . -name "*.js" -type f -exec sed -i 's|/dashboard-old\.html|/dashboard.html|g' {} \;
find . -name "*.js" -type f -exec sed -i 's|dashboard-old\.html|dashboard.html|g' {} \;

# Ensure auth navigation points to correct dashboard
if [ -f auth-navigation.js ]; then
    sed -i 's|/dashboard-old\.html|/dashboard.html|g' auth-navigation.js
fi

echo "   ✓ Updated all JavaScript references"

echo ""
echo "4. Clearing cache with timestamp update..."
timestamp=$(date +%s)
# Update dashboard.html references with cache busting
find . -name "*.html" -type f -exec sed -i "s|dashboard\.html\"|dashboard.html?v=$timestamp\"|g" {} \;
find . -name "*.html" -type f -exec sed -i "s|dashboard\.html'|dashboard.html?v=$timestamp'|g" {} \;

echo "   ✓ Added cache busting to force reload"

echo ""
echo "5. Verifying dashboard has modern features..."
if grep -q "modern-dashboard" dashboard.html; then
    echo "   ✓ Modern dashboard CSS detected"
fi
if grep -q "chart" dashboard.html; then
    echo "   ✓ Charts feature detected"
fi
if grep -q "analytics" dashboard.html; then
    echo "   ✓ Analytics feature detected"
fi

echo ""
echo "✓ Modern dashboard is now the main dashboard!"
ENDSSH

echo ""
echo -e "${GREEN}✓ Successfully switched to modern dashboard!${NC}"
echo ""
echo "What was done:"
echo "   ✅ Modern dashboard (with CSS and features) is now at /dashboard.html"
echo "   ✅ Old dashboard backed up to /dashboard-old.html"
echo "   ✅ All links updated to use modern dashboard"
echo "   ✅ Cache busting added to force browser refresh"
echo ""
echo "Test it:"
echo "   1. Clear browser cache or use incognito mode"
echo "   2. Login at https://bankcsvconverter.com"
echo "   3. Click 'Dashboard' in navigation"
echo "   4. You should see the modern dashboard with:"
echo "      - Professional CSS styling"
echo "      - Charts and analytics"
echo "      - All modern features"
echo ""
echo -e "${YELLOW}⚠️  If you still see the old dashboard, hard refresh with Ctrl+Shift+R${NC}"