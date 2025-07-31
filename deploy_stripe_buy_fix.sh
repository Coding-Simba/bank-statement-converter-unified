#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Stripe Buy Fix"
echo "========================"

# Deploy the stripe-buy-fix.js
echo "1. Deploying stripe-buy-fix.js..."
scp -i "$KEY_PATH" js/stripe-buy-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing.html to include the script
echo "2. Updating pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add stripe-buy-fix.js to pricing page if not already there
if ! grep -q "stripe-buy-fix.js" pricing.html; then
    # Add it after stripe-complete-fix.js
    sed -i '/stripe-complete-fix.js/a\    <script src="/js/stripe-buy-fix.js"></script>' pricing.html
    echo "Added stripe-buy-fix.js to pricing.html"
else
    echo "stripe-buy-fix.js already in pricing.html"
fi

# Show the current scripts loaded
echo -e "\nCurrent scripts in pricing.html:"
grep -E "(auth|stripe)" pricing.html | grep script
EOF

echo -e "\n✅ Stripe Buy Fix deployed!"
echo "=========================="
echo "This fix:"
echo "1. Directly attaches onclick handlers without cloning buttons"
echo "2. Runs after page load with 1 second delay"
echo "3. Checks auth and redirects to login if needed"
echo "4. Calls Stripe API with proper headers"
echo ""
echo "Test by visiting https://bankcsvconverter.com/pricing.html"