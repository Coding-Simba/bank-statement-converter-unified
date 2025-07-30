#\!/bin/bash

# Deploy Modern Dashboard to Production

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Modern Dashboard"
echo "========================="

# Backup current dashboard
echo "1. Backing up current dashboard..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'BACKUP'
cd /home/ubuntu/bank-statement-converter/frontend
if [ -f dashboard.html ]; then
    cp dashboard.html dashboard_backup_$(date +%Y%m%d_%H%M%S).html
    echo "✓ Current dashboard backed up"
fi
BACKUP

# Copy new files
echo -e "\n2. Copying new dashboard files..."
scp -i "$KEY_PATH" dashboard-modern.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/dashboard.html"
scp -i "$KEY_PATH" css/modern-dashboard.css "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/css/"
scp -i "$KEY_PATH" js/modern-dashboard.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

echo -e "\n3. Setting permissions..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'PERMS'
cd /home/ubuntu/bank-statement-converter/frontend
chmod 644 dashboard.html
chmod 644 css/modern-dashboard.css
chmod 644 js/modern-dashboard.js
echo "✓ Permissions set"
PERMS

echo -e "\n4. Testing deployment..."
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/dashboard.html)

if [ "$DASHBOARD_STATUS" == "200" ]; then
    echo "✅ Modern dashboard deployed successfully\!"
    echo "View at: https://bankcsvconverter.com/dashboard.html"
else
    echo "❌ Dashboard returned HTTP $DASHBOARD_STATUS"
fi

echo -e "\nDeployment complete\!"
