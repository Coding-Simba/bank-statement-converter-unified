// Script to analyze what's happening on the pricing page

console.log('=== PRICING PAGE ANALYSIS ===');

// 1. Check what scripts are loaded
console.log('\n1. Loaded Scripts:');
Array.from(document.scripts).forEach(script => {
    if (script.src) {
        console.log('  -', script.src);
    }
});

// 2. Check localStorage
console.log('\n2. LocalStorage:');
console.log('  - access_token:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING');
console.log('  - user_email:', localStorage.getItem('user_email') || 'MISSING');

// 3. Check global objects
console.log('\n3. Global Objects:');
console.log('  - window.BankAuth:', typeof window.BankAuth);
console.log('  - window.API_CONFIG:', typeof window.API_CONFIG);
console.log('  - window.getApiBase:', typeof window.getApiBase);

// 4. Check if BankAuth is properly initialized
if (window.BankAuth) {
    console.log('\n4. BankAuth Details:');
    console.log('  - TokenManager:', typeof window.BankAuth.TokenManager);
    if (window.BankAuth.TokenManager) {
        console.log('  - getAccessToken:', typeof window.BankAuth.TokenManager.getAccessToken);
        console.log('  - isAuthenticated:', typeof window.BankAuth.TokenManager.isAuthenticated);
        try {
            console.log('  - Current token:', window.BankAuth.TokenManager.getAccessToken() ? 'EXISTS' : 'MISSING');
            console.log('  - Is authenticated:', window.BankAuth.TokenManager.isAuthenticated());
        } catch (e) {
            console.log('  - Error checking auth:', e.message);
        }
    }
}

// 5. Check Buy buttons
console.log('\n5. Buy Buttons:');
const buttons = document.querySelectorAll('.pricing-cta.primary');
console.log('  - Found buttons:', buttons.length);
buttons.forEach((btn, i) => {
    console.log(`  - Button ${i}:`, {
        text: btn.textContent.trim(),
        href: btn.href || 'none',
        onclick: btn.onclick ? 'has onclick' : 'no onclick',
        eventListeners: btn._eventListeners || 'cannot access'
    });
});

// 6. Check for navigation interference
console.log('\n6. Navigation Links:');
const navLinks = document.querySelectorAll('a[href="/pricing.html"]');
console.log('  - Pricing links found:', navLinks.length);

// 7. Try to simulate authentication check
console.log('\n7. Authentication Test:');
function testAuth() {
    const token = localStorage.getItem('access_token');
    console.log('  - localStorage token:', !!token);
    
    if (window.BankAuth && window.BankAuth.TokenManager) {
        const bankAuthToken = window.BankAuth.TokenManager.getAccessToken();
        const isAuth = window.BankAuth.TokenManager.isAuthenticated();
        console.log('  - BankAuth token:', !!bankAuthToken);
        console.log('  - BankAuth isAuthenticated:', isAuth);
        console.log('  - Final auth decision:', isAuth && !!bankAuthToken);
    } else {
        console.log('  - BankAuth not available');
        console.log('  - Final auth decision: false (would redirect to signup)');
    }
}
testAuth();

// 8. Check for script loading order issues
console.log('\n8. Script Loading Order:');
console.log('  - DOMContentLoaded fired:', document.readyState === 'complete');
console.log('  - Document ready state:', document.readyState);

console.log('\n=== END ANALYSIS ===');