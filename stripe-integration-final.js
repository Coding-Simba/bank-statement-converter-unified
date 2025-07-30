// Stripe Integration for Pricing Page - FINAL WORKING VERSION

// Wait for all dependencies to load
function waitForDependencies(callback) {
    let attempts = 0;
    const maxAttempts = 50; // 5 seconds
    
    const checkDependencies = () => {
        attempts++;
        
        if (window.BankAuth && window.BankAuth.TokenManager && window.API_CONFIG) {
            console.log('Dependencies loaded after', attempts, 'attempts');
            callback();
        } else if (attempts < maxAttempts) {
            setTimeout(checkDependencies, 100);
        } else {
            console.error('Dependencies failed to load after 5 seconds');
            callback(); // Continue anyway
        }
    };
    
    checkDependencies();
}

// Initialize when dependencies are ready
waitForDependencies(() => {
    console.log('Stripe integration initializing with dependencies loaded...');
    
    // Use the existing getApiBase from auth.js or API_CONFIG
    const STRIPE_API_BASE = (() => {
        if (typeof getApiBase !== 'undefined') {
            return getApiBase() + '/api/stripe';
        }
        if (window.API_CONFIG) {
            return window.API_CONFIG.getBaseUrl() + '/api/stripe';
        }
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5000/api/stripe';
        }
        return `${window.location.protocol}//${hostname}/api/stripe`;
    })();
    
    console.log('Stripe API Base:', STRIPE_API_BASE);
    
    // Get all pricing buttons
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    console.log('Found pricing buttons:', pricingButtons.length);
    
    pricingButtons.forEach((button, index) => {
        // Determine the plan based on button position
        const plans = ['starter', 'professional', 'business'];
        const plan = plans[index];
        console.log(`Setting up button ${index} for plan: ${plan}`);
        
        if (plan) {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent any parent handlers
                
                console.log('=== BUY BUTTON CLICKED ===');
                console.log('Plan:', plan);
                console.log('BankAuth available:', !!window.BankAuth);
                console.log('TokenManager available:', !!(window.BankAuth && window.BankAuth.TokenManager));
                
                // Check authentication
                let isAuthenticated = false;
                let accessToken = null;
                
                if (window.BankAuth && window.BankAuth.TokenManager) {
                    accessToken = window.BankAuth.TokenManager.getAccessToken();
                    isAuthenticated = window.BankAuth.TokenManager.isAuthenticated();
                    console.log('Access token exists:', !!accessToken);
                    console.log('Is authenticated:', isAuthenticated);
                } else {
                    console.log('BankAuth not available!');
                }
                
                if (!isAuthenticated || !accessToken) {
                    console.log('Not authenticated, redirecting to signup...');
                    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                    return;
                }
                
                console.log('User is authenticated, proceeding with checkout...');
                
                // Get billing period
                const toggleElement = document.getElementById('pricingToggle');
                const isYearly = toggleElement && toggleElement.classList.contains('active');
                const billingPeriod = isYearly ? 'yearly' : 'monthly';
                
                console.log('Billing period:', billingPeriod);
                
                // Show loading state
                const originalText = button.textContent;
                button.textContent = 'Processing...';
                button.disabled = true;
                
                try {
                    const payload = {
                        plan: plan,
                        billing_period: billingPeriod
                    };
                    
                    console.log('Sending request to:', `${STRIPE_API_BASE}/create-checkout-session`);
                    console.log('Payload:', payload);
                    console.log('Token:', accessToken.substring(0, 50) + '...');
                    
                    const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${accessToken}`
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    console.log('Response status:', response.status);
                    const responseText = await response.text();
                    console.log('Response body:', responseText);
                    
                    if (!response.ok) {
                        throw new Error(`API error: ${responseText}`);
                    }
                    
                    const data = JSON.parse(responseText);
                    console.log('Checkout URL:', data.checkout_url);
                    
                    if (data.checkout_url) {
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error('No checkout URL received');
                    }
                    
                } catch (error) {
                    console.error('Checkout error:', error);
                    alert(`Failed to start checkout: ${error.message}`);
                    
                    // Restore button
                    button.textContent = originalText;
                    button.disabled = false;
                }
            });
        }
    });
    
    // Check subscription status if authenticated
    if (window.BankAuth && window.BankAuth.TokenManager && window.BankAuth.TokenManager.isAuthenticated()) {
        console.log('User authenticated, checking subscription status...');
        checkSubscriptionStatus();
    }
});

// Check subscription status
async function checkSubscriptionStatus() {
    try {
        const token = window.BankAuth.TokenManager.getAccessToken();
        if (!token) {
            console.log('No token for subscription check');
            return;
        }
        
        const STRIPE_API_BASE = (() => {
            if (typeof getApiBase !== 'undefined') {
                return getApiBase() + '/api/stripe';
            }
            if (window.API_CONFIG) {
                return window.API_CONFIG.getBaseUrl() + '/api/stripe';
            }
            return '/api/stripe';
        })();
        
        const response = await fetch(`${STRIPE_API_BASE}/subscription-status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const status = await response.json();
            console.log('Subscription status:', status);
            
            if (status.plan !== 'free') {
                displayManageSubscriptionButton(status);
            }
        }
    } catch (error) {
        console.error('Error checking subscription:', error);
    }
}

// Display manage subscription button
function displayManageSubscriptionButton(status) {
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
        
        document.getElementById('manageSubscription').addEventListener('click', async () => {
            const button = document.getElementById('manageSubscription');
            button.textContent = 'Loading...';
            button.disabled = true;
            
            try {
                const token = window.BankAuth.TokenManager.getAccessToken();
                const STRIPE_API_BASE = (() => {
                    if (typeof getApiBase !== 'undefined') {
                        return getApiBase() + '/api/stripe';
                    }
                    if (window.API_CONFIG) {
                        return window.API_CONFIG.getBaseUrl() + '/api/stripe';
                    }
                    return '/api/stripe';
                })();
                
                const response = await fetch(`${STRIPE_API_BASE}/customer-portal`, {
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
                console.error('Portal error:', error);
                alert('Failed to open subscription management.');
                button.textContent = 'Manage Subscription';
                button.disabled = false;
            }
        });
    }
}