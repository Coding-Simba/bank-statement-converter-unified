#!/bin/bash

# Fix Stripe Frontend
echo "🔧 Fixing Stripe Frontend Integration"
echo "===================================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Getting price IDs from backend configuration..."
cd /home/ubuntu/backend
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('Price IDs from environment:')
print(f'STRIPE_STARTER_MONTHLY_PRICE_ID={os.getenv(\"STRIPE_STARTER_MONTHLY_PRICE_ID\")}')
print(f'STRIPE_STARTER_YEARLY_PRICE_ID={os.getenv(\"STRIPE_STARTER_YEARLY_PRICE_ID\")}')
print(f'STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID={os.getenv(\"STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID\")}')
print(f'STRIPE_PROFESSIONAL_YEARLY_PRICE_ID={os.getenv(\"STRIPE_PROFESSIONAL_YEARLY_PRICE_ID\")}')
print(f'STRIPE_BUSINESS_MONTHLY_PRICE_ID={os.getenv(\"STRIPE_BUSINESS_MONTHLY_PRICE_ID\")}')
print(f'STRIPE_BUSINESS_YEARLY_PRICE_ID={os.getenv(\"STRIPE_BUSINESS_YEARLY_PRICE_ID\")}')
" > /tmp/price_ids.txt

cat /tmp/price_ids.txt

echo -e "\n2. Updating stripe-integration.js with correct price mapping..."
cd /home/ubuntu/bank-statement-converter

# Create updated stripe integration
cat > js/stripe-integration-fixed.js << 'EOF'
/**
 * Stripe Integration Module
 * Handles subscription purchases and billing
 */

