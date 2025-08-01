#!/bin/bash

# Debug Stripe Checkout
echo "🔍 Debugging Stripe Checkout Issue"
echo "=================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking if Stripe endpoints exist in backend..."
cd /home/ubuntu/backend
grep -r "stripe\|checkout" . --include="*.py" | grep -E "(router|@app|endpoint)" | head -20

echo -e "\n2. Looking for Stripe API configuration..."
grep -r "stripe" . --include="*.py" | grep -E "(api_key|secret|STRIPE)" | head -10

echo -e "\n3. Checking environment variables for Stripe..."
if [ -f .env ]; then
    grep -i stripe .env | sed 's/=.*/=***HIDDEN***/'
else
    echo "No .env file found"
fi

echo -e "\n4. Checking available API endpoints..."
curl -s http://localhost:5000/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Stripe/Payment related endpoints:')
for path in data.get('paths', {}):
    if any(word in path.lower() for word in ['stripe', 'checkout', 'payment', 'subscription']):
        methods = list(data['paths'][path].keys())
        print(f'  {methods} {path}')
" 2>/dev/null || echo "Could not parse OpenAPI spec"

echo -e "\n5. Checking pricing page for Stripe integration..."
cd /home/ubuntu/bank-statement-converter
echo "Stripe references in pricing.html:"
grep -E "stripe|checkout|payment" pricing.html | grep -v "<!--" | head -10

echo -e "\n6. Looking for Stripe JavaScript..."
find . -name "*.js" -type f -exec grep -l "stripe\|Stripe" {} \; | grep -v node_modules | head -10

echo -e "\n7. Checking recent backend logs for Stripe errors..."
cd /home/ubuntu/backend
tail -100 backend_clean.log 2>/dev/null | grep -E "(stripe|Stripe|checkout|payment)" | tail -10

echo -e "\n8. Testing if Stripe checkout endpoint exists..."
# Common Stripe endpoints
for endpoint in "/api/create-checkout-session" "/api/stripe/checkout" "/api/checkout" "/api/payment/checkout"; do
    echo -n "Testing $endpoint: "
    curl -X POST http://localhost:5000$endpoint \
      -H "Content-Type: application/json" \
      -d '{"test": true}' \
      -w "Status: %{http_code}\n" -s -o /dev/null
done

echo -e "\n9. Checking nginx access logs for checkout attempts..."
sudo tail -50 /var/log/nginx/access.log | grep -E "(checkout|stripe|payment)" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"