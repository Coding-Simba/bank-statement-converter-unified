#\!/bin/bash

# Server details
SERVER="ubuntu@3.235.19.83"
KEY_PATH="/Users/MAC/Desktop/bank-statement-converter.pem"

echo "Final deployment of Stripe integration..."

# Copy files to home directory first
echo "1. Copying files to server..."
scp -i "$KEY_PATH" js/stripe-integration.js "$SERVER:/home/ubuntu/"
scp -i "$KEY_PATH" js/dashboard.js "$SERVER:/home/ubuntu/"
scp -i "$KEY_PATH" pricing.html "$SERVER:/home/ubuntu/"
scp -i "$KEY_PATH" dashboard.html "$SERVER:/home/ubuntu/"

ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
# Find the correct web root
echo "2. Finding web root..."
WEB_ROOT=$(sudo find /var/www -name "index.html" -type f 2>/dev/null | head -1 | xargs dirname)
echo "Web root found: $WEB_ROOT"

# Copy files to web root
echo "3. Copying files to web root..."
sudo cp /home/ubuntu/stripe-integration.js "$WEB_ROOT/js/" && echo "✓ stripe-integration.js copied"
sudo cp /home/ubuntu/dashboard.js "$WEB_ROOT/js/" && echo "✓ dashboard.js copied"
sudo cp /home/ubuntu/pricing.html "$WEB_ROOT/" && echo "✓ pricing.html copied"
sudo cp /home/ubuntu/dashboard.html "$WEB_ROOT/" && echo "✓ dashboard.html copied"

# Clean up
rm -f /home/ubuntu/stripe-integration.js
rm -f /home/ubuntu/dashboard.js
rm -f /home/ubuntu/pricing.html
rm -f /home/ubuntu/dashboard.html

# Restart backend service
echo "4. Restarting backend service..."
sudo systemctl restart bankconverter.service

# Check status
echo "5. Checking service status..."
sudo systemctl status bankconverter.service --no-pager

# Test the API
echo "6. Testing API..."
curl -s http://localhost:5000/health | jq '.' || echo "API health check failed"

echo "Deployment complete\!"
echo ""
echo "Next steps:"
echo "1. Visit https://bankcsvconverter.com/pricing.html"
echo "2. Test the payment flow"
echo "3. Check webhook deliveries in Stripe Dashboard"
ENDSSH
