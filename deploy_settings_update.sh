#!/bin/bash

# Deploy Settings Page Update Script
# This script deploys the new settings page with full backend integration

echo "🚀 Deploying Settings Page Update..."
echo "=================================="

# Configuration
SERVER="3.235.19.83"
USER="ubuntu"
KEY_PATH="$HOME/Downloads/bank-statement-converter.pem"
REMOTE_PATH="/home/ubuntu"

# Check if SSH key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    exit 1
fi

echo "📦 Preparing deployment package..."

# Create deployment directory
DEPLOY_DIR="settings_deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p $DEPLOY_DIR

# Copy frontend files
echo "📄 Copying frontend files..."
cp settings.html $DEPLOY_DIR/
cp js/settings-integrated.js $DEPLOY_DIR/
cp js/auth-cookie.js $DEPLOY_DIR/

# Copy backend files
echo "🔧 Copying backend files..."
mkdir -p $DEPLOY_DIR/backend/api
mkdir -p $DEPLOY_DIR/backend/migrations
cp backend/api/user_settings_simple.py $DEPLOY_DIR/backend/api/
cp backend/api/user_export.py $DEPLOY_DIR/backend/api/
cp backend/migrations/add_user_preferences.py $DEPLOY_DIR/backend/migrations/
cp backend/main.py $DEPLOY_DIR/backend/

# Create deployment script
cat > $DEPLOY_DIR/deploy_on_server.sh << 'EOF'
#!/bin/bash

echo "🔄 Deploying settings update on server..."

# Backup current files
echo "📦 Creating backup..."
BACKUP_DIR="backup_settings_$(date +%Y%m%d_%H%M%S)"
mkdir -p ~/$BACKUP_DIR
cp /var/www/html/settings.html ~/$BACKUP_DIR/ 2>/dev/null || true
cp /var/www/html/js/settings-*.js ~/$BACKUP_DIR/ 2>/dev/null || true

# Deploy frontend files
echo "🌐 Deploying frontend..."
sudo cp settings.html /var/www/html/
sudo cp settings-integrated.js /var/www/html/js/
sudo cp auth-cookie.js /var/www/html/js/

# Deploy backend files
echo "🔧 Deploying backend..."
cp backend/api/user_settings_simple.py ~/backend/api/
cp backend/api/user_export.py ~/backend/api/
cp backend/main.py ~/backend/

# Run database migration
echo "🗄️ Running database migration..."
cd ~/backend
source venv/bin/activate
python migrations/add_user_preferences.py

# Restart backend service
echo "🔄 Restarting backend service..."
sudo systemctl restart bankcsv-backend

# Check service status
sleep 3
if sudo systemctl is-active --quiet bankcsv-backend; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service failed to start"
    sudo journalctl -u bankcsv-backend -n 50
    exit 1
fi

# Test endpoints
echo "🧪 Testing endpoints..."
curl -s http://localhost:5000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding"
fi

# Clear browser cache
echo "🧹 Cache busting..."
sudo find /var/www/html -name "*.html" -exec sed -i 's/\.js"/\.js?v='$(date +%s)'"/g' {} \;

echo "✅ Settings update deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test the settings page at https://bankcsvconverter.com/settings.html"
echo "2. Verify all forms are working"
echo "3. Check that preferences are saved"
echo "4. Test password change functionality"
echo "5. Verify Stripe customer portal integration"
EOF

chmod +x $DEPLOY_DIR/deploy_on_server.sh

# Copy deployment package to server
echo "📤 Uploading to server..."
scp -i "$KEY_PATH" -r $DEPLOY_DIR "$USER@$SERVER:~/"

# Execute deployment on server
echo "🚀 Executing deployment..."
ssh -i "$KEY_PATH" "$USER@$SERVER" "cd ~/$DEPLOY_DIR && ./deploy_on_server.sh"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf $DEPLOY_DIR

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Manual verification steps:"
echo "1. Visit https://bankcsvconverter.com/settings.html"
echo "2. Test profile update functionality"
echo "3. Test password change (use a test account)"
echo "4. Test notification preferences"
echo "5. Test conversion preferences"
echo "6. Verify usage statistics display"
echo "7. Test data export functionality"
echo "8. Test Stripe customer portal link"
echo ""
echo "🔍 To check logs:"
echo "ssh -i \"$KEY_PATH\" \"$USER@$SERVER\" \"sudo journalctl -u bankcsv-backend -f\""