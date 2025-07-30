#!/bin/bash
# Comprehensive deployment script for BankCSVConverter

echo "BankCSVConverter Deployment Script"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server details
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
BACKEND_DIR="/home/bankcsv/backend"
FRONTEND_DIR="/var/www/html"

echo -e "${YELLOW}Step 1: Backing up existing files...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
# Backup JavaScript files
sudo cp /var/www/html/js/stripe-integration.js /var/www/html/js/stripe-integration.js.backup 2>/dev/null || true
sudo cp /var/www/html/js/auth.js /var/www/html/js/auth.js.backup 2>/dev/null || true
sudo cp /var/www/html/js/dashboard.js /var/www/html/js/dashboard.js.backup 2>/dev/null || true

# Backup backend env
sudo cp /home/bankcsv/backend/.env /home/bankcsv/backend/.env.backup 2>/dev/null || true

# Backup HTML files
sudo cp /var/www/html/index.html /var/www/html/index.html.backup 2>/dev/null || true
sudo cp /var/www/html/pricing.html /var/www/html/pricing.html.backup 2>/dev/null || true
EOF

echo -e "${YELLOW}Step 2: Uploading new files...${NC}"

# Upload JavaScript files
scp stripe-integration.js auth.js dashboard.js ${SERVER_USER}@${SERVER_IP}:/tmp/

# Upload backend env
scp backend.env ${SERVER_USER}@${SERVER_IP}:/tmp/

# Upload HTML files with fixes
scp ../index.html ../pricing.html ${SERVER_USER}@${SERVER_IP}:/tmp/

echo -e "${YELLOW}Step 3: Deploying files on server...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
# Deploy JavaScript files
sudo cp /tmp/stripe-integration.js /var/www/html/js/
sudo cp /tmp/auth.js /var/www/html/js/
sudo cp /tmp/dashboard.js /var/www/html/js/

# Deploy backend env
sudo cp /tmp/backend.env /home/bankcsv/backend/.env

# Deploy HTML files
sudo cp /tmp/index.html /var/www/html/
sudo cp /tmp/pricing.html /var/www/html/

# Set correct permissions
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 644 /var/www/html/js/*.js
sudo chmod -R 644 /var/www/html/*.html
sudo chown www-data:www-data /home/bankcsv/backend/.env
sudo chmod 600 /home/bankcsv/backend/.env

# Clean up temp files
rm -f /tmp/stripe-integration.js /tmp/auth.js /tmp/dashboard.js /tmp/backend.env /tmp/index.html /tmp/pricing.html
EOF

echo -e "${YELLOW}Step 4: Restarting backend service...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
sudo systemctl restart bankcsv-backend
sleep 3
sudo systemctl status bankcsv-backend --no-pager
EOF

echo -e "${YELLOW}Step 5: Testing deployment...${NC}"

# Test backend health
echo "Testing backend health endpoint..."
curl -s https://bankcsvconverter.com/api/health | jq . || echo "Backend health check failed"

# Test Stripe endpoint
echo "Testing Stripe endpoint..."
curl -s https://bankcsvconverter.com/api/stripe/subscription-status || echo "Stripe endpoint test failed"

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Clear CloudFlare cache:"
echo "   - Go to CloudFlare dashboard"
echo "   - Navigate to Caching > Configuration"
echo "   - Click 'Purge Everything'"
echo ""
echo "2. Test the website:"
echo "   - Visit https://bankcsvconverter.com"
echo "   - Check pricing page: https://bankcsvconverter.com/pricing.html"
echo "   - Test login: https://bankcsvconverter.com/login.html"
echo "   - Verify Stripe checkout works correctly"
echo ""
echo "3. Monitor logs:"
echo "   ssh ${SERVER_USER}@${SERVER_IP} 'sudo journalctl -u bankcsv-backend -f'"