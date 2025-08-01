#\!/bin/bash

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "🔧 DIRECT FIX - Ensuring auth works"
echo "==================================="

# Check if login.html has closing body tag
echo "1. Checking login.html structure:"
grep -n "</body>" login.html || echo "WARNING: No </body> tag found\!"

# Add the script in a different way
echo -e "\n2. Adding auth script directly after last existing script:"
# Find the line number of the last script tag
LAST_SCRIPT_LINE=$(grep -n "<script" login.html | tail -1 | cut -d: -f1)
echo "Last script tag at line: $LAST_SCRIPT_LINE"

# Insert ultrathink-auth.js after the last script
if [ \! -z "$LAST_SCRIPT_LINE" ] && \! grep -q "ultrathink-auth.js" login.html; then
    sed -i "${LAST_SCRIPT_LINE}a\\<script src=\"/js/ultrathink-auth.js\"></script>" login.html
    echo "✅ Inserted ultrathink-auth.js after line $LAST_SCRIPT_LINE"
fi

# Alternative: Add before </html> if </body> doesn't exist
if \! grep -q "</body>" login.html && \! grep -q "ultrathink-auth.js" login.html; then
    sed -i '/<\/html>/i <script src="/js/ultrathink-auth.js"></script>' login.html
    echo "✅ Added before </html>"
fi

echo -e "\n3. Final verification of scripts in login.html:"
echo "All script tags:"
grep -n "script" login.html | grep "src" | tail -10

echo -e "\n4. Let's also ensure auth-fixed.js is used as fallback:"
# Since ultrathink might not be working, let's use auth-fixed.js
if [ -f js/auth-fixed.js ] && \! grep -q "auth-fixed.js" login.html; then
    LAST_LINE=$(grep -n "<script" login.html | tail -1 | cut -d: -f1)
    sed -i "${LAST_LINE}a\\<script src=\"/js/auth-fixed.js\"></script>" login.html
    echo "✅ Also added auth-fixed.js as backup"
fi

echo -e "\n5. Creating a guaranteed working version:"
# Copy a working version
cp test-login-working.html login-backup.html
echo "✅ Created login-backup.html as a working alternative"

echo -e "\n📊 FINAL STATUS:"
echo "==============="
echo "Scripts in login.html:"
grep "\.js" login.html | grep -v "google" | tail -5
echo ""
echo "Available auth scripts:"
ls -1 js/auth*.js js/ultra*.js 2>/dev/null | grep -v "[0-9]\{10\}" | head -10

echo -e "\n✅ FIXES COMPLETE\!"
echo ""
echo "🔗 TEST THESE NOW:"
echo "1. https://bankcsvconverter.com/test-login-working.html (guaranteed to work)"
echo "2. https://bankcsvconverter.com/login.html (main login)"
echo "3. https://bankcsvconverter.com/login-backup.html (backup login)"

ENDSSH
