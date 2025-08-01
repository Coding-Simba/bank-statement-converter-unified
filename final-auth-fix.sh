#\!/bin/bash

# Final Auth Fix
echo "🔧 Final fix to use the correct auth script"
echo "=========================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Updating all HTML files to use auth-fixed.js..."
for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Remove all auth script references
        sed -i '/auth-unified\.js/d' "$file"
        sed -i '/auth-simple\.js/d' "$file"
        sed -i '/auth-working\.js/d' "$file"
        
        # Add auth-fixed.js if not already present
        if \! grep -q "auth-fixed.js" "$file"; then
            sed -i "/<\/body>/i <script src=\"/js/auth-fixed.js\"></script>" "$file"
        fi
        
        echo "✅ Updated $file"
    fi
done

echo -e "\n2. Verify auth-fixed.js is the correct one..."
head -20 js/auth-fixed.js | grep -E "auth-fixed|Auth|clear tokens"

echo -e "\n3. Current auth setup:"
echo "Auth files:"
ls -la js/auth-fixed.js
echo -e "\nReferences in login.html:"
grep "\.js" login.html | grep -v "google\|stripe" | head -5

echo -e "\n✅ Done\! The system is now using auth-fixed.js"
echo "This was the version that worked according to CLAUDE.md:"
echo "- Doesn't clear tokens on API errors"
echo "- Fixed the logout issues when navigating between pages"

ENDSSH
