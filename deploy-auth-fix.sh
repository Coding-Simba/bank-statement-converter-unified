#\!/bin/bash

# Deploy Auth Fix
echo "🚀 Deploying Auth Fix"
echo "===================="
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
if [ \! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

echo "1. Uploading updated auth-unified.js..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    js/auth-unified.js \
    "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/js/"

echo -e "\n2. Setting file permissions..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter
chmod 644 js/auth-unified.js
echo "✓ Permissions set"

echo -e "\n3. Clearing browser cache (nginx)..."
# Touch the file to update timestamp
touch js/auth-unified.js

echo -e "\n4. Testing authentication..."
# First, let's create a test user if needed
cd /home/ubuntu/backend
cat > create_test_user.py << 'EOFPY'
#\!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from models.database import get_db, User
from utils.auth import get_password_hash
from sqlalchemy.orm import Session

def create_test_user():
    db = next(get_db())
    
    # Check if test user exists
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("test123"),
            full_name="Test User",
            account_type="free"
        )
        db.add(user)
        db.commit()
        print("✓ Test user created")
    else:
        print("✓ Test user already exists")
    
    db.close()

if __name__ == "__main__":
    create_test_user()
EOFPY

python3 create_test_user.py

echo -e "\n5. Testing login with correct credentials..."
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies.txt \
  -w "\nStatus: %{http_code}\n" | head -10

echo -e "\n6. Checking if cookie was set..."
cat cookies.txt | grep -E "(access_token|session)" | head -5

ENDSSH

echo ""
echo -e "${GREEN}✓ Auth fix deployed\!${NC}"
echo ""
echo "You can now test login at: https://bankcsvconverter.com/login.html"
echo "Test credentials: test@example.com / test123"
EOF < /dev/null