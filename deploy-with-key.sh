#!/bin/bash
# Deployment script with SSH key
# Update the SSH_KEY_PATH with your actual key file path

# SSH key path
SSH_KEY_PATH="$HOME/Downloads/bank-statement-converter.pem"

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "❌ SSH key not found at: $SSH_KEY_PATH"
    echo "Please update the SSH_KEY_PATH variable in this script with your actual key path"
    echo ""
    echo "Common locations for AWS keys:"
    echo "  ~/.ssh/your-key-name.pem"
    echo "  ~/Downloads/your-key-name.pem"
    echo "  ~/Desktop/your-key-name.pem"
    exit 1
fi

echo "Using SSH key: $SSH_KEY_PATH"
echo "Deploying to: $SERVER_USER@$SERVER_IP"

# Test connection
echo "Testing SSH connection..."
if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'Connected successfully'" 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ Cannot connect. Check your key permissions:"
    echo "   chmod 400 $SSH_KEY_PATH"
    exit 1
fi

# Upload backend
echo "Uploading backend files..."
scp -i "$SSH_KEY_PATH" -r backend $SERVER_USER@$SERVER_IP:/home/ubuntu/
scp -i "$SSH_KEY_PATH" test-analyze-api.html $SERVER_USER@$SERVER_IP:/home/ubuntu/
scp -i "$SSH_KEY_PATH" js/api-config.js $SERVER_USER@$SERVER_IP:/home/ubuntu/
scp -i "$SSH_KEY_PATH" js/analyze-transactions-api.js $SERVER_USER@$SERVER_IP:/home/ubuntu/

# Deploy on server
echo "Running deployment on server..."
ssh -i "$SSH_KEY_PATH" $SERVER_USER@$SERVER_IP << 'REMOTE_COMMANDS'
# Update frontend files
sudo cp /home/ubuntu/api-config.js /var/www/html/js/ 2>/dev/null || echo "Frontend path may be different"
sudo cp /home/ubuntu/analyze-transactions-api.js /var/www/html/js/ 2>/dev/null
sudo cp /home/ubuntu/test-analyze-api.html /var/www/html/ 2>/dev/null

# Run quick fix
cd /home/ubuntu/backend/deploy
sudo bash quick-fix-analyze.sh

echo "Deployment complete!"
REMOTE_COMMANDS

echo ""
echo "✅ Deployment finished!"
echo "Test here: https://bankcsvconverter.com/test-analyze-api.html"