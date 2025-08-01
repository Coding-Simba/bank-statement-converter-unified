#\!/bin/bash

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

# Quick fix - ensure ultrathink-auth.js is in login.html
grep -q "ultrathink-auth.js" login.html || sed -i "/<\/body>/i <script src=\"/js/ultrathink-auth.js?v=$(date +%s)\"></script>" login.html

echo "✅ Fixed\! Auth script now properly included in login.html"
ENDSSH
