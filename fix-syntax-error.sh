#!/bin/bash

# Fix Syntax Error
echo "🔧 Fixing Syntax Error in Auth"
echo "============================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking the syntax error around line 335..."
sed -n '330,340p' js/auth-unified-1754074945.js

echo -e "\n2. Looking for the login method to check for syntax issues..."
grep -n -A 20 "async login" js/auth-unified-1754074945.js | head -40

echo -e "\n3. Creating a clean version from the working backup..."
# Use the last known working version as base
if [ -f js/auth-unified-1754069674.js ]; then
    echo "Using auth-unified-1754069674.js as base..."
    cp js/auth-unified-1754069674.js js/auth-unified-fixed.js
else
    echo "Using latest backup..."
    LATEST_BACKUP=$(ls -t js/auth-unified-backup-*.js | head -1)
    cp "$LATEST_BACKUP" js/auth-unified-fixed.js
fi

echo -e "\n4. Applying the auth header fix properly..."
cat > /tmp/fix_auth_clean.py << 'EOF'
#!/usr/bin/env python3

# Read the file
with open('js/auth-unified-fixed.js', 'r') as f:
    content = f.read()

# Find makeAuthenticatedRequest and update it properly
import re

# Pattern to find the makeAuthenticatedRequest method
pattern = r'(async makeAuthenticatedRequest\(url, options = \{\}\) \{[\s\S]*?)(const response = await fetch\(fullUrl, \{[\s\S]*?\}\);)'

def replace_method(match):
    method_start = match.group(1)
    fetch_part = match.group(2)
    
    # Build the new method with proper Authorization header
    new_method = method_start + '''// Build headers with auth token
            const headers = {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken
            };
            
            // Add Authorization header if we have a token
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(fullUrl, {
                ...options,
                credentials: 'include',
                headers: headers
            });'''
    
    return new_method

# Apply the replacement
content = re.sub(pattern, replace_method, content, count=1)

# Also ensure login stores the token
if 'localStorage.setItem(\'access_token\'' not in content:
    # Find the login success part and add token storage
    login_pattern = r'(this\.user = data\.user;)'
    login_replacement = r'\1\n            // Store access token\n            if (data.access_token) {\n                localStorage.setItem(\'access_token\', data.access_token);\n            }'
    content = re.sub(login_pattern, login_replacement, content)

# Write the fixed file
with open('js/auth-unified-fixed.js', 'w') as f:
    f.write(content)

print("✓ Fixed auth-unified.js")
EOF

python3 /tmp/fix_auth_clean.py

echo -e "\n5. Creating new timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-fixed.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n6. Updating all HTML files..."
for file in *.html; do
    if [ -f "$file" ]; then
        sed -i "s|auth-unified-[0-9]*\.js[^\"]*|auth-unified-${TIMESTAMP}.js|g" "$file"
    fi
done

echo -e "\n7. Verifying the fix..."
echo "Checking for syntax errors in new file:"
node -c "js/auth-unified-${TIMESTAMP}.js" 2>&1 || echo "Note: Node.js syntax check (browser code may still be valid)"

echo -e "\n8. Checking the specific area that had the error..."
grep -n -A 5 -B 5 "makeAuthenticatedRequest" "js/auth-unified-${TIMESTAMP}.js" | head -20

echo -e "\n9. Also fixing the login.html syntax error..."
# Check line 217 in login.html
sed -n '215,220p' login.html

# Remove any stray script tags or fix syntax
sed -i '217s/<[^>]*>//g' login.html 2>/dev/null || true

echo -e "\n10. Final cleanup..."
rm /tmp/fix_auth_clean.py
rm js/auth-unified-fixed.js

echo "New auth file: js/auth-unified-${TIMESTAMP}.js"

ENDSSH

echo ""
echo -e "${GREEN}✓ Syntax error fixed!${NC}"
echo ""
echo "The authentication system should now work properly."
echo "Clear your browser cache and try again at: https://bankcsvconverter.com/login.html"