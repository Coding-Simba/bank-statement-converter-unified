#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Debugging Stripe routing issue"
echo "============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking if stripe_payments.py has double prefix..."
echo "==================================================="
head -30 api/stripe_payments.py | grep -E "router|prefix|APIRouter"

echo -e "\n2. The issue: Double prefix!"
echo "============================"
echo "The router already has prefix='/api/stripe' in stripe_payments.py"
echo "And we're adding another prefix in main.py"
echo "Result: /api/stripe/api/stripe/create-checkout-session"

echo -e "\n3. Fixing the double prefix issue..."
echo "==================================="
# Remove the prefix from main.py since it's already in the router
sed -i 's/app.include_router(stripe_router, prefix="\/api\/stripe", tags=\["stripe"\])/app.include_router(stripe_router)/' main.py

echo -e "\n4. Verifying the fix..."
echo "======================"
grep "stripe_router" main.py

echo -e "\n5. Restarting backend..."
echo "======================="
pkill -f uvicorn
sleep 2
source venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_final.log 2>&1 &
sleep 5

echo -e "\n6. Testing the correct endpoints..."
echo "================================="
# Test locally first
echo "Local test - subscription status:"
curl -s http://localhost:5000/api/stripe/subscription-status | python3 -m json.tool 2>/dev/null | head -10

echo -e "\n7. Full test with authentication..."
echo "================================="
# Get CSRF token
CSRF_TOKEN=$(curl -s https://bankcsvconverter.com/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)

if [ -n "$CSRF_TOKEN" ]; then
    # Create test user
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="stripefinal${TIMESTAMP}@example.com"
    
    echo "Creating test user: $TEST_EMAIL"
    REG_RESPONSE=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
        -c final_cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Stripe Final Test\"}")
    
    if echo "$REG_RESPONSE" | grep -q "\"id\""; then
        echo "✅ User created"
        
        echo -e "\nTesting subscription status:"
        SUBSCRIPTION=$(curl -s https://bankcsvconverter.com/api/stripe/subscription-status -b final_cookies.txt)
        if echo "$SUBSCRIPTION" | grep -q "status"; then
            echo "✅ Subscription endpoint working!"
            echo "$SUBSCRIPTION" | python3 -m json.tool
        else
            echo "❌ Subscription endpoint failed"
            echo "$SUBSCRIPTION"
        fi
        
        echo -e "\nTesting checkout session creation:"
        CHECKOUT=$(curl -s -X POST https://bankcsvconverter.com/api/stripe/create-checkout-session \
            -b final_cookies.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d '{"plan":"professional","billing_period":"monthly"}')
        
        if echo "$CHECKOUT" | grep -q "detail"; then
            echo "Response: $CHECKOUT"
            if echo "$CHECKOUT" | grep -q "Stripe API key"; then
                echo "⚠️  Stripe API keys not configured"
                echo ""
                echo "NEXT STEP: Add Stripe API keys to .env file:"
                echo "  STRIPE_SECRET_KEY=sk_test_..."
                echo "  STRIPE_PUBLIC_KEY=pk_test_..."
            fi
        else
            echo "✅ Checkout endpoint working!"
            echo "$CHECKOUT" | python3 -m json.tool | head -20
        fi
    fi
    
    rm -f final_cookies.txt
fi

echo -e "\n8. Summary of Stripe endpoints..."
echo "================================"
echo "✅ Available Stripe endpoints:"
echo "  POST /api/stripe/create-checkout-session"
echo "  GET  /api/stripe/subscription-status"
echo "  POST /api/stripe/webhook"
echo ""
echo "📍 Access them at:"
echo "  https://bankcsvconverter.com/api/stripe/create-checkout-session"
echo "  https://bankcsvconverter.com/api/stripe/subscription-status"

EOF

echo -e "\n✅ Stripe routing investigation complete!"