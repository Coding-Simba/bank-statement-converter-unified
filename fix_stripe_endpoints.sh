#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Stripe endpoint routing"
echo "============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking current Stripe routes..."
echo "==================================="
grep -n "stripe" main.py
echo ""
grep -n "create-checkout-session\|subscription-status" api/stripe_payments.py | head -10

echo -e "\n2. Checking if routes are properly registered..."
echo "=============================================="
python3 -c "
import sys
sys.path.append('.')
from main import app
print('Registered routes:')
for route in app.routes:
    if hasattr(route, 'path'):
        print(f'  {route.path}')
" | grep -E "stripe|checkout|subscription" || echo "No stripe routes found in app"

echo -e "\n3. Fixing route registration..."
echo "==============================="
# Check how stripe router is imported and included
grep -A5 -B5 "stripe_router\|stripe_payments" main.py

echo -e "\n4. Testing Stripe endpoints directly..."
echo "====================================="
# Start backend if not running
if ! pgrep -f "uvicorn main:app" > /dev/null; then
    echo "Starting backend..."
    source venv/bin/activate
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_test.log 2>&1 &
    sleep 5
fi

# Test the endpoints
echo "Testing checkout endpoint variations:"
for endpoint in "/create-checkout-session" "/api/create-checkout-session" "/v2/api/create-checkout-session" "/stripe/create-checkout-session"; do
    echo -n "  $endpoint: "
    STATUS=$(curl -s -X POST http://localhost:5000$endpoint \
        -H "Content-Type: application/json" \
        -d '{"price_id":"test"}' \
        -w "%{http_code}" -o /dev/null)
    echo "HTTP $STATUS"
done

echo -e "\nTesting subscription status variations:"
for endpoint in "/subscription-status" "/api/subscription-status" "/v2/api/subscription-status" "/stripe/subscription-status"; do
    echo -n "  $endpoint: "
    STATUS=$(curl -s http://localhost:5000$endpoint -w "%{http_code}" -o /dev/null)
    echo "HTTP $STATUS"
done

echo -e "\n5. Checking the actual Stripe implementation..."
echo "============================================="
# Show the actual endpoints defined
head -50 api/stripe_payments.py | grep -E "@router|def |async def"

echo -e "\n6. Let's check router prefix in main.py..."
echo "========================================"
grep -C3 "include_router.*stripe" main.py

echo -e "\n7. Final test with correct paths..."
echo "=================================="
# Based on the findings, test the actual endpoints
echo "Testing with authentication:"

# First get a CSRF token and create a test user
CSRF_TOKEN=$(curl -s http://localhost:5000/v2/api/auth/csrf | python3 -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null || echo "")
if [ -n "$CSRF_TOKEN" ]; then
    # Create test user
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="stripetest${TIMESTAMP}@example.com"
    
    REG_RESPONSE=$(curl -s -X POST http://localhost:5000/v2/api/auth/register \
        -c stripe_test_cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $CSRF_TOKEN" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Stripe Test\"}")
    
    if echo "$REG_RESPONSE" | grep -q "\"id\""; then
        echo "Test user created"
        
        # Now test Stripe endpoints with auth
        echo -e "\nTesting /api/stripe/create-checkout-session:"
        curl -s -X POST http://localhost:5000/api/stripe/create-checkout-session \
            -b stripe_test_cookies.txt \
            -H "Content-Type: application/json" \
            -H "X-CSRF-Token: $CSRF_TOKEN" \
            -d '{"price_id":"price_test","success_url":"http://localhost/success","cancel_url":"http://localhost/cancel"}' \
            | python3 -m json.tool 2>/dev/null | head -20 || echo "Failed"
        
        echo -e "\nTesting /api/stripe/subscription-status:"
        curl -s http://localhost:5000/api/stripe/subscription-status \
            -b stripe_test_cookies.txt \
            | python3 -m json.tool 2>/dev/null || echo "Failed"
    fi
    
    rm -f stripe_test_cookies.txt
fi

EOF

echo -e "\n✅ Stripe endpoint investigation complete!"