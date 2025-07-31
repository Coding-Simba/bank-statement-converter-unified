#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Cookie-Based Authentication System"
echo "==========================================="

# Step 1: Deploy backend changes
echo "1. Deploying backend authentication updates..."

# Copy new auth files
scp -i "$KEY_PATH" backend/api/auth_cookie.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"
scp -i "$KEY_PATH" backend/migrations/add_refresh_token_fields.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/migrations/"
scp -i "$KEY_PATH" backend/models/database.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/models/"
scp -i "$KEY_PATH" backend/main.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/"

# Step 2: Run migration on server
echo "2. Running database migration..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend
source venv/bin/activate
python migrations/add_refresh_token_fields.py
echo "Database migration completed"
EOF

# Step 3: Update backend to include new auth router
echo "3. Updating backend to support cookie auth..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

# Update main.py to include cookie auth router
cat > temp_main_update.py << 'PYTHON'
import re

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Add import for cookie auth
if 'from api.auth_cookie import router as auth_cookie_router' not in content:
    import_section = content.find('from api.auth import router as auth_router')
    if import_section != -1:
        # Insert after the auth import
        content = content[:import_section] + 'from api.auth_cookie import router as auth_cookie_router\n' + content[import_section:]

# Add cookie auth router
if 'app.include_router(auth_cookie_router)' not in content:
    router_section = content.find('app.include_router(auth_router)')
    if router_section != -1:
        # Insert after auth router
        insert_pos = content.find('\n', router_section) + 1
        content = content[:insert_pos] + 'app.include_router(auth_cookie_router, prefix="/v2")  # New cookie-based auth\n' + content[insert_pos:]

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print("Backend updated to support cookie auth")
PYTHON

python temp_main_update.py
rm temp_main_update.py
EOF

# Step 4: Deploy frontend files
echo "4. Deploying frontend authentication service..."

# Copy new frontend files
scp -i "$KEY_PATH" js/auth-service.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
scp -i "$KEY_PATH" js/login-cookie-auth.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
scp -i "$KEY_PATH" js/stripe-cookie-auth.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Step 5: Update HTML files to use new auth
echo "5. Updating HTML files to use cookie auth..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Create a script to update all HTML files
cat > update_html_auth.py << 'PYTHON'
import os
import re

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

python update_html_auth.py
rm update_html_auth.py

# Update login.html to use new login handler
if grep -q "login-cookie-auth.js" login.html; then
    echo "login.html already uses cookie auth"
else
    # Add login-cookie-auth.js after auth-service.js
    sed -i '/auth-service.js/a\    <script src="/js/login-cookie-auth.js"></script>' login.html
fi

# Update pricing.html to use new Stripe handler
if grep -q "stripe-cookie-auth.js" pricing.html; then
    echo "pricing.html already uses cookie auth"
else
    # Add stripe-cookie-auth.js after auth-service.js
    sed -i '/auth-service.js/a\    <script src="/js/stripe-cookie-auth.js"></script>' pricing.html
fi

EOF

# Step 6: Restart backend
echo "6. Restarting backend service..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend
# Kill existing process
pkill -f "uvicorn main:app" || true
sleep 2
# Start new process
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
echo "Backend restarted with cookie authentication support"
EOF

echo -e "\n✅ Cookie-based authentication deployed!"
echo "==========================================="
echo "The system now supports:"
echo "1. HTTP-only cookies for JWT storage"
echo "2. Refresh token rotation"
echo "3. CSRF protection"
echo "4. Automatic token refresh"
echo ""
echo "Test the new auth at:"
echo "- https://bankcsvconverter.com/login.html"
echo "- Check console for [AuthService] messages"
echo ""
echo "Note: Old localStorage auth still works during migration"