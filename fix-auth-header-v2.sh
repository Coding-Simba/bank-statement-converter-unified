#!/bin/bash

# Fix Auth Header V2
echo "🔧 Fixing Auth Header V2"
echo "======================="
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

echo "1. Creating a properly fixed version of makeAuthenticatedRequest..."
# Find the makeAuthenticatedRequest method and create a fixed version
cat > /tmp/fix_auth.py << 'EOF'
#!/usr/bin/env python3
import re

# Read the file
with open('js/auth-unified-1754069674.js', 'r') as f:
    content = f.read()

# Find and replace the makeAuthenticatedRequest method
# This is a more targeted approach
old_method = '''async makeAuthenticatedRequest(url, options = {}) {
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            const response = await fetch(fullUrl, {
                ...options,
                credentials: 'include',
                headers: {
                    ...options.headers,
                    'X-CSRF-Token': this.csrfToken
                }
            });'''

new_method = '''async makeAuthenticatedRequest(url, options = {}) {
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            // Include Authorization header if we have a token
            const headers = {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken
            };
            
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(fullUrl, {
                ...options,
                credentials: 'include',
                headers: headers
            });'''

# Replace the method
content = content.replace(old_method, new_method)

# Also fix the retry part
old_retry = '''// Retry request
                    return fetch(fullUrl, {
                        ...options,
                        credentials: 'include',
                        headers: {
                            ...options.headers,
                            'X-CSRF-Token': this.csrfToken
                        }
                    });'''

new_retry = '''// Retry request with refreshed token
                    const retryHeaders = {
                        ...options.headers,
                        'X-CSRF-Token': this.csrfToken
                    };
                    
                    const newToken = localStorage.getItem('access_token');
                    if (newToken) {
                        retryHeaders['Authorization'] = `Bearer ${newToken}`;
                    }
                    
                    return fetch(fullUrl, {
                        ...options,
                        credentials: 'include',
                        headers: retryHeaders
                    });'''

content = content.replace(old_retry, new_retry)

# Write back
with open('js/auth-unified-1754069674.js', 'w') as f:
    f.write(content)

print("✓ Fixed makeAuthenticatedRequest method")
EOF

python3 /tmp/fix_auth.py

echo -e "\n2. Also ensuring the login method stores the token..."
# Check if token is already being stored
if ! grep -q "localStorage.setItem('access_token'" js/auth-unified-1754069674.js; then
    echo "Adding token storage to login method..."
    sed -i '/this\.user = data\.user;/a\            \
            // Store access token for API requests\
            if (data.access_token) {\
                localStorage.setItem('"'"'access_token'"'"', data.access_token);\
            }' js/auth-unified-1754069674.js
fi

echo -e "\n3. Verifying the changes..."
echo "Checking makeAuthenticatedRequest:"
grep -A 20 "makeAuthenticatedRequest" js/auth-unified-1754069674.js | grep -E "(Authorization|Bearer|token)" | head -5

echo -e "\n4. Creating new timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-1754069674.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n5. Updating all HTML files to use new version..."
for file in *.html; do
    if [ -f "$file" ]; then
        sed -i "s|auth-unified-[0-9]*\.js[^\"]*|auth-unified-${TIMESTAMP}.js|g" "$file"
    fi
done

echo -e "\n6. Verifying HTML updates..."
grep "auth-unified-${TIMESTAMP}.js" pricing.html | head -2

echo -e "\n7. Cleaning up..."
rm /tmp/fix_auth.py

ENDSSH

echo ""
echo -e "${GREEN}✓ Auth header fix complete!${NC}"
echo ""
echo "The authentication system now properly includes Authorization headers."
echo ""
echo "IMPORTANT: Clear your browser cache completely:"
echo "  1. Press Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)"
echo "  2. Select 'Cached images and files'"
echo "  3. Click 'Clear data'"
echo ""
echo "Then try purchasing at: https://bankcsvconverter.com/pricing.html"