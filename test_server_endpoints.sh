#!/bin/bash

# Test Server Endpoints

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Testing Server Endpoints"
echo "========================"

# SSH to server and test
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Testing backend directly on localhost:5000..."
echo "Root endpoint:"
curl -s http://localhost:5000/ | python3 -m json.tool || echo "Failed"

echo -e "\nHealth endpoint:"
curl -s http://localhost:5000/health | python3 -m json.tool || echo "Failed"

echo -e "\nAPI auth endpoint:"
curl -s http://localhost:5000/api/auth | python3 -m json.tool || echo "Failed"

echo -e "\n2. Testing through nginx on port 80..."
echo "Root endpoint:"
curl -s http://localhost/ -H "Host: bankcsvconverter.com" | head -20

echo -e "\nHealth endpoint:"
curl -s -v http://localhost/health -H "Host: bankcsvconverter.com" 2>&1 | grep -E "< HTTP|< Location|^<"

echo -e "\nAPI endpoint:"
curl -s http://localhost/api -H "Host: bankcsvconverter.com" | python3 -m json.tool || echo "Not JSON"

echo -e "\n3. Checking backend logs for errors..."
tail -10 /home/ubuntu/backend.log 2>/dev/null || echo "No backend log"

echo -e "\n4. Checking if frontend is accessible..."
ls -la /home/ubuntu/bank-statement-converter-unified/frontend/ | head -5

echo -e "\n5. Testing from external (what users see)..."
echo "You can test these URLs from your browser:"
echo "- http://bankcsvconverter.com/"
echo "- http://bankcsvconverter.com/api"
echo "- http://bankcsvconverter.com/health"
echo "- http://3.235.19.83/"

echo -e "\n6. Summary of services:"
echo "Nginx:" $(sudo systemctl is-active nginx)
echo "Backend:" $(sudo systemctl is-active bank-converter-backend)
echo "Backend PID:" $(pgrep -f "run_backend.py")

EOF

echo -e "\n7. Testing from local machine..."
echo "Testing http://$SERVER_IP/health"
curl -s http://$SERVER_IP/health || echo "Not accessible from outside"