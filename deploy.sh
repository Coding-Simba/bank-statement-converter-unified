#\!/bin/bash

# Deployment script for bank-statement-converter-unified backend
# Run this script on the AWS server

echo "🚀 Starting deployment of bank-statement-converter-unified backend..."

# Navigate to project directory
cd /home/ubuntu/bank-statement-converter-unified || exit 1

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull origin main

# Navigate to backend
cd backend || exit 1

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Stop the current service
echo "⏹️  Stopping current FastAPI service..."
sudo systemctl stop fastapi

# Give it a moment to fully stop
sleep 2

# Start the service again
echo "▶️  Starting FastAPI service..."
sudo systemctl start fastapi

# Check status
echo "✅ Checking service status..."
sudo systemctl status fastapi --no-pager

# Show recent logs
echo -e "\n📋 Recent logs:"
sudo journalctl -u fastapi -n 20 --no-pager

echo -e "\n✨ Deployment complete\!"
echo "🌐 The backend should now be accessible at http://3.235.19.83:5000"
echo "📝 New endpoints available:"
echo "   - POST /api/split-statement"
echo "   - POST /api/analyze-transactions"
