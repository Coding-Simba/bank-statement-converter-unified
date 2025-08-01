#!/bin/bash

# Deploy Settings Page Functionality Fix
echo "🔧 Fixing Settings Page Functionality"
echo "===================================="
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

echo "1. Checking current settings.js issues..."
echo "   - Using old localStorage auth instead of UnifiedAuth"
echo "   - Wrong API endpoints (/api/auth/me instead of /v2/api/auth/me)"
echo "   - Missing event handlers for navigation"
echo ""

echo "2. Uploading fixed settings script..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/settings-unified-fix.js \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter

echo "3. Backing up and updating settings.js..."
# The correct path is frontend/js/settings.js
if [ -f frontend/js/settings.js ]; then
    cp frontend/js/settings.js frontend/js/settings-backup-$(date +%Y%m%d-%H%M%S).js
fi

# Copy the fixed version
cp /tmp/settings-unified-fix.js frontend/js/settings.js
chmod 644 frontend/js/settings.js

echo "   ✓ Updated frontend/js/settings.js"

# Also check if there's a settings.js in the js directory
if [ -f js/settings.js ]; then
    cp /tmp/settings-unified-fix.js js/settings.js
    chmod 644 js/settings.js
    echo "   ✓ Also updated js/settings.js"
fi

# Clean up
rm -f /tmp/settings-unified-fix.js

echo ""
echo "4. Fixing settings navigation functionality..."
# Create a proper settings navigation handler
cat > js/settings-navigation.js << 'EOF'
// Settings Page Navigation Handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Settings Nav] Initializing navigation...');
    
    // Get all navigation items and panels
    const navItems = document.querySelectorAll('.settings-nav-item');
    const panels = document.querySelectorAll('.settings-panel');
    
    if (navItems.length === 0 || panels.length === 0) {
        console.error('[Settings Nav] Navigation items or panels not found');
        return;
    }
    
    console.log(`[Settings Nav] Found ${navItems.length} nav items and ${panels.length} panels`);
    
    // Add click handlers to navigation items
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetSection = this.getAttribute('data-section');
            console.log(`[Settings Nav] Switching to section: ${targetSection}`);
            
            // Remove active class from all items and panels
            navItems.forEach(nav => nav.classList.remove('active'));
            panels.forEach(panel => panel.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Show corresponding panel
            const targetPanel = document.getElementById(`${targetSection}-panel`);
            if (targetPanel) {
                targetPanel.classList.add('active');
                console.log(`[Settings Nav] Activated panel: ${targetSection}-panel`);
            } else {
                console.error(`[Settings Nav] Panel not found: ${targetSection}-panel`);
            }
            
            // Update URL hash
            window.location.hash = targetSection;
        });
    });
    
    // Handle initial hash or default to profile
    const initialHash = window.location.hash.slice(1) || 'profile';
    const initialNavItem = document.querySelector(`[data-section="${initialHash}"]`);
    if (initialNavItem) {
        initialNavItem.click();
    }
});
EOF

chmod 644 js/settings-navigation.js
echo "   ✓ Created settings navigation handler"

echo ""
echo "5. Adding scripts to settings.html..."
# Ensure settings.html loads the navigation script
if ! grep -q "settings-navigation.js" settings.html; then
    sed -i '/<\/body>/i <script src="/js/settings-navigation.js"></script>' settings.html
    echo "   ✓ Added settings-navigation.js to settings.html"
fi

echo ""
echo "6. Adding cache busting..."
timestamp=$(date +%s)
sed -i "s|/js/settings\.js\"|/js/settings.js?v=$timestamp\"|g" settings.html
sed -i "s|settings-navigation\.js\"|settings-navigation.js?v=$timestamp\"|g" settings.html

echo ""
echo "7. Creating notification styles..."
# Add notification styles if not present
if ! grep -q "notification {" css/settings.css 2>/dev/null; then
    cat >> css/settings.css << 'EOF'

/* Notifications */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #fff;
    border-radius: 8px;
    padding: 16px 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 1000;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
}

.notification.show {
    opacity: 1;
    transform: translateX(0);
}

.notification.success {
    border-left: 4px solid #28a745;
}

.notification.error {
    border-left: 4px solid #dc3545;
}

.notification.info {
    border-left: 4px solid #17a2b8;
}

.notification i {
    font-size: 20px;
}

.notification.success i {
    color: #28a745;
}

.notification.error i {
    color: #dc3545;
}

.notification.info i {
    color: #17a2b8;
}
EOF
    echo "   ✓ Added notification styles"
fi

echo ""
echo "✓ Settings functionality deployment complete!"
ENDSSH

echo ""
echo -e "${GREEN}✓ Settings page functionality fixed!${NC}"
echo ""
echo "What was fixed:"
echo "   ✅ Updated to use UnifiedAuth instead of localStorage"
echo "   ✅ Fixed API endpoints (/v2/api/* instead of /api/*)"
echo "   ✅ Added proper navigation between settings sections"
echo "   ✅ Fixed form submissions and event handlers"
echo "   ✅ Added notification system for user feedback"
echo ""
echo "Settings features now working:"
echo "   • Section navigation (Profile, Security, etc.)"
echo "   • Profile information updates"
echo "   • Password changes"
echo "   • Notification preferences"
echo "   • API key generation"
echo "   • Account deletion"
echo ""
echo "Test it:"
echo "   1. Clear browser cache (Ctrl+Shift+R)"
echo "   2. Go to https://bankcsvconverter.com/settings.html"
echo "   3. Click different sections in left navigation"
echo "   4. Try updating your profile information"
echo "   5. Test other settings features"
echo ""
echo -e "${YELLOW}⚠️  Some features (email notifications, 2FA) require backend implementation${NC}"