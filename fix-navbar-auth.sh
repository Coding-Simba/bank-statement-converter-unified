#!/bin/bash

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

echo "🔧 Fixing navbar authentication display..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

# Add auth navbar fix right after navigation in all HTML files
for file in index.html login.html signup.html dashboard-modern.html settings.html pricing.html convert-pdf.html merge-statements.html split-by-date.html analyze-transactions.html; do
    if [ -f "$file" ]; then
        # Remove any existing navbar fix script first
        sed -i '/auth-navbar-fix.js/d' "$file"
        
        # Add the navbar fix script right after the </nav> tag
        sed -i '/<\/nav>/a \    <script src="/js/auth-navbar-fix.js"></script>' "$file"
        echo "✅ Updated $file"
    fi
done

# Also ensure the main auth script is still at the bottom
for file in index.html login.html signup.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Check if auth-unified-fixed.js is already there
        if ! grep -q "auth-unified-fixed.js" "$file"; then
            sed -i '/<\/body>/i <script src="/js/auth-unified-fixed.js"></script>' "$file"
        fi
    fi
done

echo -e "\n✅ Navbar auth fix deployed!"
echo "The navbar will now immediately show the logged-in state on all pages."
ENDSSH