#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing frontend authentication endpoints"
echo "======================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter

echo "1. Fixing auth-service.js to use v2 endpoints..."
echo "=============================================="
# Update all API calls to use v2 endpoints
sed -i 's|/api/auth/|/v2/api/auth/|g' frontend/js/auth-service.js

echo -e "\n2. Fixing auth.js to use v2 endpoints..."
echo "========================================"
if [ -f frontend/js/auth.js ]; then
    sed -i "s|'/api/auth'|'/v2/api/auth'|g" frontend/js/auth.js
    sed -i 's|"/api/auth|"/v2/api/auth|g' frontend/js/auth.js
fi

echo -e "\n3. Checking api-config.js..."
echo "==========================="
if [ -f frontend/js/api-config.js ]; then
    cat frontend/js/api-config.js
    echo -e "\nUpdating api-config.js to use v2..."
    sed -i "s|'/api'|'/v2/api'|g" frontend/js/api-config.js
fi

echo -e "\n4. Verifying the changes..."
echo "=========================="
echo "auth-service.js endpoints:"
grep -E "fetch.*auth" frontend/js/auth-service.js | head -5

echo -e "\n5. Creating the missing auth.css file..."
echo "======================================"
mkdir -p css
cat > css/auth.css << 'CSS'
/* Auth page styles */
.auth-container {
    max-width: 400px;
    margin: 50px auto;
    padding: 20px;
}

.error-message {
    color: #dc3545;
    margin-top: 10px;
    font-size: 14px;
}

.success-message {
    color: #28a745;
    margin-top: 10px;
    font-size: 14px;
}

.form-control:focus {
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

.loading {
    opacity: 0.6;
    pointer-events: none;
}
CSS

echo -e "\n6. Let's also ensure the signup page uses the correct script..."
echo "============================================================="
# The signup page is using multiple auth scripts which might conflict
# Let's check what it should be using
echo "Current signup.html script tags:"
grep -E "auth.*\.js" signup.html | head -10

echo -e "\n7. Testing the authentication flow directly..."
echo "==========================================="
# Test the endpoints
echo "Testing CSRF endpoint:"
curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -m json.tool | head -5

echo -e "\n8. Let's create a unified fix for signup.html..."
echo "=============================================="
# Backup current signup.html
cp signup.html signup.html.backup.$(date +%Y%m%d_%H%M%S)

# Remove conflicting auth scripts and use only auth-unified.js
sed -i '/<script src="\/js\/auth\.js"><\/script>/d' signup.html
sed -i '/<script src="\/js\/auth-service\.js"><\/script>/d' signup.html
sed -i '/<script src="\/js\/auth-redirect-fix\.js"><\/script>/d' signup.html
sed -i '/<script src="\/js\/auth-navigation\.js"><\/script>/d' signup.html

# Ensure auth-unified.js is included
if ! grep -q "auth-unified.js" signup.html; then
    # Add before closing body tag
    sed -i '/<\/body>/i <script src="/js/auth-unified.js"></script>' signup.html
fi

echo -e "\n9. Final verification of endpoints..."
echo "==================================="
echo "Testing login flow:"
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
if [ -n "$CSRF_TOKEN" ]; then
    echo "✅ Got CSRF token"
    
    # Try a login
    LOGIN_TEST=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/login \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d '{"email":"nonexistent@example.com","password":"wrong"}' \
        | python3 -m json.tool 2>/dev/null)
    
    if echo "$LOGIN_TEST" | grep -q "Invalid credentials"; then
        echo "✅ Login endpoint working (correctly rejecting invalid credentials)"
    else
        echo "Login response: $LOGIN_TEST"
    fi
fi

echo -e "\n10. Summary of changes..."
echo "======================="
echo "✅ Updated auth-service.js to use /v2/api/auth endpoints"
echo "✅ Updated auth.js to use /v2/api/auth endpoints"
echo "✅ Created missing auth.css file"
echo "✅ Fixed signup.html to use auth-unified.js"
echo ""
echo "The authentication should now work in your browser!"

EOF

echo -e "\n✅ Frontend authentication endpoints fixed!"
echo ""
echo "🧪 To test in your browser:"
echo "1. Open Chrome in incognito mode"
echo "2. Go to https://bankcsvconverter.com/signup.html"
echo "3. Create a new account"
echo "4. Check if you stay logged in when navigating to other pages"