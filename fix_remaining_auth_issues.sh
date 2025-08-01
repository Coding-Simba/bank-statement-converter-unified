#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing remaining authentication issues"
echo "====================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

echo "1. Fixing login.html - removing old auth.js comment..."
sed -i 's|// The auth.js module will handle all login functionality|// The auth-unified.js module will handle all login functionality|g' login.html
sed -i 's|// auth.js automatically sets up OAuth buttons|// auth-unified.js automatically sets up OAuth buttons|g' login.html

echo "2. Fixing signup.html - removing old auth.js comment..."
sed -i 's|// The auth.js module will handle all signup functionality|// The auth-unified.js module will handle all signup functionality|g' signup.html
sed -i 's|// OAuth buttons and form submission are automatically set up by auth.js|// OAuth buttons and form submission are automatically set up by auth-unified.js|g' signup.html

echo "3. Removing temp_signup.html..."
rm -f temp_signup.html

echo "4. Fixing test-auth.html..."
sed -i 's|<script src="/js/auth-persistent.js"></script>||g' test-auth.html

echo "5. Adding auth-unified.js to all blog posts..."
for blog_file in blog/*.html; do
    if [ -f "$blog_file" ]; then
        # Check if auth-unified.js is already present
        if ! grep -q "auth-unified.js" "$blog_file"; then
            # Add auth-unified.js after </title>
            sed -i '/<\/title>/a\    <script src="/js/auth-unified.js"></script>' "$blog_file"
            echo "Added auth-unified.js to $blog_file"
        fi
    fi
done

echo -e "\n6. Final verification of critical pages..."
echo "==========================================="

echo -e "\nlogin.html:"
grep -E "auth.*\.js" login.html || echo "✅ No old auth scripts"

echo -e "\nsignup.html:"
grep -E "auth.*\.js" signup.html || echo "✅ No old auth scripts"

echo -e "\npricing.html:"
grep -E "auth.*\.js" pricing.html || echo "✅ No old auth scripts"

echo -e "\ndashboard.html:"
grep -E "auth.*\.js" dashboard.html || echo "✅ No old auth scripts"

echo -e "\nindex.html:"
grep -E "auth.*\.js" index.html || echo "✅ No old auth scripts"

echo -e "\n7. Checking blog posts have auth-unified.js..."
echo "============================================="
blog_count=$(find blog -name "*.html" | wc -l)
auth_count=$(grep -l "auth-unified.js" blog/*.html 2>/dev/null | wc -l)
echo "Total blog posts: $blog_count"
echo "Posts with auth-unified.js: $auth_count"

if [ "$blog_count" -eq "$auth_count" ]; then
    echo "✅ All blog posts have auth-unified.js"
else
    echo "⚠️  Some blog posts still missing auth-unified.js"
fi

EOF

echo -e "\n✅ Authentication fixes complete!"