#!/bin/bash

# Fix production parser deployment
echo "🔧 Fixing production parser deployment..."

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"

# First, check the actual Python command on server
echo "Checking Python setup on server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'which python3 && python3 --version'

# Test the parser directly
echo -e "\nTesting parser import..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'cd /home/ubuntu/bank-statement-converter/backend && source venv/bin/activate && python3 -c "from universal_parser import parse_universal_pdf; print(\"Parser OK\")"'

# Check current server status
echo -e "\nChecking current server process..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'ps aux | grep -E "(python|uvicorn|main.py)" | grep -v grep'

# Start server with proper Python path
echo -e "\nStarting server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'cd /home/ubuntu/bank-statement-converter/backend && source venv/bin/activate && nohup python3 main.py > server.log 2>&1 & echo $! > server.pid'

sleep 5

# Check if running
echo -e "\nChecking server status..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'cd /home/ubuntu/bank-statement-converter/backend && curl -s http://localhost:5001/health || (echo "Server logs:" && tail -20 server.log)'

echo -e "\n✅ Done!"