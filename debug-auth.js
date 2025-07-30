// Debug script to check authentication state
console.log('=== AUTH DEBUG START ===');
console.log('1. window.BankAuth exists?', typeof window.BankAuth !== 'undefined');
if (window.BankAuth) {
    console.log('2. TokenManager exists?', typeof window.BankAuth.TokenManager !== 'undefined');
    if (window.BankAuth.TokenManager) {
        console.log('3. getAccessToken exists?', typeof window.BankAuth.TokenManager.getAccessToken === 'function');
        console.log('4. isAuthenticated exists?', typeof window.BankAuth.TokenManager.isAuthenticated === 'function');
        
        const token = window.BankAuth.TokenManager.getAccessToken();
        console.log('5. Access token:', token ? token.substring(0, 50) + '...' : 'null');
        console.log('6. Token in localStorage:', localStorage.getItem('access_token') ? 'YES' : 'NO');
        console.log('7. isAuthenticated returns:', window.BankAuth.TokenManager.isAuthenticated());
    }
}
console.log('=== AUTH DEBUG END ===');