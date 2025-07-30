// Update navigation based on authentication status
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is authenticated
    if (window.BankAuth && window.BankAuth.TokenManager.isAuthenticated()) {
        const user = window.BankAuth.UserManager.getUser();
        
        // Find login/signup links
        const loginLink = document.querySelector('a[href="/login.html"]');
        const signupLink = document.querySelector('a[href="/signup.html"]');
        
        if (loginLink) {
            // Replace login link with dashboard link
            loginLink.textContent = 'Dashboard';
            loginLink.href = '/dashboard.html';
        }
        
        if (signupLink) {
            // Replace signup link with logout
            signupLink.textContent = 'Log Out';
            signupLink.href = '#';
            signupLink.classList.remove('btn-primary');
            signupLink.classList.add('btn-secondary');
            
            // Add logout handler
            signupLink.addEventListener('click', async (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to log out?')) {
                    await window.BankAuth.AuthAPI.logout();
                }
            });
        }
    }
});