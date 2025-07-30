#!/bin/bash

# Deploy Global Authentication System

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Global Authentication System"
echo "====================================="

# 1. Copy auth-global.js
echo "1. Copying auth-global.js..."
scp -i "$KEY_PATH" js/auth-global.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# 2. Update HTML files on server
echo -e "\n2. Updating HTML files to include global auth..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Function to add auth-global.js to a file
add_auth_to_file() {
    local file=$1
    if [ -f "$file" ]; then
        # Check if auth-global.js is already included
        if ! grep -q "auth-global.js" "$file"; then
            # Add before </body> tag
            sed -i '/<\/body>/i \    <script src="/js/auth-global.js"></script>' "$file"
            echo "  ✓ Updated: $file"
        else
            echo "  - Already has auth: $file"
        fi
    fi
}

# Update main pages
echo "Updating main pages..."
add_auth_to_file "index.html"
add_auth_to_file "pricing.html"
add_auth_to_file "business.html"
add_auth_to_file "blog.html"
add_auth_to_file "convert-pdf.html"
add_auth_to_file "merge-statements.html"
add_auth_to_file "split-by-date.html"
add_auth_to_file "analyze-transactions.html"

# Update other pages
echo -e "\nUpdating other pages..."
for file in *.html; do
    add_auth_to_file "$file"
done

echo -e "\n✅ All pages updated with global authentication!"
EOF

echo -e "\n3. Testing authentication persistence..."
# Test if auth-global.js is accessible
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/js/auth-global.js)

if [ "$AUTH_STATUS" == "200" ]; then
    echo "✅ Global authentication script is accessible!"
else
    echo "❌ auth-global.js returned HTTP $AUTH_STATUS"
fi

echo -e "\nDeployment complete!"
echo "====================
echo "Authentication is now persistent across all pages!"