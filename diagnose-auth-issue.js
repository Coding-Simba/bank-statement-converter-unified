// Diagnostic script - Copy and paste this into browser console on pricing page

console.log('=== AUTHENTICATION DIAGNOSTIC ===');
console.log('Page:', window.location.href);
console.log('Time:', new Date().toISOString());

// 1. Check localStorage
console.log('\n1. LOCALSTORAGE CHECK:');
const token = localStorage.getItem('access_token');
console.log('  access_token exists:', !!token);
if (token) {
    console.log('  token preview:', token.substring(0, 50) + '...');
}
console.log('  user_email:', localStorage.getItem('user_email') || 'not found');

// 2. Check BankAuth
console.log('\n2. BANKAUTH CHECK:');
if (typeof window.BankAuth !== 'undefined') {
    console.log('  BankAuth: FOUND');
    if (window.BankAuth.TokenManager) {
        console.log('  TokenManager: FOUND');
        try {
            const baToken = window.BankAuth.TokenManager.getAccessToken();
            const isAuth = window.BankAuth.TokenManager.isAuthenticated();
            console.log('  getAccessToken():', baToken ? 'returns token' : 'returns null');
            console.log('  isAuthenticated():', isAuth);
        } catch (e) {
            console.log('  Error calling methods:', e.message);
        }
    } else {
        console.log('  TokenManager: NOT FOUND');
    }
} else {
    console.log('  BankAuth: NOT FOUND (auth.js may not be loaded)');
}

// 3. Check Buy buttons
console.log('\n3. BUY BUTTON CHECK:');
const buttons = document.querySelectorAll('.pricing-cta.primary');
console.log('  Found buttons:', buttons.length);
if (buttons.length > 0) {
    const firstButton = buttons[0];
    console.log('  First button text:', firstButton.textContent.trim());
    console.log('  First button href:', firstButton.href || 'no href');
    
    // Check for event listeners (Chrome DevTools specific)
    if (window.getEventListeners) {
        const listeners = getEventListeners(firstButton);
        console.log('  Event listeners:', Object.keys(listeners));
    }
}

// 4. Test authentication flow
console.log('\n4. AUTHENTICATION FLOW TEST:');
function testAuthFlow() {
    const token = localStorage.getItem('access_token');
    let decision = 'NOT AUTHENTICATED';
    
    if (token) {
        console.log('  ✓ Token found in localStorage');
        decision = 'AUTHENTICATED';
    } else {
        console.log('  ✗ No token in localStorage');
    }
    
    if (window.BankAuth && window.BankAuth.TokenManager) {
        const isAuth = window.BankAuth.TokenManager.isAuthenticated();
        if (isAuth) {
            console.log('  ✓ BankAuth says authenticated');
        } else {
            console.log('  ✗ BankAuth says NOT authenticated');
            decision = 'NOT AUTHENTICATED';
        }
    } else {
        console.log('  ! BankAuth not available for check');
    }
    
    console.log('\n  FINAL DECISION:', decision);
    if (decision === 'AUTHENTICATED') {
        console.log('  → Would proceed to Stripe checkout');
    } else {
        console.log('  → Would redirect to /signup.html?plan=starter&redirect=/pricing.html');
    }
}
testAuthFlow();

// 5. Manual buy button test
console.log('\n5. MANUAL BUY BUTTON TEST:');
console.log('To test a buy button, run:');
console.log('  document.querySelector(".pricing-cta.primary").click()');
console.log('\nOr simulate the click logic:');
console.log(`
if (localStorage.getItem('access_token')) {
    console.log('→ Would go to Stripe checkout');
} else {
    console.log('→ Would go to signup page');
    console.log('URL: /signup.html?plan=starter&redirect=/pricing.html');
}
`);

console.log('\n=== END DIAGNOSTIC ===');