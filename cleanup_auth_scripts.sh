#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Cleaning up conflicting authentication scripts"
echo "============================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove ALL old auth and stripe scripts from pricing.html
echo "1. Cleaning pricing.html..."
cp pricing.html pricing.html.backup

# Remove all old script tags
sed -i '/<script src="\/js\/debug-auth.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/auth-fixed.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-complete-fix.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-buy-fix.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-integration-fixed.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-simple-fix.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-auth-fix.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/force-auth-storage.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/auth-redirect-fix.js"><\/script>/d' pricing.html

echo "Removed old scripts from pricing.html"

# Clean login.html
echo "2. Cleaning login.html..."
cp login.html login.html.backup

sed -i '/<script src="\/js\/debug-auth.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/auth-fixed.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/auth-login-fix.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/force-auth-storage.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/login-override-final.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/login-redirect-handler.js"><\/script>/d' login.html

echo "Removed old scripts from login.html"

# Clean all other HTML files
echo "3. Cleaning other pages..."
for file in dashboard.html index.html settings.html signup.html; do
    if [ -f "$file" ]; then
        sed -i '/<script src="\/js\/debug-auth.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-fixed.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-global.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-persistent.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-universal.js"><\/script>/d' "$file"
        echo "Cleaned $file"
    fi
done

# Ensure auth-service.js loads FIRST in head
echo "4. Ensuring proper script order..."

# Update pricing.html
cat > fix_pricing_scripts.py << 'PYTHON'
with open('pricing.html', 'r') as f:
    content = f.read()

# Remove existing auth-service and stripe-cookie-auth references
content = content.replace('<script src="/js/auth-service.js"></script>\n', '')
content = content.replace('<script src="/js/stripe-cookie-auth.js"></script>\n', '')

# Find </title> and add our scripts right after
title_end = content.find('</title>')
if title_end != -1:
    insert_pos = content.find('\n', title_end) + 1
    insert_scripts = '''    
    <!-- Cookie-based Authentication (MUST LOAD FIRST) -->
    <script src="/js/auth-service.js"></script>
    <script src="/js/stripe-cookie-auth.js"></script>
'''
    content = content[:insert_pos] + insert_scripts + content[insert_pos:]

with open('pricing.html', 'w') as f:
    f.write(content)
print("Fixed pricing.html script order")
PYTHON

python3 fix_pricing_scripts.py
rm fix_pricing_scripts.py

# Update login.html
cat > fix_login_scripts.py << 'PYTHON'
with open('login.html', 'r') as f:
    content = f.read()

# Remove existing references
content = content.replace('<script src="/js/auth-service.js"></script>\n', '')
content = content.replace('<script src="/js/login-cookie-auth.js"></script>\n', '')

# Add right after </title>
title_end = content.find('</title>')
if title_end != -1:
    insert_pos = content.find('\n', title_end) + 1
    insert_scripts = '''    
    <!-- Cookie-based Authentication (MUST LOAD FIRST) -->
    <script src="/js/auth-service.js"></script>
    <script src="/js/login-cookie-auth.js"></script>
'''
    content = content[:insert_pos] + insert_scripts + content[insert_pos:]

with open('login.html', 'w') as f:
    f.write(content)
print("Fixed login.html script order")
PYTHON

python3 fix_login_scripts.py
rm fix_login_scripts.py

echo "5. Script cleanup complete!"
echo ""
echo "Current scripts in pricing.html:"
grep -E "script.*src.*js\/(auth|stripe)" pricing.html || echo "No auth/stripe scripts found"
echo ""
echo "Current scripts in login.html:"
grep -E "script.*src.*js\/(auth|login)" login.html || echo "No auth/login scripts found"

EOF

echo -e "\n✅ Cleanup complete!"
echo "============================"
echo "Now ONLY using:"
echo "- auth-service.js (cookie auth)"
echo "- stripe-cookie-auth.js (for pricing)"
echo "- login-cookie-auth.js (for login)"
echo ""
echo "Visit https://bankcsvconverter.com/pricing.html"
echo "and check console for [AuthService] messages"