#!/bin/bash

# Deploy cross-tab authentication test files to production
# Run this from the project root directory

echo "🚀 Deploying cross-tab authentication test files..."

# Server details
SERVER="ubuntu@3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
REMOTE_PATH="/var/www/html"

# Files to deploy
FILES=(
    "cross_tab_auth_test.html"
    "test_cross_tab_auth_sync.js"
)

echo "📁 Files to deploy:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        exit 1
    fi
done

echo ""
echo "🔗 Copying files to server..."

# Copy files to server
for file in "${FILES[@]}"; do
    echo "Uploading $file..."
    scp -i "$KEY_PATH" "$file" "$SERVER:$REMOTE_PATH/"
    if [ $? -eq 0 ]; then
        echo "  ✅ $file uploaded successfully"
    else
        echo "  ❌ Failed to upload $file"
        exit 1
    fi
done

echo ""
echo "🔧 Setting proper permissions..."
ssh -i "$KEY_PATH" "$SERVER" "chmod 644 $REMOTE_PATH/cross_tab_auth_test.html $REMOTE_PATH/test_cross_tab_auth_sync.js"

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Test URLs:"
echo "  Main Test Page: https://bankcsvconverter.com/cross_tab_auth_test.html"
echo "  Legacy Test Page: https://bankcsvconverter.com/test_cross_tab_logout.html"
echo ""
echo "📋 Testing Instructions:"
echo "1. Open https://bankcsvconverter.com/cross_tab_auth_test.html"
echo "2. Run automated test suite"
echo "3. Open multiple tabs with different pages"
echo "4. Login in one tab, verify sync in others"
echo "5. Logout in any tab, verify all tabs sync"
echo ""
echo "⏱️  Expected Results:"
echo "  - BroadcastChannel sync: < 100ms"
echo "  - localStorage event sync: < 500ms"
echo "  - Overall sync reliability: > 95%"