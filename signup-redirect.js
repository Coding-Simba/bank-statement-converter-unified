// Add to signup.html to handle already-logged-in users
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in and has a plan parameter
    const urlParams = new URLSearchParams(window.location.search);
    const plan = urlParams.get('plan');
    
    if (plan && window.BankAuth && window.BankAuth.TokenManager.isAuthenticated()) {
        // User is already logged in and trying to buy a plan
        // Redirect back to pricing page
        window.location.href = '/pricing.html';
    }
});