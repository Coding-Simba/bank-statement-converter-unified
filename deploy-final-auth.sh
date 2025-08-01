#!/bin/bash

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

echo "🎯 Deploying FINAL authentication fix..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

# Update all pages to use the final auth system
for file in index.html login.html signup.html dashboard-modern.html settings.html pricing.html convert-pdf.html merge-statements.html split-by-date.html analyze-transactions.html; do
    if [ -f "$file" ]; then
        # Replace any existing auth script with the final version
        sed -i 's/auth-unified-fixed.js/auth-unified-final.js/g' "$file"
        sed -i 's/auth-cookie-based.js/auth-unified-final.js/g' "$file"
        sed -i 's/auth-unified-ultrathink.js/auth-unified-final.js/g' "$file"
        
        # Ensure the final auth script is included
        if ! grep -q "auth-unified-final.js" "$file"; then
            sed -i '/<\/body>/i <script src="/js/auth-unified-final.js"></script>' "$file"
        fi
        
        echo "✅ Updated $file"
    fi
done

echo -e "\n🎯 FINAL AUTH SYSTEM DEPLOYED!"
echo ""
echo "The authentication now:"
echo "✅ ALWAYS uses localStorage for persistence"
echo "✅ Works whether 'Remember me' is checked or not"
echo "✅ Remember me only affects token expiration time"
echo "✅ Auth state persists across all page navigations"
echo "✅ Navbar updates immediately on all pages"
ENDSSH