#!/bin/bash

echo "Testing all fixes on bankcsvconverter.com"
echo "========================================="

# Test 1: Check if auth API is working
echo -e "\n1. Testing Auth API:"
curl -s -X POST https://bankcsvconverter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | jq '.access_token' | head -c 50
echo "..."

# Test 2: Check if stripe-integration.js loads
echo -e "\n\n2. Testing Stripe Integration Script:"
curl -s "https://bankcsvconverter.com/js/stripe-integration.js?v=5" | grep -o "User authenticated at click time" | head -1

# Test 3: Check if navigation scripts are in place
echo -e "\n\n3. Testing Navigation Scripts:"
curl -s https://bankcsvconverter.com/index.html | grep -o "nav-links-fix.js" | head -1

# Test 4: Check pricing page scripts
echo -e "\n\n4. Testing Pricing Page:"
curl -s https://bankcsvconverter.com/pricing.html | grep -E "stripe-integration.js\?v=5|auth.js|api-config.js" | wc -l

echo -e "\n\nAll tests completed. Expected results:"
echo "1. Should show JWT token"
echo "2. Should show 'User authenticated at click time'"
echo "3. Should show 'nav-links-fix.js'"
echo "4. Should show 3 (all required scripts)"