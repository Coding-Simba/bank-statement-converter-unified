#!/bin/bash
# Automated deployment script for BankCSV backend
# Run this locally to deploy to your server

set -e  # Exit on error

# Server details
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"

echo "=== BankCSV Backend Deployment ==="
echo "Deploying to: $SERVER_USER@$SERVER_IP"
echo ""

# Check if we can connect to server
echo "Testing SSH connection..."
if ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✓ SSH connection established"
else
    echo "✗ Cannot connect to server. Please check:"
    echo "  - Your SSH key is properly configured"
    echo "  - The server IP is correct"
    echo "  - You have network connectivity"
    exit 1
fi

# Create deployment package
echo ""
echo "Preparing deployment package..."
DEPLOY_DIR="/tmp/bankcsv-deploy-$(date +%Y%m%d-%H%M%S)"
mkdir -p $DEPLOY_DIR

# Copy backend files
cp -r backend $DEPLOY_DIR/
cp -r js/api-config.js $DEPLOY_DIR/
cp -r js/analyze-transactions-api.js $DEPLOY_DIR/
cp test-analyze-api.html $DEPLOY_DIR/

echo "✓ Deployment package created"

# Upload files to server
echo ""
echo "Uploading files to server..."
scp -r $DEPLOY_DIR/backend $SERVER_USER@$SERVER_IP:/home/ubuntu/
scp $DEPLOY_DIR/api-config.js $SERVER_USER@$SERVER_IP:/tmp/
scp $DEPLOY_DIR/analyze-transactions-api.js $SERVER_USER@$SERVER_IP:/tmp/
scp $DEPLOY_DIR/test-analyze-api.html $SERVER_USER@$SERVER_IP:/tmp/

echo "✓ Files uploaded"

# Execute deployment on server
echo ""
echo "Executing deployment on server..."

ssh $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
set -e

echo "=== Starting remote deployment ==="

# Update frontend files if web root exists
if [ -d "/var/www/bankcsvconverter" ]; then
    echo "Updating frontend files..."
    sudo cp /tmp/api-config.js /var/www/bankcsvconverter/js/ 2>/dev/null || true
    sudo cp /tmp/analyze-transactions-api.js /var/www/bankcsvconverter/js/ 2>/dev/null || true
    sudo cp /tmp/test-analyze-api.html /var/www/bankcsvconverter/ 2>/dev/null || true
    echo "✓ Frontend files updated"
elif [ -d "/var/www/html" ]; then
    echo "Updating frontend files in /var/www/html..."
    sudo cp /tmp/api-config.js /var/www/html/js/ 2>/dev/null || true
    sudo cp /tmp/analyze-transactions-api.js /var/www/html/js/ 2>/dev/null || true
    sudo cp /tmp/test-analyze-api.html /var/www/html/ 2>/dev/null || true
    echo "✓ Frontend files updated"
else
    echo "⚠ Web root not found, skipping frontend updates"
fi

# Run the quick fix script
echo ""
echo "Running quick deployment..."
cd /home/ubuntu/backend/deploy
sudo bash quick-fix-analyze.sh

echo ""
echo "=== Deployment complete ==="
REMOTE_SCRIPT

# Clean up local temp files
rm -rf $DEPLOY_DIR

# Test the deployment
echo ""
echo "Testing deployment..."
sleep 3

# Test API endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/api/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ API is working! (HTTP $HTTP_CODE)"
    echo ""
    echo "=== SUCCESS ==="
    echo "The analyze-transactions feature is now deployed!"
    echo ""
    echo "Test it here:"
    echo "- Diagnostic tool: https://bankcsvconverter.com/test-analyze-api.html"
    echo "- Main feature: https://bankcsvconverter.com/analyze-transactions.html"
elif [ "$HTTP_CODE" = "502" ]; then
    echo "⚠ Backend service may still be starting (HTTP 502)"
    echo "Wait a moment and check: https://bankcsvconverter.com/test-analyze-api.html"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "⚠ Nginx configuration may need manual update (HTTP 404)"
    echo "SSH to server and check nginx configuration"
else
    echo "⚠ Could not verify deployment (HTTP $HTTP_CODE)"
    echo "Check manually: https://bankcsvconverter.com/test-analyze-api.html"
fi

echo ""
echo "To check backend logs on server:"
echo "ssh $SERVER_USER@$SERVER_IP 'sudo journalctl -u bankcsv-api -f'"