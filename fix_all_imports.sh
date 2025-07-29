#!/bin/bash

# Fix ALL Import Issues on AWS Server

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing ALL Import Issues on AWS Server"
echo "======================================"

# SSH to server and fix all imports
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter-unified/backend

echo "1. Fixing auth.py imports..."
sed -i 's/from ..models.database/from models.database/g' api/auth.py
sed -i 's/from ..utils.auth/from utils.auth/g' api/auth.py
sed -i 's/from ..middleware.auth_middleware/from middleware.auth_middleware/g' api/auth.py

echo "2. Fixing statements.py imports..."
sed -i 's/from \.\./from /g' api/statements.py

echo "3. Fixing feedback.py imports..."
sed -i 's/from \.\./from /g' api/feedback.py

echo "4. Fixing oauth.py imports..."
sed -i 's/from \.\./from /g' api/oauth.py

echo "5. Fixing split_statement.py imports..."
sed -i 's/from \.\./from /g' api/split_statement.py

echo "6. Fixing analyze_transactions.py imports..."
sed -i 's/from \.\./from /g' api/analyze_transactions.py

# Fix any remaining relative imports in all Python files
echo "7. Fixing any remaining relative imports..."
find . -name "*.py" -type f -exec sed -i 's/from \.\.models/from models/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from \.\.utils/from utils/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from \.\.middleware/from middleware/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from \.\.parsers/from parsers/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from \.\.api/from api/g' {} \;

# Create a simple test script
echo "8. Creating test script..."
cat > test_imports.py << 'TESTPY'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")
try:
    from backend.api.auth import router as auth_router
    print("✅ Auth import successful")
except Exception as e:
    print(f"❌ Auth import failed: {e}")

try:
    from backend.api.statements import router as statements_router
    print("✅ Statements import successful")
except Exception as e:
    print(f"❌ Statements import failed: {e}")

try:
    from backend.models.database import init_db
    print("✅ Database import successful")
except Exception as e:
    print(f"❌ Database import failed: {e}")

try:
    from backend.main import app
    print("✅ Main app import successful")
except Exception as e:
    print(f"❌ Main app import failed: {e}")
TESTPY

chmod +x test_imports.py

# Run the test
echo "9. Running import test..."
cd /home/ubuntu/bank-statement-converter-unified
python3 backend/test_imports.py

# Update the run script to be simpler
echo "10. Updating run_backend.py..."
cat > backend/run_backend.py << 'RUNPY'
#!/usr/bin/env python3
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, backend_dir)

# Set environment variables
os.environ['PYTHONPATH'] = parent_dir

# Import and run the app
import main

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        main.app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
RUNPY

chmod +x backend/run_backend.py

# Restart service
echo "11. Restarting service..."
sudo systemctl daemon-reload
sudo systemctl restart bank-converter-backend

# Wait a bit for service to start
sleep 5

# Check status
echo "12. Checking service status..."
sudo systemctl status bank-converter-backend --no-pager | head -20

# Check if running
echo "13. Checking if API is responding..."
curl -s http://localhost:5000/health || echo "API not responding"

# Show error logs
echo "14. Recent error logs:"
tail -20 /home/ubuntu/backend-error.log 2>/dev/null || echo "No error log"

EOF

echo "Done fixing imports!"