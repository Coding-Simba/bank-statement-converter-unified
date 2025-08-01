#!/bin/bash

# Check Auth Navigation
echo "🔍 Checking Auth Navigation File"
echo "================================"
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

# Check via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Looking for auth-navigation.js..."
find . -name "auth-navigation.js" -type f | head -10

echo -e "\n2. Checking content of auth-navigation.js..."
if [ -f "auth-navigation.js" ]; then
    echo "File size: $(wc -l auth-navigation.js)"
    echo -e "\nChecking for v2/api references:"
    grep -n "v2/api" auth-navigation.js | head -10
    
    echo -e "\nFirst 30 lines of file:"
    head -30 auth-navigation.js
fi

echo -e "\n3. Let's also check what's making the v2/api calls..."
# Check browser console logs from nginx
tail -100 /var/log/nginx/access.log | grep "v2/api" | tail -5

echo -e "\n4. Looking for any other auth-related JS files..."
find . -name "*auth*.js" -type f | grep -v node_modules | grep -v ".old" | head -20

ENDSSH

echo ""
echo -e "${GREEN}✓ Check complete!${NC}"