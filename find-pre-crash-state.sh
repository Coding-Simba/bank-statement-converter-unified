#\!/bin/bash

# Find Pre-Crash State
echo "🔍 Finding the actual state before server crash"
echo "=============================================="
echo ""

# Check local git history
echo "1. Checking git history for commits before the crash..."
git log --oneline --since="2025-07-30" --until="2025-08-01" | head -20

echo -e "\n2. Looking for the auth files from before today's changes..."
# The crash happened today (Aug 1), so we need files from before that
git log --oneline --before="2025-08-01" --grep="auth\|Auth" | head -10

echo -e "\n3. Checking what auth files existed before the crash..."
# Show the state of js directory before today
git ls-tree HEAD~20 js/ | grep -E "auth|Auth" | head -10

echo -e "\n4. Let's get the exact commit before the server issues started..."
# Based on CLAUDE.md, the last working state mentioned was with auth-fixed.js
LAST_GOOD_COMMIT=$(git log --oneline --before="2025-08-01 12:00" -n 1 | awk '{print $1}')
echo "Last commit before issues: $LAST_GOOD_COMMIT"

if [ \! -z "$LAST_GOOD_COMMIT" ]; then
    echo -e "\n5. Files in that commit:"
    git show --name-only $LAST_GOOD_COMMIT | head -20
fi

# Deploy the restoration
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

echo -e "\n6. Restoring files on server from before the crash..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << ENDSSH
cd /home/ubuntu/bank-statement-converter

echo "Checking for the original frontend backup..."
# The frontend directory mentioned in earlier errors
if [ -d /home/ubuntu/bank-statement-converter/frontend ]; then
    echo "Found frontend directory with original files\!"
    
    # Check what auth files are in the frontend backup
    ls -la frontend/js/auth* 2>/dev/null | head -10
    
    # Copy the original auth files
    if [ -f frontend/js/auth.js ]; then
        cp frontend/js/auth.js js/auth.js
        echo "✅ Restored original auth.js"
    fi
    
    if [ -f frontend/js/auth-unified.js ]; then
        cp frontend/js/auth-unified.js js/auth-unified.js
        echo "✅ Restored original auth-unified.js"
    fi
    
    # Check for original HTML files
    for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
        if [ -f "frontend/\$file" ]; then
            cp "frontend/\$file" "\$file"
            echo "✅ Restored \$file from frontend backup"
        fi
    done
fi

echo -e "\nChecking auth-fixed.js from the old backup..."
if [ -f /home/ubuntu/bank-statement-converter/frontend/js/old-auth-backup/auth-fixed.js ]; then
    echo "Found auth-fixed.js in old backup\!"
    cp /home/ubuntu/bank-statement-converter/frontend/js/old-auth-backup/auth-fixed.js js/auth-fixed.js
    
    # Update HTML files to use auth-fixed.js as mentioned in CLAUDE.md
    for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
        if [ -f "\$file" ]; then
            # Remove any auth script references added today
            sed -i '/auth-unified-[0-9]*.js/d' "\$file"
            sed -i '/auth-simple.js/d' "\$file"
            sed -i '/auth-working.js/d' "\$file"
            
            # Use auth-fixed.js as it was the working version
            if \! grep -q "auth-fixed.js" "\$file"; then
                sed -i "/<\/body>/i <script src=\"/js/auth-fixed.js\"></script>" "\$file"
            fi
        fi
    done
    echo "✅ Updated all HTML files to use auth-fixed.js"
fi

echo -e "\n✅ Restoration complete\!"

ENDSSH

echo -e "\n7. Showing the current auth setup on server..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH2'
cd /home/ubuntu/bank-statement-converter
echo "Current auth files:"
ls -la js/auth*.js | grep -v "auth-unified-[0-9]" | head -5
echo -e "\nAuth script references in HTML:"
grep -h "auth.*\.js" login.html | head -3
ENDSSH2

