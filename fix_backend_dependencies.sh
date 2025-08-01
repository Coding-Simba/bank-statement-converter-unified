#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing backend dependencies and starting server"
echo "=============================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Activating virtual environment..."
source venv/bin/activate

echo -e "\n2. Installing missing dependencies..."
pip install user-agents

echo -e "\n3. Checking if sessions router is included in main.py..."
if ! grep -q "from api.sessions import router as sessions_router" main.py; then
    echo "Adding sessions router import..."
    sed -i '/from api.stripe_payments import router as stripe_router/a from api.sessions import router as sessions_router' main.py
fi

if ! grep -q "app.include_router(sessions_router)" main.py; then
    echo "Adding sessions router..."
    sed -i '/app.include_router(stripe_router)/a app.include_router(sessions_router)' main.py
fi

echo -e "\n4. Running database migrations..."
cd migrations
if [ -f "add_sessions_table.py" ]; then
    python3 add_sessions_table.py
else
    echo "Creating sessions table migration..."
    cat > add_sessions_table.py << 'PYTHON'
"""Add sessions table migration."""
import sys
sys.path.append('..')

from models.database import engine, Base
from models.session import Session
from sqlalchemy import inspect

def create_sessions_table():
    """Create sessions table if it doesn't exist."""
    inspector = inspect(engine)
    
    if 'sessions' not in inspector.get_table_names():
        print("Creating sessions table...")
        Base.metadata.create_all(bind=engine, tables=[Session.__table__])
        print("Sessions table created successfully!")
    else:
        print("Sessions table already exists.")

if __name__ == "__main__":
    create_sessions_table()
PYTHON
    python3 add_sessions_table.py
fi
cd ..

echo -e "\n5. Starting backend server..."
pkill -f "uvicorn main:app" || true
sleep 2

nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &

sleep 5

echo -e "\n6. Verifying backend is running..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running!"
    
    echo -e "\n7. Testing auth endpoints..."
    
    echo "Getting CSRF token:"
    CSRF_RESPONSE=$(curl -s http://localhost:5000/v2/api/auth/csrf)
    echo "Response: $CSRF_RESPONSE"
    
    echo -e "\nTesting register endpoint:"
    curl -X POST http://localhost:5000/v2/api/auth/register \
         -H "Content-Type: application/json" \
         -d '{
           "email": "test@example.com",
           "password": "Test123!",
           "full_name": "Test User"
         }' \
         -w "\nStatus: %{http_code}\n" \
         2>/dev/null || echo "Failed"
    
    echo -e "\nBackend logs (last 20 lines):"
    tail -20 server.log
else
    echo "❌ Backend failed to start"
    echo "Full error log:"
    cat server.log
fi

EOF