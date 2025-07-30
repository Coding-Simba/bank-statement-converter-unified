#!/bin/bash

# Deployment script for authentication fix
# This script should be run on the server

echo "=== Deploying Authentication Fix ==="
echo "Time: $(date)"

# 1. Backup current files
echo -e "\n1. Creating backups..."
cd /home/ubuntu/bank-statement-converter/frontend
mkdir -p backups/$(date +%Y%m%d)
cp js/stripe-integration.js backups/$(date +%Y%m%d)/stripe-integration-$(date +%H%M%S).js
cp js/auth.js backups/$(date +%Y%m%d)/auth-$(date +%H%M%S).js
echo "✓ Backups created"

# 2. Create the fixed stripe-integration.js
echo -e "\n2. Creating fixed stripe-integration.js..."
cat > js/stripe-integration-fixed.js << 'EOF'
// Stripe Integration - Fixed Version
(function() {
    'use strict';
    
    console.log('[Stripe] Loading...');
    
    // Wait for DOM
    function init() {
        console.log('[Stripe] Initializing...');
        
        // Setup buy buttons
        const buttons = document.querySelectorAll('.pricing-cta.primary');
        const plans = ['starter', 'professional', 'business'];
        
        buttons.forEach((button, index) => {
            const plan = plans[index];
            if (!plan) return;
            
            // Clone to remove old handlers
            const newBtn = button.cloneNode(true);
            button.parentNode.replaceChild(newBtn, button);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('[Stripe] Clicked:', plan);
                
                // Check auth NOW
                const token = localStorage.getItem('access_token');
                if (!token) {
                    console.log('[Stripe] No auth, redirecting...');
                    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                    return;
                }
                
                // Create checkout
                handleCheckout(plan, token, newBtn);
            });
        });
    }
    
    async function handleCheckout(plan, token, button) {
        const originalText = button.textContent;
        button.textContent = 'Processing...';
        button.disabled = true;
        
        try {
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            
            const response = await fetch('https://bankcsvconverter.com/api/stripe/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    plan: plan,
                    billing_period: isYearly ? 'yearly' : 'monthly'
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                throw new Error(data.detail || 'Checkout failed');
            }
        } catch (error) {
            alert('Unable to start checkout: ' + error.message);
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
EOF

# 3. Replace the current version
echo -e "\n3. Deploying fixed version..."
cp js/stripe-integration-fixed.js js/stripe-integration.js
echo "✓ stripe-integration.js updated"

# 4. Check auth.js exports BankAuth
echo -e "\n4. Checking auth.js..."
if grep -q "window.BankAuth" js/auth.js; then
    echo "✓ auth.js exports BankAuth"
else
    echo "⚠ auth.js might not export BankAuth properly"
fi

# 5. Verify pricing.html script order
echo -e "\n5. Checking pricing.html script order..."
tail -20 pricing.html | grep -E "api-config|auth|stripe-integration" || echo "⚠ Scripts might be missing"

# 6. Clear any caches
echo -e "\n6. Clearing caches..."
# Add cache clearing commands if needed

echo -e "\n=== Deployment Complete ==="
echo "Test at: https://bankcsvconverter.com/pricing.html"
echo ""
echo "To verify fix:"
echo "1. Login at /login.html"
echo "2. Go to /pricing.html"
echo "3. Open console and run: localStorage.getItem('access_token')"
echo "4. Click any Buy button - should go to Stripe, not signup"