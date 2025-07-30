#\!/bin/bash

# Server details
SERVER="ubuntu@3.235.19.83"
KEY_PATH="/Users/MAC/Desktop/bank-statement-converter.pem"

echo "Fixing deployment issues..."

ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
# Copy frontend files with sudo
echo "1. Copying frontend files with proper permissions..."
cd /home/ubuntu

# Create temporary directory
mkdir -p temp_deploy

# Check the actual backend service name
echo "2. Finding backend service..."
sudo systemctl list-units | grep -E "(backend|bank|fastapi|uvicorn|python)" | grep -v grep

# Check if backend is running with pm2
pm2 list

# Find the correct Python process
ps aux | grep -E "(python|uvicorn|fastapi)" | grep -v grep

# Check nginx sites
echo "3. Checking nginx configuration..."
ls -la /etc/nginx/sites-enabled/

# Find the web root directory
echo "4. Finding web root..."
grep -r "root" /etc/nginx/sites-enabled/ | grep -v "#" | head -5
ENDSSH

echo "Now copying files with sudo..."
# Copy files to home directory first
scp -i "$KEY_PATH" js/stripe-integration.js "$SERVER:/home/ubuntu/temp_deploy/"
scp -i "$KEY_PATH" js/dashboard.js "$SERVER:/home/ubuntu/temp_deploy/"
scp -i "$KEY_PATH" pricing.html "$SERVER:/home/ubuntu/temp_deploy/"
scp -i "$KEY_PATH" dashboard.html "$SERVER:/home/ubuntu/temp_deploy/"

# Then move them with sudo
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
# Copy to correct locations
sudo cp /home/ubuntu/temp_deploy/stripe-integration.js /var/www/bankcsvconverter.com/html/js/
sudo cp /home/ubuntu/temp_deploy/dashboard.js /var/www/bankcsvconverter.com/html/js/
sudo cp /home/ubuntu/temp_deploy/pricing.html /var/www/bankcsvconverter.com/html/
sudo cp /home/ubuntu/temp_deploy/dashboard.html /var/www/bankcsvconverter.com/html/

# Clean up
rm -rf /home/ubuntu/temp_deploy

# Restart backend using pm2
echo "5. Restarting backend..."
cd /home/ubuntu/backend
pm2 restart all

# Check status
pm2 status

echo "Deployment fixed\!"
ENDSSH
