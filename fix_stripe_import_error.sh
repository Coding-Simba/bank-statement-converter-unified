#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Stripe import error"
echo "========================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Fixing the import error in main.py..."
echo "======================================"
# Remove the incorrect import/router line
sed -i '/stripe_routes\.router/d' main.py

echo -e "\n2. Checking stripe_router configuration..."
echo "========================================"
grep -n "stripe_router" main.py

echo -e "\n3. Looking at the stripe_payments.py router setup..."
echo "=================================================="
grep -B5 -A5 "router = " api/stripe_payments.py | head -20

echo -e "\n4. Checking if stripe_router has a prefix..."
echo "=========================================="
grep -B2 -A2 "include_router(stripe_router" main.py

echo -e "\n5. Adding proper prefix to stripe_router..."
echo "========================================="
# Update the stripe router to have a prefix
sed -i 's/app.include_router(stripe_router)/app.include_router(stripe_router, prefix="\/api\/stripe", tags=["stripe"])/' main.py

echo -e "\n6. Verifying the changes..."
echo "=========================="
grep "stripe_router" main.py

echo -e "\n7. Restarting backend..."
echo "======================="
pkill -f uvicorn
sleep 2
source venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_stripe_fix.log 2>&1 &
sleep 5

echo -e "\n8. Testing the corrected endpoints..."
echo "==================================="
# Check if backend is running
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "Backend is running"
    
    # Test endpoints
    echo -e "\nTesting /api/stripe/create-checkout-session:"
    curl -sI http://localhost:5000/api/stripe/create-checkout-session | head -3
    
    echo -e "\nTesting /api/stripe/subscription-status:"
    curl -sI http://localhost:5000/api/stripe/subscription-status | head -3
    
    # Test through public URL
    echo -e "\nTesting through public URL:"
    curl -s https://bankcsvconverter.com/api/stripe/subscription-status | head -20
else
    echo "Backend failed to start. Checking logs:"
    tail -20 backend_stripe_fix.log
fi

echo -e "\n9. Creating a complete test with authentication..."
echo "==============================================="
# Get CSRF and test with auth
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
if [ -n "$CSRF_TOKEN" ]; then
    echo "Got CSRF token"
    
    # Create test user
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="stripefix${TIMESTAMP}@example.com"
    
    REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c stripe_cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Stripe Fix Test\"}")
    
    if echo "$REG_RESPONSE" | grep -q "\"id\""; then
        echo "Test user created"
        
        echo -e "\nTesting Stripe subscription status:"
        SUBSCRIPTION=$(curl -s https://bankcsvconverter.com/api/stripe/subscription-status -b stripe_cookies.txt)
        echo "$SUBSCRIPTION" | python3 -m json.tool 2>/dev/null || echo "$SUBSCRIPTION"
        
        echo -e "\nTesting Stripe checkout (will fail without valid price_id):"
        CHECKOUT=$(curl -s -X POST https://bankcsvconverter.com/api/stripe/create-checkout-session \
            -b stripe_cookies.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d '{"price_id":"price_test","success_url":"https://bankcsvconverter.com/success","cancel_url":"https://bankcsvconverter.com/pricing"}')
        echo "$CHECKOUT" | python3 -m json.tool 2>/dev/null | head -20 || echo "$CHECKOUT" | head -20
    fi
    
    rm -f stripe_cookies.txt
fi

EOF

echo -e "\n✅ Stripe import error fixed!"