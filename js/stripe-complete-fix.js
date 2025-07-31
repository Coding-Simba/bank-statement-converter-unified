// Complete Stripe Fix - All-in-one solution
(function() {
    console.log('[Stripe Complete] Starting...');
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
    // Store original fetch to bypass any interception
    const originalFetch = window.fetch;
    
    // Check current page
    const isLoginPage = window.location.pathname.includes('login.html');
    const isPricingPage = window.location.pathname.includes('pricing.html');
    
    // Handle login page redirect
    if (isLoginPage) {
        console.log('[Stripe Complete] On login page, setting up redirect handler...');
        
        // Check for stored redirect
        const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                        sessionStorage.getItem('stripe_redirect') || 
                        sessionStorage.getItem('redirect_after_login');
        
        if (redirect) {
            console.log('[Stripe Complete] Will redirect to:', redirect);
            
            // Watch for successful login
            const originalSetItem = localStorage.setItem;
            localStorage.setItem = function(key, value) {
                originalSetItem.call(localStorage, key, value);
                
                if (key === 'access_token' && value) {
                    console.log('[Stripe Complete] Login successful, redirecting...');
                    
                    // Clear all redirect keys
                    sessionStorage.removeItem('redirect_after_stripe');
                    sessionStorage.removeItem('stripe_redirect');
                    sessionStorage.removeItem('redirect_after_login');
                    sessionStorage.removeItem('stripe_plan');
                    sessionStorage.removeItem('intended_plan');
                    
                    // Restore original setItem
                    localStorage.setItem = originalSetItem;
                    
                    // Redirect
                    setTimeout(() => {
                        window.location.href = redirect;
                    }, 100);
                }
            };
        }
    }
    
    // Handle pricing page
    if (isPricingPage) {
        console.log('[Stripe Complete] On pricing page, setting up buy buttons...');
        
        function setupButtons() {
            const buttons = document.querySelectorAll('.pricing-cta.primary');
            console.log('[Stripe Complete] Found buttons:', buttons.length);
            
            buttons.forEach((button, index) => {
                if (!button.textContent.includes('Buy')) return;
                
                const plans = ['starter', 'professional', 'business'];
                const plan = plans[index];
                if (!plan) return;
                
                // Remove all existing handlers
                const newButton = button.cloneNode(true);
                button.parentNode.replaceChild(newButton, button);
                
                newButton.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('[Stripe Complete] Buy clicked for plan:', plan);
                    
                    // Check authentication
                    const token = localStorage.getItem('access_token');
                    const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
                    
                    if (!token || !userData) {
                        console.log('[Stripe Complete] Not authenticated, saving state and redirecting...');
                        
                        // Save current state
                        sessionStorage.setItem('redirect_after_stripe', window.location.href);
                        sessionStorage.setItem('stripe_plan', plan);
                        
                        // Redirect to login
                        window.location.href = '/login.html';
                        return;
                    }
                    
                    console.log('[Stripe Complete] Authenticated, proceeding with checkout...');
                    
                    // Get billing period
                    const toggleElement = document.getElementById('pricingToggle');
                    const billingPeriod = toggleElement?.classList.contains('active') ? 'yearly' : 'monthly';
                    
                    // Update button state
                    const originalText = newButton.textContent;
                    newButton.textContent = 'Processing...';
                    newButton.disabled = true;
                    newButton.style.opacity = '0.7';
                    
                    try {
                        console.log('[Stripe Complete] Making API call to create checkout session...');
                        
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
                        
                        console.log('[Stripe Complete] API response status:', response.status);
                        
                        if (response.status === 401) {
                            console.log('[Stripe Complete] Token expired, clearing auth and redirecting...');
                            
                            // Clear auth
                            localStorage.removeItem('access_token');
                            localStorage.removeItem('refresh_token');
                            localStorage.removeItem('user_data');
                            localStorage.removeItem('user');
                            
                            // Save state and redirect
                            sessionStorage.setItem('redirect_after_stripe', window.location.href);
                            sessionStorage.setItem('stripe_plan', plan);
                            
                            window.location.href = '/login.html';
                            return;
                        }
                        
                        const data = await response.json();
                        console.log('[Stripe Complete] API response data:', data);
                        
                        if (response.ok && data.checkout_url) {
                            console.log('[Stripe Complete] Success! Redirecting to Stripe checkout...');
                            window.location.href = data.checkout_url;
                        } else {
                            throw new Error(data.detail || 'Failed to create checkout session');
                        }
                        
                    } catch (error) {
                        console.error('[Stripe Complete] Error:', error);
                        
                        // Show user-friendly error
                        alert('Unable to process payment at this time. Please try again or contact support.');
                        
                        // Restore button
                        newButton.textContent = originalText;
                        newButton.disabled = false;
                        newButton.style.opacity = '1';
                    }
                });
            });
        }
        
        // Setup buttons when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupButtons);
        } else {
            // Small delay to ensure other scripts have loaded
            setTimeout(setupButtons, 500);
        }
        
        // Check if we should auto-click after login
        const savedPlan = sessionStorage.getItem('stripe_plan');
        if (savedPlan && localStorage.getItem('access_token')) {
            console.log('[Stripe Complete] Found saved plan after login:', savedPlan);
            
            // Clear saved state
            sessionStorage.removeItem('stripe_plan');
            sessionStorage.removeItem('redirect_after_stripe');
            
            // Auto-click the button
            setTimeout(() => {
                const planIndex = ['starter', 'professional', 'business'].indexOf(savedPlan);
                if (planIndex !== -1) {
                    const buttons = document.querySelectorAll('.pricing-cta.primary');
                    const button = buttons[planIndex];
                    if (button && button.textContent.includes('Buy')) {
                        console.log('[Stripe Complete] Auto-clicking plan button...');
                        button.click();
                    }
                }
            }, 1000);
        }
    }
})();