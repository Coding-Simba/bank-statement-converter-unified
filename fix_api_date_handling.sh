#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing API date handling..."

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'SSHEOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Backing up api/statements.py..."
cp api/statements.py api/statements.py.backup_date_fix

echo -e "\n2. Fixing date handling in API..."
python3 << 'PYTHON'
import re

# Read the file
with open('api/statements.py', 'r') as f:
    content = f.read()

# Fix the date handling
old_code = """                for trans in sorted_trans:
                    # Handle missing dates
                    if trans.get('date'):
                        date_str = trans['date'].strftime('%Y-%m-%d')
                    else:
                        date_str = "2024-01-01"  # Default date for transactions without dates"""

new_code = """                for trans in sorted_trans:
                    # Handle missing dates
                    if trans.get('date'):
                        # Handle both string and datetime objects
                        if hasattr(trans['date'], 'strftime'):
                            date_str = trans['date'].strftime('%Y-%m-%d')
                        else:
                            date_str = str(trans['date'])  # Already a string
                    else:
                        date_str = "2024-01-01"  # Default date for transactions without dates"""

content = content.replace(old_code, new_code)

# Write back
with open('api/statements.py', 'w') as f:
    f.write(content)

print("✅ Fixed date handling in API")
PYTHON

echo -e "\n3. Restarting service..."
sudo systemctl restart bankconverter

echo -e "\n✅ API date handling fixed\!"

SSHEOF
