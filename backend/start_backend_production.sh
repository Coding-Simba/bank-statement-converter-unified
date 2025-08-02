#!/bin/bash
# Start backend in production mode

cd /home/ubuntu/backend

# Kill any existing uvicorn processes
pkill -f uvicorn || true

# Activate virtual environment
source venv/bin/activate

# Start uvicorn in background
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &

# Wait a moment
sleep 2

# Check if it started
if ps aux | grep -v grep | grep uvicorn > /dev/null; then
    echo "Backend started successfully"
    tail -10 backend.log
else
    echo "Backend failed to start"
    tail -20 backend.log
fi