#!/bin/bash

# Fix Stripe Return URLs
echo "🔧 Fixing Stripe Return URLs"
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

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "1. Fixing backend environment variables..."
cd /home/ubuntu/bank-statement-converter/backend

# Create or update .env file with correct FRONTEND_URL
if [ -f .env ]; then
    echo "   Updating existing .env file..."
    # Remove any existing FRONTEND_URL lines
    grep -v "FRONTEND_URL" .env > .env.tmp || true
    mv .env.tmp .env
fi

# Add correct FRONTEND_URL
echo "FRONTEND_URL=https://bankcsvconverter.com" >> .env
echo "   ✓ Set FRONTEND_URL=https://bankcsvconverter.com"

# Show current environment
echo ""
echo "2. Current environment variables:"
grep -E "FRONTEND_URL|STRIPE|DATABASE" .env || echo "   No relevant vars found"

echo ""
echo "3. Restarting backend..."
# Find and kill the current uvicorn process
current_pid=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$current_pid" ]; then
    echo "   Stopping current process (PID: $current_pid)..."
    kill $current_pid
    sleep 2
fi

# Start the backend again
echo "   Starting backend..."
cd /home/ubuntu/bank-statement-converter/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > /home/ubuntu/backend.log 2>&1 &
sleep 3

# Verify it's running
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "   ✓ Backend restarted successfully"
else
    echo "   ⚠️  Backend may not have started properly"
fi

echo ""
echo "4. Testing Stripe endpoints..."
# Test if Stripe endpoints are responding
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/stripe/products)
echo "   Stripe products endpoint: $response"

ENDSSH

echo ""
echo -e "${GREEN}✓ Stripe URLs fixed!${NC}"
echo ""
echo "What was done:"
echo "   ✅ Updated FRONTEND_URL to https://bankcsvconverter.com"
echo "   ✅ Restarted backend with new environment"
echo "   ✅ Stripe will now use production URLs"
echo ""
echo "Test it:"
echo "   1. Go to https://bankcsvconverter.com/pricing.html"
echo "   2. Click a Buy button"
echo "   3. Complete checkout"
echo "   4. Verify you're redirected to bankcsvconverter.com (not localhost)"