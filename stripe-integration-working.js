// Stripe Integration for Pricing Page - WORKING VERSION WITH FIXES

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Stripe Integration] Initializing...');
    
    // Set up API base URL
    const STRIPE_API_BASE = (() => {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5000/api/stripe';
        }
        return `${window.location.protocol}//${hostname}/api/stripe`;
    })();
    
    console.log('[Stripe Integration] API Base:', STRIPE_API_BASE);
    
    // Get all pricing buttons
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    console.log('[Stripe Integration] Found', pricingButtons.length, 'pricing buttons');
    
    pricingButtons.forEach((button, index) => {
        // Determine the plan based on button position
        const plans = ['starter', 'professional', 'business'];
        const plan = plans[index];
        
        if (plan) {
            console.log(`[Stripe Integration] Setting up button ${index} for plan: ${plan}`);
            
            // Remove any existing event listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add our click handler
            newButton.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('[Stripe Integration] Buy button clicked for plan:', plan);
                
                // Check authentication
                const token = localStorage.getItem('access_token');
                const hasToken = !!token;
                
                console.log('[Stripe Integration] Token in localStorage:', hasToken);
                
                // Also check BankAuth if available
                let isAuthenticated = hasToken;
                if (window.BankAuth && window.BankAuth.TokenManager) {
                    const bankAuthToken = window.BankAuth.TokenManager.getAccessToken();
                    const bankAuthCheck = window.BankAuth.TokenManager.isAuthenticated();
                    console.log('[Stripe Integration] BankAuth token:', !!bankAuthToken);
                    console.log('[Stripe Integration] BankAuth isAuthenticated:', bankAuthCheck);
                    isAuthenticated = bankAuthCheck && !!bankAuthToken;
                }
                
                if (!isAuthenticated) {
                    console.log('[Stripe Integration] Not authenticated, redirecting to signup...');
                    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                    return;
                }
                
                console.log('[Stripe Integration] User authenticated, creating checkout session...');
                
                // Get billing period
                const toggleElement = document.getElementById('pricingToggle');
                const isYearly = toggleElement && toggleElement.classList.contains('active');
                const billingPeriod = isYearly ? 'yearly' : 'monthly';
                
                console.log('[Stripe Integration] Billing period:', billingPeriod);
                
                // Show loading state
                const originalText = newButton.textContent;
                newButton.textContent = 'Processing...';
                newButton.disabled = true;
                
                try {
                    const requestBody = {
                        plan: plan,
                        billing_period: billingPeriod
                    };
                    
                    console.log('[Stripe Integration] Request URL:', `${STRIPE_API_BASE}/create-checkout-session`);
                    console.log('[Stripe Integration] Request body:', requestBody);
                    
                    const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify(requestBody)
                    });
                    
                    console.log('[Stripe Integration] Response status:', response.status);
                    
                    const responseText = await response.text();
                    console.log('[Stripe Integration] Response text:', responseText);
                    
                    if (!response.ok) {
                        throw new Error(`API error (${response.status}): ${responseText}`);
                    }
                    
                    const data = JSON.parse(responseText);
                    console.log('[Stripe Integration] Parsed response:', data);
                    
                    if (data.checkout_url) {
                        console.log('[Stripe Integration] Redirecting to Stripe:', data.checkout_url);
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error('No checkout URL in response');
                    }
                    
                } catch (error) {
                    console.error('[Stripe Integration] Error:', error);
                    alert(`Failed to start checkout: ${error.message}`);
                    
                    // Restore button
                    newButton.textContent = originalText;
                    newButton.disabled = false;
                }
            });
        }
    });
    
    // Check subscription status if authenticated
    const token = localStorage.getItem('access_token');
    if (token) {
        console.log('[Stripe Integration] User has token, checking subscription status...');
        checkSubscriptionStatus(token, STRIPE_API_BASE);
    }
});

// Check subscription status
async function checkSubscriptionStatus(token, apiBase) {
    try {
        console.log('[Stripe Integration] Checking subscription status...');
        
        const response = await fetch(`${apiBase}/subscription-status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const status = await response.json();
            console.log('[Stripe Integration] Subscription status:', status);
            
            if (status.plan !== 'free') {
                displayManageSubscriptionButton(status, token, apiBase);
            }
        } else {
            console.log('[Stripe Integration] Failed to get subscription status:', response.status);
        }
    } catch (error) {
        console.error('[Stripe Integration] Error checking subscription:', error);
    }
}

// Display manage subscription button
function displayManageSubscriptionButton(status, token, apiBase) {
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        const manageDiv = document.createElement('div');
        manageDiv.className = 'subscription-status';
        manageDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #f0f9ff; border-radius: 12px; text-align: center;';
        
        manageDiv.innerHTML = `
            <p style="font-size: 1.8rem; color: #0066ff; margin-bottom: 1rem;">
                Current Plan: <strong>${status.plan.charAt(0).toUpperCase() + status.plan.slice(1)}</strong>
            </p>
            <p style="font-size: 1.6rem; color: #6b7280; margin-bottom: 2rem;">
                ${status.pages_used} / ${status.pages_limit} pages used this month
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
                transition: all 0.2s;
            ">Manage Subscription</button>
        `;
        
        heroSection.appendChild(manageDiv);
        
        // Add click handler
        document.getElementById('manageSubscription').addEventListener('click', async () => {
            const button = document.getElementById('manageSubscription');
            button.textContent = 'Loading...';
            button.disabled = true;
            
            try {
                const response = await fetch(`${apiBase}/customer-portal`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        return_url: '/dashboard.html'
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to create portal session');
                }
                
                const data = await response.json();
                window.location.href = data.portal_url;
                
            } catch (error) {
                console.error('[Stripe Integration] Portal error:', error);
                alert('Failed to open subscription management.');
                button.textContent = 'Manage Subscription';
                button.disabled = false;
            }
        });
    }
}

// Handle payment success return
if (window.location.search.includes('session_id=')) {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
        console.log('[Stripe Integration] Payment success detected, session:', sessionId);
        
        const heroSection = document.querySelector('.hero');
        if (heroSection) {
            const successDiv = document.createElement('div');
            successDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #d1fae5; border-radius: 12px; text-align: center; color: #065f46;';
            successDiv.innerHTML = '<h3 style="font-size: 2.4rem; margin-bottom: 1rem;">🎉 Payment Successful!</h3><p style="font-size: 1.8rem;">Your subscription is now active. Redirecting to dashboard...</p>';
            heroSection.appendChild(successDiv);
            
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 3000);
        }
    }
}

console.log('[Stripe Integration] Script loaded successfully');