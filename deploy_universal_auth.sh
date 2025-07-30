#\!/bin/bash

# Deploy Universal Authentication

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Universal Authentication"
echo "================================="

# 1. Deploy files
echo "1. Deploying auth-universal.js..."
scp -i "$KEY_PATH" js/auth-universal.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
scp -i "$KEY_PATH" dashboard-modern.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/dashboard.html"

# 2. Add to all pages
echo -e "\n2. Adding to all pages..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'SSH_END'
cd /home/ubuntu/bank-statement-converter/frontend

# Add auth-universal.js to all HTML files before </body>
for file in *.html; do
    if [ -f "$file" ]; then
        # Check if already has auth-universal.js
        if \! grep -q "auth-universal.js" "$file"; then
            # Add before </body>
            sed -i '/<\/body>/i \    <script src="/js/auth-universal.js"></script>' "$file"
            echo "  ✓ Added to: $file"
        else
            echo "  - Already has: $file"
        fi
    fi
done

echo -e "\n✅ Universal auth added to all pages\!"
SSH_END

echo -e "\n✅ Deployment complete\!"
echo "================================="
echo "The authentication should now persist across ALL pages\!"
