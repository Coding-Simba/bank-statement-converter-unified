/**
 * Login page handler using cookie-based authentication
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorDiv = document.getElementById('errorMessage');
    const loadingDiv = document.getElementById('loadingMessage');
    
    // Check for redirect after login
    const urlParams = new URLSearchParams(window.location.search);
    const redirect = urlParams.get('redirect') || 
                    sessionStorage.getItem('redirect_after_login') ||
                    sessionStorage.getItem('redirect_after_stripe');
    
    if (redirect) {
        console.log('[Login] Will redirect to:', redirect);
    }
    
    // If already authenticated, redirect
    if (window.authService && window.authService.isAuthenticated()) {
        if (redirect) {
            sessionStorage.removeItem('redirect_after_login');
            sessionStorage.removeItem('redirect_after_stripe');
            sessionStorage.removeItem('stripe_plan');
            window.location.href = redirect;
        } else {
            window.location.href = '/dashboard.html';
        }
        return;
    }
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Show loading
            if (loadingDiv) {
                loadingDiv.style.display = 'block';
                loadingDiv.textContent = 'Logging in...';
            }
            if (errorDiv) {
                errorDiv.style.display = 'none';
            }
            
            try {
                // Use the auth service
                const result = await window.authService.login(email, password);
                
                if (result.success) {
                    // Login successful
                    if (loadingDiv) {
                        loadingDiv.textContent = 'Login successful! Redirecting...';
                    }
                    
                    // Check for saved Stripe plan (for auto-clicking buy button)
                    const stripePlan = sessionStorage.getItem('stripe_plan');
                    
                    // Clear session storage
                    const redirectUrl = redirect || '/dashboard.html';
                    sessionStorage.removeItem('redirect_after_login');
                    sessionStorage.removeItem('redirect_after_stripe');
                    
                    // If we have a Stripe plan, keep it for auto-click
                    if (stripePlan && redirectUrl.includes('pricing')) {
                        sessionStorage.setItem('stripe_plan', stripePlan);
                    }
                    
                    // Redirect
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 500);
                } else {
                    // Login failed
                    if (loadingDiv) {
                        loadingDiv.style.display = 'none';
                    }
                    if (errorDiv) {
                        errorDiv.style.display = 'block';
                        errorDiv.textContent = result.error || 'Invalid email or password';
                    }
                }
            } catch (error) {
                console.error('[Login] Error:', error);
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
                if (errorDiv) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'An error occurred. Please try again.';
                }
            }
        });
    }
    
    // Handle Google OAuth button
    const googleBtn = document.getElementById('googleLoginBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', function() {
            // Save redirect URL for after OAuth
            if (redirect) {
                sessionStorage.setItem('oauth_redirect', redirect);
            }
            window.location.href = '/api/auth/google';
        });
    }
    
    // Password visibility toggle
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        });
    }
});