// Stripe Integration - Final Version with Authentication Fix

(function() {
    'use strict';
    
    console.log('[Stripe] Script loaded at', new Date().toISOString());
    
    // Configuration
    const API_CONFIG = {
        getStripeUrl: function() {
            const hostname = window.location.hostname;
            const protocol = window.location.protocol;
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                return 'http://localhost:5000/api/stripe';
            }
            return `${protocol}//${hostname}/api/stripe`;
        }
    };
    
    // Authentication helpers
    const Auth = {
        getToken: function() {
            // Try localStorage first (most reliable)
            const token = localStorage.getItem('access_token');
            if (token) {
                console.log('[Stripe] Token found in localStorage');
                return token;
            }
            
            // Try BankAuth if available
            if (window.BankAuth && window.BankAuth.TokenManager) {
                const bankAuthToken = window.BankAuth.TokenManager.getAccessToken();
                if (bankAuthToken) {
                    console.log('[Stripe] Token found in BankAuth');
                    return bankAuthToken;
                }
            }
            
            console.log('[Stripe] No token found');
            return null;
        },
        
        isAuthenticated: function() {
            const token = this.getToken();
            return !!token;
        }
    };
    
    // Main initialization
    function init() {
        console.log('[Stripe] Initializing...');
        
        // Find all Buy buttons
        const buyButtons = document.querySelectorAll('.pricing-cta.primary');
        console.log('[Stripe] Found', buyButtons.length, 'buy buttons');
        
        if (buyButtons.length === 0) {
            console.warn('[Stripe] No buy buttons found!');
            return;
        }
        
        // Plan mapping
        const plans = ['starter', 'professional', 'business'];
        
        buyButtons.forEach((button, index) => {
            const plan = plans[index];
            if (!plan) {
                console.warn('[Stripe] No plan mapping for button', index);
                return;
            }
            
            console.log('[Stripe] Setting up button', index, 'for plan:', plan);
            
            // Remove existing listeners by cloning
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add click handler
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                handleBuyClick(plan, newButton);
            });
        });
        
        // Check subscription status if authenticated
        if (Auth.isAuthenticated()) {
            checkSubscriptionStatus();
        }
        
        // Handle payment success
        handlePaymentSuccess();
    }
    
    // Handle buy button click
    async function handleBuyClick(plan, button) {
        console.log('[Stripe] Buy button clicked for plan:', plan);
        
        // Check authentication RIGHT NOW
        if (!Auth.isAuthenticated()) {
            console.log('[Stripe] User not authenticated, redirecting to signup');
            const redirectUrl = `/signup.html?plan=${plan}&redirect=/pricing.html`;
            console.log('[Stripe] Redirect URL:', redirectUrl);
            window.location.href = redirectUrl;
            return;
        }
        
        console.log('[Stripe] User authenticated, proceeding with checkout');
        
        // Get billing period
        const toggleElement = document.getElementById('pricingToggle');
        const isYearly = toggleElement && toggleElement.classList.contains('active');
        const billingPeriod = isYearly ? 'yearly' : 'monthly';
        
        console.log('[Stripe] Billing period:', billingPeriod);
        
        // Update button state
        const originalText = button.textContent;
        button.textContent = 'Processing...';
        button.disabled = true;
        
        try {
            const token = Auth.getToken();
            const apiUrl = API_CONFIG.getStripeUrl();
            const payload = {
                plan: plan,
                billing_period: billingPeriod
            };
            
            console.log('[Stripe] API URL:', apiUrl + '/create-checkout-session');
            console.log('[Stripe] Payload:', payload);
            console.log('[Stripe] Token present:', !!token);
            
            const response = await fetch(`${apiUrl}/create-checkout-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            
            console.log('[Stripe] Response status:', response.status);
            
            const responseData = await response.text();
            console.log('[Stripe] Response data:', responseData);
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} - ${responseData}`);
            }
            
            const data = JSON.parse(responseData);
            
            if (!data.checkout_url) {
                throw new Error('No checkout URL in response');
            }
            
            console.log('[Stripe] Redirecting to checkout:', data.checkout_url);
            window.location.href = data.checkout_url;
            
        } catch (error) {
            console.error('[Stripe] Checkout error:', error);
            alert(`Unable to start checkout: ${error.message}`);
            
            // Restore button
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Check subscription status
    async function checkSubscriptionStatus() {
        console.log('[Stripe] Checking subscription status...');
        
        try {
            const token = Auth.getToken();
            const apiUrl = API_CONFIG.getStripeUrl();
            
            const response = await fetch(`${apiUrl}/subscription-status`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const status = await response.json();
                console.log('[Stripe] Subscription status:', status);
                
                if (status.plan && status.plan !== 'free') {
                    displaySubscriptionInfo(status);
                }
            }
        } catch (error) {
            console.error('[Stripe] Error checking subscription:', error);
        }
    }
    
    // Display subscription info
    function displaySubscriptionInfo(status) {
        const heroSection = document.querySelector('.hero');
        if (!heroSection) return;
        
        const infoDiv = document.createElement('div');
        infoDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #f0f9ff; border-radius: 12px; text-align: center;';
        infoDiv.innerHTML = `
            <p style="font-size: 1.8rem; color: #0066ff; margin-bottom: 1rem;">
                Current Plan: <strong>${status.plan.charAt(0).toUpperCase() + status.plan.slice(1)}</strong>
            </p>
            <p style="font-size: 1.6rem; color: #6b7280; margin-bottom: 2rem;">
                ${status.pages_used || 0} / ${status.pages_limit || '∞'} pages used this month
            </p>
            <button id="manageSubscription" style="
                background: #0066ff;
                color: white;
                padding: 1.2rem 2.4rem;
                border: none;
                border-radius: 8px;
                font-size: 1.6rem;
                font-weight: 600;
                cursor: pointer;
            ">Manage Subscription</button>
        `;
        
        heroSection.appendChild(infoDiv);
        
        // Handle manage button
        document.getElementById('manageSubscription').addEventListener('click', manageSubscription);
    }
    
    // Manage subscription
    async function manageSubscription() {
        const button = document.getElementById('manageSubscription');
        const originalText = button.textContent;
        button.textContent = 'Loading...';
        button.disabled = true;
        
        try {
            const token = Auth.getToken();
            const apiUrl = API_CONFIG.getStripeUrl();
            
            const response = await fetch(`${apiUrl}/customer-portal`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    return_url: window.location.origin + '/dashboard.html'
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create portal session');
            }
            
            const data = await response.json();
            if (data.portal_url) {
                window.location.href = data.portal_url;
            }
        } catch (error) {
            console.error('[Stripe] Portal error:', error);
            alert('Unable to open subscription management.');
            button.textContent = originalText;
            button.disabled = false;
        }
    }
    
    // Handle payment success
    function handlePaymentSuccess() {
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        
        if (sessionId) {
            console.log('[Stripe] Payment success detected');
            
            const heroSection = document.querySelector('.hero');
            if (heroSection) {
                const successDiv = document.createElement('div');
                successDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #d1fae5; border-radius: 12px; text-align: center; color: #065f46;';
                successDiv.innerHTML = `
                    <h3 style="font-size: 2.4rem; margin-bottom: 1rem;">🎉 Payment Successful!</h3>
                    <p style="font-size: 1.8rem;">Your subscription is now active. Redirecting to dashboard...</p>
                `;
                heroSection.appendChild(successDiv);
                
                setTimeout(() => {
                    window.location.href = '/dashboard.html';
                }, 3000);
            }
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();