#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Checking all pages for authentication issues"
echo "==========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

echo "1. Finding all HTML files..."
echo "============================"
find . -name "*.html" -type f | sort

echo -e "\n2. Checking for old auth scripts in each HTML file..."
echo "=================================================="

# List of old auth scripts to check for
OLD_SCRIPTS=(
    "auth.js"
    "auth-fixed.js"
    "auth-persistent.js"
    "auth-universal.js"
    "auth-global.js"
    "debug-auth.js"
    "auth-login-fix.js"
    "auth-redirect-fix.js"
    "force-auth-storage.js"
    "login-override-final.js"
    "login-redirect-handler.js"
    "auth-service.js"
    "login-cookie-auth.js"
    "stripe-cookie-auth.js"
    "stripe-complete-fix.js"
    "stripe-buy-fix.js"
    "stripe-integration-fixed.js"
    "stripe-simple-fix.js"
    "stripe-auth-fix.js"
    "simple_stripe_handler.js"
)

# Check each HTML file
for html_file in $(find . -name "*.html" -type f | sort); do
    echo -e "\nChecking: $html_file"
    echo "-------------------"
    
    # Check for auth-unified.js
    if grep -q "auth-unified.js" "$html_file"; then
        echo "✅ Uses auth-unified.js"
    else
        echo "❌ Missing auth-unified.js"
    fi
    
    # Check for old scripts
    found_old=false
    for old_script in "${OLD_SCRIPTS[@]}"; do
        if grep -q "$old_script" "$html_file"; then
            echo "⚠️  Found old script: $old_script"
            found_old=true
        fi
    done
    
    if [ "$found_old" = false ]; then
        echo "✅ No old auth scripts found"
    fi
done

echo -e "\n3. Listing pages that need fixing..."
echo "===================================="

# Find pages missing auth-unified.js
echo "Pages missing auth-unified.js:"
for html_file in $(find . -name "*.html" -type f); do
    if ! grep -q "auth-unified.js" "$html_file"; then
        echo "- $html_file"
    fi
done

echo -e "\nPages with old auth scripts:"
for html_file in $(find . -name "*.html" -type f); do
    for old_script in "${OLD_SCRIPTS[@]}"; do
        if grep -q "$old_script" "$html_file"; then
            echo "- $html_file (has $old_script)"
            break
        fi
    done
done

EOF