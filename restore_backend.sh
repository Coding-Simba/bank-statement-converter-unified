#!/bin/bash

# Restore Original Backend Configuration

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Restoring Original Backend Configuration"
echo "========================================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter-unified

echo "1. Checking current backend setup..."
echo "Current Python files in backend/api:"
ls -la backend/api/*.py | head -5

echo -e "\n2. Restoring from git (reverting import changes)..."
cd backend

# Restore main.py from git
git checkout 5d47636d8 -- main.py 2>/dev/null || echo "Git checkout of main.py failed"

# Also restore the API files to remove absolute imports
git checkout 5d47636d8 -- api/auth.py 2>/dev/null
git checkout 5d47636d8 -- api/statements.py 2>/dev/null
git checkout 5d47636d8 -- api/feedback.py 2>/dev/null
git checkout 5d47636d8 -- api/oauth.py 2>/dev/null
git checkout 5d47636d8 -- api/split_statement.py 2>/dev/null
git checkout 5d47636d8 -- api/analyze_transactions.py 2>/dev/null

echo -e "\n3. Checking what backend service was originally used..."
# Look for the original service configuration
if [ -f /etc/systemd/system/bankconverter.service ]; then
    echo "Found bankconverter.service:"
    cat /etc/systemd/system/bankconverter.service
fi

echo -e "\n4. Stopping current backend and starting original..."
sudo systemctl stop bank-converter-backend

# Check if original service should be used
if [ -f /home/ubuntu/bank-statement-converter-unified/backend/app.py ]; then
    echo "Found app.py - this might be the Flask backend"
    # Start the original service
    sudo systemctl start bankconverter 2>/dev/null || echo "bankconverter service not configured"
fi

echo -e "\n5. Checking which backend files exist:"
ls -la /home/ubuntu/bank-statement-converter-unified/backend/{app.py,main.py,server.py} 2>/dev/null

echo -e "\n6. Testing the API endpoints that were working before:"
sleep 3
# Test common endpoints
echo "Testing /api/upload:"
curl -s -X POST http://localhost:5000/api/upload -H "Content-Type: application/json" -d '{}' | head -20

echo -e "\nChecking running processes:"
ps aux | grep -E "python.*backend|flask|fastapi|uvicorn" | grep -v grep

EOF

echo -e "\nWhat errors are you seeing specifically? This will help me identify which backend configuration was originally working."