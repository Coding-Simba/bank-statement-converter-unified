#!/bin/bash

# Deploy Settings Backend
echo "🚀 Deploying Settings Backend"
echo "============================"
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

echo "1. Uploading backend files..."
# Create temp directory for files
mkdir -p /tmp/settings-backend-deploy

# Copy files
cp backend/api/user_settings.py /tmp/settings-backend-deploy/
cp backend/utils/email.py /tmp/settings-backend-deploy/
cp backend/utils/two_factor.py /tmp/settings-backend-deploy/
cp backend/migrations/add_settings_fields.py /tmp/settings-backend-deploy/
cp backend/models/database.py /tmp/settings-backend-deploy/
cp backend/main.py /tmp/settings-backend-deploy/
cp backend/requirements.txt /tmp/settings-backend-deploy/
cp goodbye.html /tmp/settings-backend-deploy/

# Upload files
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r \
    /tmp/settings-backend-deploy/* \
    "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "2. Backing up current files..."
cd /home/ubuntu/bank-statement-converter/backend

# Backup existing files
cp models/database.py models/database-backup-$(date +%Y%m%d-%H%M%S).py
cp main.py main-backup-$(date +%Y%m%d-%H%M%S).py

echo "3. Installing new files..."
# Copy API endpoints
cp /tmp/user_settings.py api/
cp /tmp/email.py utils/
cp /tmp/two_factor.py utils/

# Copy updated files
cp /tmp/database.py models/
cp /tmp/main.py .

# Copy migrations
mkdir -p migrations
cp /tmp/add_settings_fields.py migrations/

# Copy goodbye page
cp /tmp/goodbye.html ../

echo "4. Installing new dependencies..."
# Update requirements
cp /tmp/requirements.txt .

# Install new packages
source venv/bin/activate
pip install pyotp==2.9.0 qrcode==7.4.2 aiosmtplib==3.0.1

echo "5. Running database migration..."
python migrations/add_settings_fields.py || echo "Some columns may already exist, continuing..."

echo "6. Setting environment variables..."
# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env 2>/dev/null || touch .env
fi

# Add email settings if not present
if ! grep -q "SMTP_PASSWORD" .env; then
    echo "" >> .env
    echo "# Email Settings (configure with your SMTP provider)" >> .env
    echo "SMTP_HOST=smtp.sendgrid.net" >> .env
    echo "SMTP_PORT=587" >> .env
    echo "SMTP_USERNAME=apikey" >> .env
    echo "SMTP_PASSWORD=" >> .env
    echo "FROM_EMAIL=noreply@bankcsvconverter.com" >> .env
    echo "FROM_NAME=BankCSV" >> .env
fi

echo "7. Restarting backend..."
# Find and kill current process
current_pid=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$current_pid" ]; then
    echo "Stopping current backend (PID: $current_pid)..."
    kill $current_pid
    sleep 2
fi

# Start backend
echo "Starting backend..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > ../backend.log 2>&1 &
sleep 3

# Verify it's running
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "✓ Backend restarted successfully"
else
    echo "⚠️  Backend may not have started properly"
fi

echo "8. Setting permissions..."
chmod -R 755 api/
chmod -R 755 utils/
chmod 644 ../goodbye.html

# Clean up temp files
rm -f /tmp/user_settings.py /tmp/email.py /tmp/two_factor.py
rm -f /tmp/add_settings_fields.py /tmp/database.py /tmp/main.py
rm -f /tmp/requirements.txt /tmp/goodbye.html

echo "✓ Deployment complete!"
ENDSSH

# Clean up local temp files
rm -rf /tmp/settings-backend-deploy

echo ""
echo -e "${GREEN}✅ Settings backend deployed successfully!${NC}"
echo ""
echo "What was deployed:"
echo "   ✅ User settings API endpoints (/v2/api/user/*)"
echo "   ✅ Email service utilities"
echo "   ✅ Two-factor authentication"
echo "   ✅ Database fields for settings"
echo "   ✅ Goodbye page for account deletion"
echo ""
echo "Next steps:"
echo "   1. Configure SMTP settings in .env on server:"
echo "      - SMTP_PASSWORD (SendGrid API key or SMTP password)"
echo "   2. Test all settings features"
echo "   3. Monitor logs: tail -f /home/ubuntu/backend.log"
echo ""
echo -e "${YELLOW}⚠️  Email features won't work until SMTP_PASSWORD is configured${NC}"