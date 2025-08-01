#!/bin/bash

# Deploy Authentication Fixes to Production
# This script deploys the auth fixes to the production server

echo "🚀 Deploying Authentication Fixes to Production..."

# Server details
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
KEY_PATH="$HOME/Downloads/bank-statement-converter.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Please update the KEY_PATH variable with the correct path to your SSH key"
    exit 1
fi

echo "📦 Preparing deployment package..."

# Create deployment directory
mkdir -p deploy-package

# Copy updated files
echo "📄 Copying updated files..."
cp backend/api/auth_cookie.py deploy-package/
cp js/auth-unified.js deploy-package/
cp -r js/old-auth-backup deploy-package/  # Include backup for reference

# Copy all updated HTML files that now use auth-unified.js
HTML_FILES=(
    "dashboard.html"
    "login.html"
    "settings.html"
    "pricing.html"
    "index.html"
    "dashboard-modern.html"
    "convert-pdf.html"
    "analyze-transactions.html"
    "merge-statements.html"
    "split-by-date.html"
)

for file in "${HTML_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" deploy-package/
        echo "  ✓ $file"
    fi
done

# Copy debug tool
cp debug-production-auth.html deploy-package/

echo ""
echo "🔄 Deploying to server..."

# Upload files to server
echo "📤 Uploading files..."
scp -i "$KEY_PATH" -r deploy-package/* "$SERVER_USER@$SERVER_IP:/tmp/"

# Connect to server and deploy
echo "🔧 Installing on server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    echo "📍 Connected to server..."
    
    # Backup current files
    echo "💾 Creating backups..."
    sudo mkdir -p /var/www/html/backup-$(date +%Y%m%d-%H%M%S)
    sudo cp /var/www/html/js/auth*.js /var/www/html/backup-$(date +%Y%m%d-%H%M%S)/ 2>/dev/null || true
    
    # Deploy backend fix
    echo "🐍 Updating backend..."
    sudo cp /tmp/auth_cookie.py /home/ubuntu/backend/api/
    
    # Deploy frontend files
    echo "🌐 Updating frontend..."
    sudo cp /tmp/auth-unified.js /var/www/html/js/
    
    # Deploy HTML files
    for file in dashboard.html login.html settings.html pricing.html index.html dashboard-modern.html convert-pdf.html analyze-transactions.html merge-statements.html split-by-date.html; do
        if [ -f "/tmp/$file" ]; then
            sudo cp "/tmp/$file" /var/www/html/
            echo "  ✓ Updated $file"
        fi
    done
    
    # Deploy debug tool
    sudo cp /tmp/debug-production-auth.html /var/www/html/
    
    # Move old auth scripts to backup
    echo "🗑️  Moving old auth scripts to backup..."
    sudo mkdir -p /var/www/html/js/old-auth-backup
    for script in auth.js auth-fixed.js auth-global.js auth-persistent.js auth-universal.js auth-service.js; do
        if [ -f "/var/www/html/js/$script" ]; then
            sudo mv "/var/www/html/js/$script" /var/www/html/js/old-auth-backup/
            echo "  ✓ Moved $script to backup"
        fi
    done
    
    # Set permissions
    echo "🔐 Setting permissions..."
    sudo chown -R www-data:www-data /var/www/html/
    
    # Restart backend
    echo "🔄 Restarting backend service..."
    sudo systemctl restart backend
    
    # Check backend status
    echo "✅ Checking backend status..."
    sudo systemctl status backend --no-pager | head -20
    
    # Clear any caches
    echo "🧹 Clearing caches..."
    sudo nginx -s reload
    
    echo "✨ Deployment complete!"
ENDSSH

echo ""
echo "🎉 Authentication fixes deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Visit https://bankcsvconverter.com/debug-production-auth.html"
echo "2. Run the debug tests to verify:"
echo "   - Scripts are loading correctly"
echo "   - Cookies are being set with secure flags"
echo "   - Authentication persists across tabs"
echo "   - Cross-tab logout works"
echo ""
echo "🔍 Debug URL: https://bankcsvconverter.com/debug-production-auth.html"

# Cleanup
rm -rf deploy-package

echo "✅ Done!"