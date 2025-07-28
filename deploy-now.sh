#!/bin/bash
# Quick deployment script for CSS updates

echo "🚀 Bank Statement Converter - Quick Deploy"
echo "This will deploy the CSS fixes to production"
echo ""

# Check if IP is provided as argument
if [ -n "$1" ]; then
    LIGHTSAIL_IP="$1"
else
    echo "Please enter your Lightsail server IP address:"
    read LIGHTSAIL_IP
fi

if [ -z "$LIGHTSAIL_IP" ]; then
    echo "❌ Error: IP address is required"
    echo "Usage: ./deploy-now.sh [IP_ADDRESS]"
    exit 1
fi

SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found at $SSH_KEY"
    exit 1
fi

echo ""
echo "📡 Deploying to: $LIGHTSAIL_IP"
echo "🔑 Using SSH key: $SSH_KEY"
echo ""

# Test connection
echo "🔌 Testing connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$LIGHTSAIL_IP "echo 'Connected successfully'" 2>/dev/null; then
    echo "❌ Failed to connect to server"
    echo "Please check:"
    echo "  - The IP address is correct"
    echo "  - The server is running"
    echo "  - Your internet connection"
    exit 1
fi

echo "✅ Connection successful!"
echo ""

# Deploy the changes
echo "📦 Deploying changes..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@$LIGHTSAIL_IP << 'ENDSSH'
set -e
echo "📂 Navigating to project directory..."
cd /home/ubuntu/bank-statement-converter || cd /var/www/bank-statement-converter || { echo "Project directory not found"; exit 1; }

echo "📥 Pulling latest changes from GitHub..."
git pull origin main || { echo "Git pull failed"; exit 1; }

# Check if it's a Python app that needs restarting
if [ -f "backend/main.py" ] || [ -f "app.py" ]; then
    echo "🔄 Restarting Python application..."
    sudo systemctl restart bankconverter || sudo systemctl restart bank-converter || echo "Note: Could not restart service"
fi

# Check if it's served by nginx
if [ -d "/etc/nginx" ]; then
    echo "🔄 Reloading nginx..."
    sudo nginx -t && sudo systemctl reload nginx || echo "Note: nginx reload skipped"
fi

echo "✅ Deployment complete on server!"
ENDSSH

echo ""
echo "🎉 Deployment successful!"
echo "📱 The mobile navigation fix is now live!"
echo ""
echo "Please check: http://$LIGHTSAIL_IP"
echo ""