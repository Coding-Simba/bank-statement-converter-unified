#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Simple fix for pricing page authentication"
echo "=========================================="

# Create a simple working solution
cat > js/simple_stripe_handler.js << 'EOF'
// Simple Stripe Handler - Just Make It Work
(function() {
    console.log('[Simple Stripe] Initializing...');
    
    // Wait for page load
    window.addEventListener('DOMContentLoaded', function() {
        console.log('[Simple Stripe] Page loaded, setting up buttons...');
        
        // Get all buy buttons
        const buttons = document.querySelectorAll('.pricing-cta.primary');
        const plans = ['starter', 'professional', 'business'];
        
        buttons.forEach((button, index) => {
            if (!button.textContent.toLowerCase().includes('buy')) return;
            
            const plan = plans[index];
            if (!plan) return;
            
            console.log(`[Simple Stripe] Setting up ${plan} button`);
            
            // Remove any existing handlers
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Remove href
            newButton.removeAttribute('href');
            newButton.style.cursor = 'pointer';
            
            // Add simple click handler
            newButton.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log(`[Simple Stripe] ${plan} clicked`);
                
                // Check localStorage auth (since that's what's working)
                const token = localStorage.getItem('access_token');
                const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
                
                if (!token || !userData) {
                    console.log('[Simple Stripe] Not authenticated, redirecting...');
                    sessionStorage.setItem('redirect_after_login', window.location.href);
                    sessionStorage.setItem('stripe_plan', plan);
                    window.location.href = '/login.html';
                    return;
                }
                
                console.log('[Simple Stripe] Authenticated, creating checkout...');
                
                // Get billing period
                const toggle = document.getElementById('pricingToggle');
                const billingPeriod = toggle?.classList.contains('active') ? 'yearly' : 'monthly';
                
                // Update button
                this.textContent = 'Processing...';
                this.disabled = true;
                
                try {
                    const response = await fetch('/api/stripe/create-checkout-session', {
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
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('[Simple Stripe] Success! Redirecting to:', data.checkout_url);
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error(`API error: ${response.status}`);
                    }
                } catch (error) {
                    console.error('[Simple Stripe] Error:', error);
                    alert('Unable to process payment. Please try again.');
                    this.textContent = 'Buy';
                    this.disabled = false;
                }
            });
        });
        
        console.log('[Simple Stripe] Setup complete');
    });
})();
EOF

# Deploy the simple fix
echo "Deploying simple fix..."
scp -i "$KEY_PATH" js/simple_stripe_handler.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing page to use ONLY this script
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'REMOTE'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove ALL stripe scripts from pricing.html
sed -i '/<script.*stripe.*js/d' pricing.html

# Add our simple handler before </body>
sed -i '/<\/body>/i\    <script src="/js/simple_stripe_handler.js"></script>' pricing.html

echo "Updated pricing.html"

# Show what scripts are loaded
echo -e "\nScripts in pricing.html:"
grep -E "script.*src.*js" pricing.html | grep -E "(auth|stripe|simple)" || echo "No matching scripts"

REMOTE

echo -e "\n✅ Simple fix deployed!"
echo "This uses localStorage auth (which is working)"
echo "Test at: https://bankcsvconverter.com/pricing.html"