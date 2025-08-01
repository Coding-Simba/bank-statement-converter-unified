#!/bin/bash

# Find and Fix Database
echo "🔍 Finding and Fixing Database"
echo "=============================="
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

# Find and fix database via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Finding database files..."
find /home/ubuntu -name "*.db" -type f 2>/dev/null | grep -E "(bank|csv|converter)" | head -10

echo -e "\n2. Checking backend directories..."
ls -la /home/ubuntu/backend/*.db 2>/dev/null || echo "No .db files in /home/ubuntu/backend/"
ls -la /home/ubuntu/bank-statement-converter/backend/*.db 2>/dev/null || echo "No .db files in /home/ubuntu/bank-statement-converter/backend/"

echo -e "\n3. Let's check the backend code for database location..."
cd /home/ubuntu/backend
grep -r "sqlite:///" . --include="*.py" | head -5

echo -e "\n4. Creating database fix script with correct path..."
cat > fix_db_schema.py << 'EOF'
#!/usr/bin/env python3
"""Fix database schema by adding missing columns."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Import database configuration
sys.path.insert(0, '/home/ubuntu/backend')
from models.database import DATABASE_URL

def fix_database_schema():
    """Add missing columns to the database."""
    print(f"Database URL: {DATABASE_URL}")
    
    # Extract database path from URL
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not db_path.startswith("/"):
            db_path = os.path.join("/home/ubuntu/backend", db_path)
    else:
        print("❌ Not a SQLite database")
        return
    
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Creating new database...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Define columns to add
    columns_to_add = [
        ("stripe_customer_id", "VARCHAR(255)"),
        ("auth_provider", "VARCHAR(50) DEFAULT 'local'"),
        ("provider_user_id", "VARCHAR(255)"),
        ("timezone", "VARCHAR(50) DEFAULT 'UTC'"),
        ("two_factor_secret", "VARCHAR(255)"),
        ("two_factor_enabled", "BOOLEAN DEFAULT 0"),
        ("api_key", "VARCHAR(255)"),
        ("notification_preferences", "TEXT"),
        ("company", "VARCHAR(255)")
    ]
    
    with engine.connect() as conn:
        # Get existing columns
        result = conn.execute(text("PRAGMA table_info(users)"))
        existing_columns = {row[1] for row in result}
        print(f"Existing columns: {', '.join(sorted(existing_columns))}")
        
        # Add missing columns
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✓ Added column: {column_name}")
                except OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding {column_name}: {e}")
            else:
                print(f"  Column {column_name} already exists")
        
        # Verify final schema
        result = conn.execute(text("PRAGMA table_info(users)"))
        final_columns = {row[1] for row in result}
        print(f"\nFinal columns: {', '.join(sorted(final_columns))}")
    
    print("\n✓ Database schema updated successfully!")

if __name__ == "__main__":
    fix_database_schema()
EOF

echo -e "\n5. Running database fix..."
python3 fix_db_schema.py

echo -e "\n6. Restarting backend..."
pkill -f "uvicorn main:app" || true
sleep 2

cd /home/ubuntu/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &

sleep 5

echo -e "\n7. Testing login endpoint..."
curl -X POST http://localhost:5000/v2/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\nStatus: %{http_code}\n" | head -10

echo -e "\n8. Checking backend logs for errors..."
tail -20 backend.log | grep -E "(ERROR|error|Error|Exception)" || echo "No errors in recent logs"

ENDSSH

echo ""
echo -e "${GREEN}✓ Database search and fix complete!${NC}"