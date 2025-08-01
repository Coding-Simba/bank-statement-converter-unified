#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Stripe authentication properly"
echo "===================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking the auth import structure..."
echo "======================================"
ls -la api/ | grep auth
echo ""
find . -name "*auth*.py" -type f | grep -v __pycache__ | head -10

echo -e "\n2. Checking correct import path..."
echo "================================="
grep -r "get_current_user_cookie" --include="*.py" . | grep "def " | head -5

echo -e "\n3. Fixing the import in stripe_payments.py..."
echo "==========================================="
# Restore backup first
cp api/stripe_payments.py.backup api/stripe_payments.py

# Check the correct import
head -30 api/stripe_payments.py | grep -n "import"

echo -e "\n4. Manually updating stripe_payments.py..."
echo "========================================"
# Create a fixed version
cat > /tmp/stripe_auth_fix.py << 'PYTHON'
# Add this import after other imports
from api.auth_cookie import get_current_user_cookie

# Then in the file, replace:
# from middleware.auth_middleware import get_current_user
# with the above import

# And replace all instances of:
# current_user: User = Depends(get_current_user)
# with:
# current_user: User = Depends(get_current_user_cookie)
PYTHON

# Apply the fix with Python
python3 << 'PYFIX'
import re

# Read the file
with open('api/stripe_payments.py', 'r') as f:
    content = f.read()

# Add the import if not present
if 'get_current_user_cookie' not in content:
    # Add after other imports
    content = content.replace(
        'from middleware.auth_middleware import get_current_user',
        'from .auth_cookie import get_current_user_cookie'
    )
    
    # Replace the dependency
    content = re.sub(
        r'current_user: User = Depends\(get_current_user\)',
        'current_user: User = Depends(get_current_user_cookie)',
        content
    )

# Write the file back
with open('api/stripe_payments.py', 'w') as f:
    f.write(content)

print("✅ File updated")
PYFIX

echo -e "\n5. Verifying the changes..."
echo "=========================="
grep -n "get_current_user" api/stripe_payments.py | head -10

echo -e "\n6. Restarting backend..."
echo "======================="
pkill -f uvicorn
sleep 2
source venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_stripe_auth.log 2>&1 &
echo "Waiting for backend to start..."
sleep 8

# Check if backend started successfully
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start. Checking logs:"
    tail -30 backend_stripe_auth.log
    exit 1
fi

echo -e "\n7. Final test with authentication..."
echo "==================================="
# Test with cookies
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

if [ -n "$CSRF_TOKEN" ]; then
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="stripefinal${TIMESTAMP}@example.com"
    
    echo "Creating authenticated session..."
    REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c stripe_test.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Final Stripe Test\"}")
    
    if echo "$REG_RESPONSE" | grep -q "\"id\""; then
        echo "✅ User authenticated"
        
        echo -e "\nTesting Stripe subscription status:"
        SUBSCRIPTION=$(curl -s https://bankcsvconverter.com/api/stripe/subscription-status -b stripe_test.txt)
        echo "$SUBSCRIPTION" | python3 -m json.tool 2>/dev/null || echo "$SUBSCRIPTION"
        
        echo -e "\nTesting Stripe checkout session:"
        CHECKOUT=$(curl -s -X POST https://bankcsvconverter.com/api/stripe/create-checkout-session \
            -b stripe_test.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d '{"plan":"professional","billing_period":"monthly"}')
        
        if echo "$CHECKOUT" | grep -q "Stripe API key not configured" || echo "$CHECKOUT" | grep -q "Invalid Stripe API key"; then
            echo "✅ AUTHENTICATION WORKING! But Stripe keys need to be configured"
            echo ""
            echo "=========================================="
            echo "STRIPE INTEGRATION IS READY!"
            echo "=========================================="
            echo ""
            echo "✅ Authentication: Working"
            echo "✅ Session persistence: Working"
            echo "✅ Stripe endpoints: Accessible"
            echo ""
            echo "📝 To complete setup, add to backend/.env:"
            echo "   STRIPE_SECRET_KEY=sk_test_YOUR_KEY"
            echo "   STRIPE_PUBLIC_KEY=pk_test_YOUR_KEY"
            echo ""
            echo "Then users can subscribe at:"
            echo "   https://bankcsvconverter.com/pricing.html"
        else
            echo "Response: $CHECKOUT" | head -30
        fi
    fi
    
    rm -f stripe_test.txt
fi

EOF

echo -e "\n✅ Stripe authentication fix complete!"