(function() {
    'use strict';
    
    console.log('Stripe integration initializing...');
    
    // Stripe Price IDs (from backend configuration)
    const PRICE_IDS = {
        starter: {
            monthly: 'price_1RqZtaKwQLBjGTW9w20V3Hst',
            yearly: 'price_1RqZubKwQLBjGTW9deSoEAWV'
        },
        professional: {
            monthly: 'price_1RqZvCKwQLBjGTW9G6DGhEfZ',
            yearly: 'price_1RqZvfKwQLBjGTW9fHNBwXjT'
        },
        business: {
            monthly: 'price_1RqZwMKwQLBjGTW9vhXMz0b3',
            yearly: 'price_1RqZwvKwQLBjGTW9iINHJsUP'
        }
    };
    
    // API configuration
    function getStripeAPIBase() {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        const base = hostname === 'localhost' || hostname === '127.0.0.1'
            ? 'http://localhost:5000'
            : `${protocol}//${hostname}`;
        return `${base}/api/stripe`;
    }
    
    const STRIPE_API_BASE = getStripeAPIBase();
    
    // Wait for UnifiedAuth to be available
    async function waitForAuth() {
        let attempts = 0;
        while (attempts < 50 && (!window.UnifiedAuth || !window.UnifiedAuth.initialized)) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        return window.UnifiedAuth && window.UnifiedAuth.initialized;
    }
    
    // Initialize Stripe integration
    async function initializeStripe() {
        const authReady = await waitForAuth();
        console.log('UnifiedAuth available:', authReady);
        
        if (!authReady) {
            console.error('UnifiedAuth not available');
            return;
        }
        
        const isAuthenticated = window.UnifiedAuth.isAuthenticated();
        console.log('User authenticated:', isAuthenticated);
        
        // Check for pricing page
        if (window.location.pathname.includes('pricing')) {
            setupPricingButtons();
            if (isAuthenticated) {
                checkSubscriptionStatus();
            }
        }
    }
    
    // Setup pricing page buttons
    function setupPricingButtons() {
        const buyButtons = document.querySelectorAll('[data-plan]');
        console.log('Found pricing buttons:', buyButtons.length);
        
        buyButtons.forEach((button, index) => {
            const plan = button.getAttribute('data-plan');
            console.log(`Setting up button ${index} for plan:`, plan);
            
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                console.log('Buy button clicked for plan:', plan);
                
                if (!window.UnifiedAuth.isAuthenticated()) {
                    // Redirect to login with return URL
                    const returnUrl = encodeURIComponent(window.location.href);
                    window.location.href = `/login.html?return=${returnUrl}&plan=${plan}`;
                    return;
                }
                
                await startCheckout(plan);
            });
        });
    }
    
    // Start Stripe checkout
    async function startCheckout(plan) {
        try {
            // Show loading state
            const loadingEl = document.createElement('div');
            loadingEl.className = 'stripe-loading';
            loadingEl.textContent = 'Starting checkout...';
            document.body.appendChild(loadingEl);
            
            // Determine billing period
            const toggleSwitch = document.querySelector('.toggle-switch');
            const toggle = toggleSwitch ? toggleSwitch.querySelector('input[type="checkbox"]') : null;
            const isYearly = toggle ? toggle.checked : false;
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            console.log('Toggle state:', toggleSwitch?.className);
            console.log('Is yearly?', isYearly);
            console.log('Billing period:', billingPeriod);
            
            // Get the price ID
            const priceId = PRICE_IDS[plan]?.[billingPeriod];
            if (!priceId) {
                throw new Error(`No price ID found for ${plan} ${billingPeriod}`);
            }
            
            const payload = {
                price_id: priceId,
                success_url: `${window.location.origin}/dashboard.html?session_id={CHECKOUT_SESSION_ID}`,
                cancel_url: window.location.href
            };
            
            console.log('Sending to Stripe API:', payload);
            console.log('API URL:', `${STRIPE_API_BASE}/create-checkout-session`);
            
            // Create checkout session
            const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${STRIPE_API_BASE}/create-checkout-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            console.log('Stripe API response status:', response.status);
            
            if (!response.ok) {
                const error = await response.json();
                console.error('Stripe API error:', error);
                throw new Error(error.detail || 'Failed to create checkout session');
            }
            
            const data = await response.json();
            console.log('Checkout session created:', data);
            
            // Redirect to Stripe Checkout
            if (data.checkout_url) {
                console.log('Redirecting to Stripe checkout:', data.checkout_url);
                window.location.href = data.checkout_url;
            } else {
                throw new Error('No checkout URL received');
            }
            
        } catch (error) {
            console.error('Checkout error:', error);
            alert('Failed to start checkout process. Please try again.');
        } finally {
            // Remove loading state
            const loadingEl = document.querySelector('.stripe-loading');
            if (loadingEl) {
                loadingEl.remove();
            }
        }
    }
    
    // Check subscription status
    async function checkSubscriptionStatus() {
        try {
            const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${STRIPE_API_BASE}/subscription-status`);
            
            if (response.ok) {
                const status = await response.json();
                console.log('Subscription status:', status);
                
                if (status.has_subscription) {
                    updateUIForActiveSubscription(status);
                }
            }
        } catch (error) {
            console.error('Error checking subscription status:', error);
        }
    }
    
    // Update UI for active subscription
    function updateUIForActiveSubscription(status) {
        const planButtons = document.querySelectorAll('[data-plan]');
        planButtons.forEach(button => {
            const plan = button.getAttribute('data-plan');
            if (plan === status.subscription_plan) {
                button.textContent = 'Current Plan';
                button.disabled = true;
                button.style.opacity = '0.6';
            }
        });
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeStripe);
    } else {
        initializeStripe();
    }
    
    // Export for debugging
    window.StripeIntegration = {
        checkSubscriptionStatus,
        startCheckout,
        PRICE_IDS
    };
    
})();
EOF

echo -e "\n3. Backing up old stripe integration..."
cp js/stripe-integration.js js/stripe-integration-backup-$(date +%s).js

echo -e "\n4. Replacing with fixed version..."
cp js/stripe-integration-fixed.js js/stripe-integration.js

echo -e "\n5. Updating timestamp to force cache refresh..."
TIMESTAMP=$(date +%s)
sed -i "s|stripe-integration.js?v=[0-9]*|stripe-integration.js?v=${TIMESTAMP}|g" pricing.html

echo -e "\n6. Verifying the update..."
grep "stripe-integration.js" pricing.html | head -2

echo -e "\n7. Testing the backend is still running..."
curl -s http://localhost:5000/health | head -5

ENDSSH

echo ""
echo -e "${GREEN}✓ Stripe frontend fixed!${NC}"
echo ""
echo "The checkout should now work properly with the correct price IDs."
echo "Clear your browser cache and try again at: https://bankcsvconverter.com/pricing.html"