#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing login.html syntax error"
echo "=============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Create backup
cp login.html login.html.backup_syntax_fix

# Remove the problematic section with malformed script tags
sed -i '220,225d' login.html

# Add back clean script tags before </body>
sed -i '/<\/body>/i\    <script src="/js/api-config.js"></script>' login.html
sed -i '/<\/body>/i\    <script src="/js/auth.js"></script>' login.html
sed -i '/<\/body>/i\    <script src="/js/auth-fixed.js"></script>' login.html
sed -i '/<\/body>/i\    <script src="/js/auth-redirect-fix.js"></script>' login.html

echo "Login page syntax fixed!"
EOF