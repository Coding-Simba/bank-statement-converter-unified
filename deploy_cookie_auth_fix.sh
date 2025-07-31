#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing deployment issues..."

# Create migrations directory and fix Python commands
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

# Create migrations directory if it doesn't exist
mkdir -p migrations

# Fix the migration script
cat > migrations/add_refresh_token_fields.py << 'PYTHON'
"""Add refresh token rotation fields to User model."""

from sqlalchemy import create_engine, text
from pathlib import Path

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / 'data' / 'bank_converter.db'
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def upgrade():
    """Add refresh token family fields for token rotation."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        # Add refresh_token_family if it doesn't exist
        if 'refresh_token_family' not in columns:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN refresh_token_family VARCHAR(255)
            """))
            print("Added refresh_token_family column")
        
        # Add refresh_token_version if it doesn't exist
        if 'refresh_token_version' not in columns:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN refresh_token_version INTEGER DEFAULT 1
            """))
            print("Added refresh_token_version column")
        
        conn.commit()
        print("Migration completed successfully")

if __name__ == "__main__":
    upgrade()
PYTHON

# Run migration with python3
source venv/bin/activate
python3 migrations/add_refresh_token_fields.py

# Update main.py to import cookie auth
cat > update_main.py << 'PYTHON'
import re

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Add import for cookie auth
if 'from api.auth_cookie import router as auth_cookie_router' not in content:
    import_line = 'from api.auth import router as auth_router'
    if import_line in content:
        content = content.replace(
            import_line,
            f'from api.auth_cookie import router as auth_cookie_router\n{import_line}'
        )

# Add cookie auth router
if 'app.include_router(auth_cookie_router' not in content:
    router_line = 'app.include_router(auth_router)'
    if router_line in content:
        content = content.replace(
            router_line,
            f'{router_line}\napp.include_router(auth_cookie_router, prefix="/v2")  # New cookie-based auth'
        )

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print("Backend updated to support cookie auth")
PYTHON

python3 update_main.py
rm update_main.py

# Update HTML files
cd /home/ubuntu/bank-statement-converter/frontend

cat > update_html_auth.py << 'PYTHON'
import os

def update_html_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has auth-service.js
    if 'auth-service.js' in content:
        print(f"Skipping {filepath} - already has auth-service.js")
        return
    
    # Find the </head> tag
    head_end = content.find('</head>')
    if head_end == -1:
        print(f"Warning: No </head> tag found in {filepath}")
        return
    
    # Insert auth-service.js before </head>
    insert = '\n    <!-- Cookie-based Authentication -->\n    <script src="/js/auth-service.js"></script>\n'
    content = content[:head_end] + insert + content[head_end:]
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated {filepath}")

# Update specific pages
pages = ['index.html', 'dashboard.html', 'pricing.html', 'login.html', 'signup.html', 'settings.html']
for page in pages:
    if os.path.exists(page):
        update_html_file(page)

print("\nAll HTML files updated")
PYTHON

python3 update_html_auth.py
rm update_html_auth.py

# Update login.html to use new login handler
if ! grep -q "login-cookie-auth.js" login.html; then
    sed -i '/auth-service.js/a\    <script src="/js/login-cookie-auth.js"></script>' login.html
    echo "Added login-cookie-auth.js to login.html"
fi

# Update pricing.html to use new Stripe handler
if ! grep -q "stripe-cookie-auth.js" pricing.html; then
    sed -i '/auth-service.js/a\    <script src="/js/stripe-cookie-auth.js"></script>' pricing.html
    echo "Added stripe-cookie-auth.js to pricing.html"
fi

# Restart backend
cd /home/ubuntu/bank-statement-converter/backend
pkill -f "uvicorn main:app" || true
sleep 2
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
echo "Backend restarted successfully"

EOF

echo "✅ Deployment issues fixed!"