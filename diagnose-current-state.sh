#!/bin/bash

# Diagnose Current State
echo "🔍 Diagnosing Current State"
echo "==========================="
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

# Diagnose via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking if backend is actually running..."
ps aux | grep -E "python|uvicorn" | grep -v grep | head -5

echo -e "\n2. Checking if port 5000 is listening..."
netstat -tlnp 2>/dev/null | grep :5000 || ss -tlnp | grep :5000 || echo "Port 5000 not found"

echo -e "\n3. Testing backend directly from server..."
curl -v http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' 2>&1 | grep -E "(< HTTP|{|Connection refused)"

echo -e "\n4. Checking backend logs for errors..."
cd /home/ubuntu/backend
tail -30 backend.log

echo -e "\n5. Testing if simple-login.html exists..."
cd /home/ubuntu/bank-statement-converter
ls -la simple-login.html test-auth.html clear-cache.html 2>/dev/null

echo -e "\n6. Checking recent nginx access logs..."
echo "Recent requests:"
sudo tail -20 /var/log/nginx/access.log | grep -v "\.png\|\.ico\|\.css" | tail -10

echo -e "\n7. Checking nginx error logs..."
echo "Recent errors:"
sudo tail -20 /var/log/nginx/error.log

echo -e "\n8. Let's manually start backend in a more stable way..."
cd /home/ubuntu/backend
pkill -f python || true
pkill -f uvicorn || true
sleep 2

# Create a proper startup script
cat > /home/ubuntu/start_backend.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/backend
export PATH=/home/ubuntu/.local/bin:$PATH
source .env 2>/dev/null || true
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
EOF

chmod +x /home/ubuntu/start_backend.sh

echo "Starting backend with systemd-compatible script..."
nohup /home/ubuntu/start_backend.sh > /home/ubuntu/backend_stable.log 2>&1 &
echo $! > /home/ubuntu/backend.pid

sleep 5

echo -e "\n9. Final check..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend not responding"
    echo "Last logs:"
    tail -20 /home/ubuntu/backend_stable.log
fi

ENDSSH

echo ""
echo -e "${GREEN}✓ Diagnosis complete!${NC}"