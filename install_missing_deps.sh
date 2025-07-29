#!/bin/bash

# Install Missing Dependencies on AWS Server

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Installing Missing Dependencies on AWS Server"
echo "==========================================="

# SSH to server and install dependencies
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter-unified/backend

echo "1. Installing matplotlib and other missing dependencies..."
pip3 install matplotlib seaborn pandas numpy plotly kaleido

echo "2. Checking if all imports work now..."
python3 test_imports.py

echo "3. Restarting backend service..."
sudo systemctl restart bank-converter-backend

echo "4. Waiting for service to start..."
sleep 5

echo "5. Checking service status..."
sudo systemctl status bank-converter-backend --no-pager | head -20

echo "6. Testing API health endpoint..."
for i in {1..10}; do
    echo "Attempt $i..."
    if curl -s http://localhost:5000/health | python3 -m json.tool; then
        echo "✅ API is responding!"
        break
    fi
    sleep 2
done

echo "7. Checking if all backend services are disabled except main one..."
systemctl list-units --type=service | grep -E "bank|csv" | grep -v bank-converter-backend

echo "8. Making sure only one backend is running..."
# Disable any conflicting services
sudo systemctl disable bankconverter.service 2>/dev/null || true
sudo systemctl disable bankcsv-api.service 2>/dev/null || true
sudo systemctl stop bankconverter.service 2>/dev/null || true
sudo systemctl stop bankcsv-api.service 2>/dev/null || true

echo "9. Final service check..."
sudo systemctl is-active bank-converter-backend

echo "10. Checking nginx configuration..."
sudo nginx -t

echo "11. Testing through nginx..."
curl -s http://localhost/api/health || echo "Nginx proxy not configured for /api"

echo "Done!"
EOF