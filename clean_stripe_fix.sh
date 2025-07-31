#!/bin/bash

# Clean up conflicting scripts and deploy a single working solution

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Cleaning up Stripe implementation"
echo "================================="

# Create a clean pricing.html with minimal scripts
echo "1. Creating clean pricing page..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove ALL stripe-related scripts except the simple fix
sed -i '/<script src="\/js\/stripe-integration\.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-integration-fixed\.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/stripe-auth-fix\.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/auth\.js"><\/script>/d' pricing.html

# Make sure only essential scripts remain
echo "Cleaned pricing.html of conflicting scripts"
EOF

# Deploy a final, simplified stripe handler
echo "2. Creating final stripe handler..."
cat > /tmp/stripe-final.js << 'SCRIPT'
// Final Stripe Integration - Clean and Simple
(function() {
    console.log('[Stripe Final] Initializing clean implementation...');
    
    // Store original fetch
    const originalFetch = window.fetch;
    window.fetch = originalFetch;
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
    function setupStripeButtons() {
        const buttons = document.querySelectorAll('.pricing-cta.primary');
        console.log('[Stripe Final] Found buttons:', buttons.length);
        
        buttons.forEach((button, index) => {
            if (!button.textContent.includes('Buy')) return;
            
            const plans = ['starter', 'professional', 'business'];
            const plan = plans[index];
            if (!plan) return;
            
            // Clone to remove ALL existing handlers
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            newButton.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                console.log('[Stripe Final] Buy clicked:', plan);
                
                const token = localStorage.getItem('access_token');
                if (!token) {
                    console.log('[Stripe Final] No token, redirecting to login...');
                    sessionStorage.setItem('stripe_plan', plan);
                    sessionStorage.setItem('stripe_redirect', window.location.href);
                    window.location.href = '/login.html';
                    return;
                }
                
                // Show loading
                const originalText = newButton.textContent;
                newButton.textContent = 'Processing...';
                newButton.disabled = true;
                
                try {
                    const toggleElement = document.getElementById('pricingToggle');
                    const billingPeriod = toggleElement?.classList.contains('active') ? 'yearly' : 'monthly';
                    
                    console.log('[Stripe Final] Calling API...');
                    const response = await originalFetch(`${API_BASE}/api/stripe/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            plan: plan,
                            billing_period: billingPeriod
                        })
                    });
                    
                    console.log('[Stripe Final] Response:', response.status);
                    
                    if (response.status === 401) {
                        localStorage.clear();
                        sessionStorage.setItem('stripe_plan', plan);
                        sessionStorage.setItem('stripe_redirect', window.location.href);
                        window.location.href = '/login.html';
                        return;
                    }
                    
                    const data = await response.json();
                    
                    if (response.ok && data.checkout_url) {
                        console.log('[Stripe Final] Success! Redirecting...');
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error(data.detail || 'Failed to create checkout');
                    }
                } catch (error) {
                    console.error('[Stripe Final] Error:', error);
                    alert('Unable to process payment. Please try logging in again.');
                    newButton.textContent = originalText;
                    newButton.disabled = false;
                }
            });
        });
    }
    
    // Setup on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupStripeButtons);
    } else {
        setupStripeButtons();
    }
    
    // Handle redirect after login
    const savedPlan = sessionStorage.getItem('stripe_plan');
    if (savedPlan && localStorage.getItem('access_token')) {
        console.log('[Stripe Final] Detected saved plan:', savedPlan);
        sessionStorage.removeItem('stripe_plan');
        sessionStorage.removeItem('stripe_redirect');
        
        setTimeout(() => {
            const planIndex = ['starter', 'professional', 'business'].indexOf(savedPlan);
            const button = document.querySelectorAll('.pricing-cta.primary')[planIndex];
            if (button && button.textContent.includes('Buy')) {
                console.log('[Stripe Final] Auto-clicking saved plan');
                button.click();
            }
        }, 1000);
    }
})();
SCRIPT

scp -i "$KEY_PATH" /tmp/stripe-final.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
rm /tmp/stripe-final.js

# Update pricing.html with only the final script
echo "3. Updating pricing.html with clean implementation..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove stripe-simple-fix.js if present
sed -i '/<script src="\/js\/stripe-simple-fix\.js"><\/script>/d' pricing.html

# Add only stripe-final.js
if ! grep -q "stripe-final.js" pricing.html; then
    sed -i '/<\/body>/i\    <script src="/js/api-config.js"></script>' pricing.html
    sed -i '/<\/body>/i\    <script src="/js/auth-fixed.js"></script>' pricing.html
    sed -i '/<\/body>/i\    <script src="/js/stripe-final.js"></script>' pricing.html
fi

echo "Pricing page updated with clean implementation"
EOF

echo -e "\n✅ Clean Stripe implementation deployed!"
echo "======================================="
echo "What was done:"
echo "1. Removed ALL conflicting stripe scripts"
echo "2. Removed auth.js that was intercepting requests"
echo "3. Deployed single clean stripe-final.js"
echo "4. Uses original fetch (no interception)"
echo ""
echo "Please clear your browser cache and try again!"