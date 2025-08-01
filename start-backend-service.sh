#!/bin/bash

# Start Backend Service
echo "🚀 Starting Backend Service"
echo "=========================="
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

# Start backend via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
# Kill any existing Python processes
pkill -f python || true
pkill -f uvicorn || true
sleep 2

# Start from the correct backend directory
cd /home/ubuntu/backend

# Create a startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/backend
while true; do
    echo "Starting backend at $(date)"
    python3 -m uvicorn main:app --host 0.0.0.0 --port 5000
    echo "Backend crashed at $(date), restarting in 5 seconds..."
    sleep 5
done
EOF

chmod +x start_backend.sh

# Start backend with nohup
echo "Starting backend service..."
nohup ./start_backend.sh > backend.log 2>&1 &
echo $! > backend.pid

sleep 5

# Check if it's running
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "✓ Backend is running"
    
    # Test endpoints
    echo "Testing endpoints..."
    curl -s http://localhost:5000/health -w "\nStatus: %{http_code}\n" | head -5
    echo ""
    curl -s http://localhost:5000/api/health -w "\nStatus: %{http_code}\n" | head -5
else
    echo "✗ Backend failed to start"
    echo "Last 20 lines of backend.log:"
    tail -20 backend.log
fi

# Show process info
echo ""
echo "Backend process:"
ps aux | grep -E "uvicorn|start_backend" | grep -v grep

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend service started!${NC}"
echo ""
echo "The backend will automatically restart if it crashes."
echo "To check logs: ssh ubuntu@$SERVER_IP 'tail -f /home/ubuntu/backend/backend.log'"
echo ""
echo "Try logging in at: https://bankcsvconverter.com/login.html"