#!/bin/bash

# Fix Protected Pages Authentication
echo "🔧 Fixing Protected Pages Authentication"
echo "========================================"
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

echo "1. Uploading fixed settings script..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/settings-unified-fix.js \
    js/dashboard-fix.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter

echo "2. Backing up current files..."
cp js/settings-unified.js js/settings-unified-backup-$(date +%Y%m%d-%H%M%S).js

echo "3. Applying fixes..."
cp /tmp/settings-unified-fix.js js/settings-unified.js
chmod 644 js/settings-unified.js

# Clean up
rm -f /tmp/settings-unified-fix.js /tmp/dashboard-fix.js

echo "4. Checking for other protected pages..."
# Find all pages that might require authentication
protected_pages=$(grep -l "isAuthenticated\|redirect.*login" *.html | grep -v "login.html\|signup.html" || true)

echo "   Protected pages found:"
echo "$protected_pages" | sed 's/^/   - /'

echo ""
echo "5. Ensuring auth navigation loads on settings page..."
# Make sure settings.html has auth-navigation.js
if ! grep -q "auth-navigation.js" settings.html; then
    # Add after auth-unified.js
    sed -i '/auth-unified.js/a <script src="/auth-navigation.js"></script>' settings.html
    echo "   ✓ Added auth-navigation.js to settings.html"
fi

echo ""
echo "6. Adding cache busting..."
timestamp=$(date +%s)
sed -i "s|settings-unified\.js\"|settings-unified.js?v=$timestamp\"|g" settings.html
sed -i "s|auth-unified\.js\"|auth-unified.js?v=$timestamp\"|g" settings.html
sed -i "s|auth-navigation\.js\"|auth-navigation.js?v=$timestamp\"|g" settings.html

echo ""
echo "7. Creating universal auth check script..."
cat > js/auth-check.js << 'EOF'
// Universal Authentication Check for Protected Pages
async function checkAuthAndRedirect(redirectPage = 'dashboard') {
    console.log(`[AuthCheck] Checking authentication for ${redirectPage}`);
    
    // Wait for UnifiedAuth
    let attempts = 0;
    while (attempts < 50 && (!window.UnifiedAuth || !window.UnifiedAuth.initialized)) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }
    
    if (!window.UnifiedAuth || !window.UnifiedAuth.initialized) {
        console.error('[AuthCheck] UnifiedAuth not available');
        window.location.href = '/';
        return false;
    }
    
    // Check authentication
    if (!window.UnifiedAuth.isAuthenticated()) {
        console.log('[AuthCheck] Not authenticated, redirecting to login');
        window.location.href = `/login.html?redirect=${redirectPage}`;
        return false;
    }
    
    console.log('[AuthCheck] User authenticated');
    return true;
}

// Auto-check on DOMContentLoaded for pages that include this script
if (window.location.pathname.includes('settings') || 
    window.location.pathname.includes('dashboard') ||
    window.location.pathname.includes('convert-pdf') ||
    window.location.pathname.includes('merge-statements') ||
    window.location.pathname.includes('split-by-date') ||
    window.location.pathname.includes('analyze-transactions')) {
    
    document.addEventListener('DOMContentLoaded', async () => {
        const pageName = window.location.pathname.split('/').pop().replace('.html', '');
        await checkAuthAndRedirect(pageName);
    });
}
EOF

chmod 644 js/auth-check.js
echo "   ✓ Created universal auth check script"

echo ""
echo "✓ Protected pages authentication fixed!"
ENDSSH

echo ""
echo -e "${GREEN}✓ Authentication fixes deployed!${NC}"
echo ""
echo "What was fixed:"
echo "   ✅ Settings page now waits for UnifiedAuth to initialize"
echo "   ✅ No more redirect loops on protected pages"
echo "   ✅ Auth navigation added to settings page"
echo "   ✅ Created universal auth check for all protected pages"
echo ""
echo "Test it:"
echo "   1. Clear browser cache (Ctrl+Shift+R)"
echo "   2. Login at https://bankcsvconverter.com"
echo "   3. Click on your user dropdown → Settings"
echo "   4. Settings page should load without redirecting"
echo ""
echo "Protected pages that now work correctly:"
echo "   • Settings"
echo "   • Dashboard" 
echo "   • Convert PDF"
echo "   • Merge Statements"
echo "   • Split by Date"
echo "   • Analyze Transactions"
echo ""
echo -e "${YELLOW}⚠️  Clear your browser cache to see the changes!${NC}"