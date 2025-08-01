#!/bin/bash

# Fix Database Schema Issues
echo "🔧 Fixing Database Schema Issues"
echo "================================"
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

# Fix database schema via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Creating database migration script..."
cat > fix_database_schema.py << 'EOF'
#!/usr/bin/env python3
"""Fix database schema by adding missing columns."""

import sqlite3
import os
import sys

def fix_database_schema():
    """Add missing columns to the database."""
    db_path = "bankcsvconverter.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        sys.exit(1)
    
    print(f"✓ Found database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"✓ Existing columns: {', '.join(sorted(existing_columns))}")
    
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
    
    # Add missing columns
    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                cursor.execute(sql)
                print(f"✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  Column {column_name} already exists")
                else:
                    print(f"❌ Error adding {column_name}: {e}")
        else:
            print(f"  Column {column_name} already exists")
    
    # Commit changes
    conn.commit()
    
    # Verify changes
    cursor.execute("PRAGMA table_info(users)")
    final_columns = {row[1] for row in cursor.fetchall()}
    print(f"\n✓ Final columns: {', '.join(sorted(final_columns))}")
    
    conn.close()
    print("\n✓ Database schema updated successfully!")

if __name__ == "__main__":
    fix_database_schema()
EOF

echo "2. Running database migration..."
python3 fix_database_schema.py

echo -e "\n3. Restarting backend service..."
# Kill existing processes
pkill -f "uvicorn main:app" || true
sleep 2

# Start backend with auto-restart
cat > start_backend_loop.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/backend
while true; do
    echo "Starting backend at $(date)"
    python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info
    echo "Backend crashed at $(date), restarting in 5 seconds..."
    sleep 5
done
EOF

chmod +x start_backend_loop.sh

# Start with nohup
nohup ./start_backend_loop.sh > backend.log 2>&1 &
echo $! > backend.pid

sleep 5

echo -e "\n4. Checking backend status..."
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "✓ Backend is running"
    
    # Test endpoints
    echo -e "\n5. Testing endpoints..."
    echo "Health check:"
    curl -s http://localhost:5000/health -w "\nStatus: %{http_code}\n" | head -5
    
    echo -e "\nAuth endpoints:"
    curl -s http://localhost:5000/v2/api/auth/csrf -w "\nStatus: %{http_code}\n" | head -5
else
    echo "✗ Backend failed to start"
    echo "Last 20 lines of backend.log:"
    tail -20 backend.log
fi

echo -e "\n6. Current database schema:"
sqlite3 bankcsvconverter.db "PRAGMA table_info(users);" | head -20

ENDSSH

echo ""
echo -e "${GREEN}✓ Database schema fix complete!${NC}"
echo ""
echo "Try logging in at: https://bankcsvconverter.com/login.html"