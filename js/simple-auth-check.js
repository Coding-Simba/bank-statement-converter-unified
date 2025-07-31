// Simple Auth Check - Logs authentication state
console.log('[Auth Check] Page:', window.location.pathname);
console.log('[Auth Check] localStorage contents:');
console.log('  access_token:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING');
console.log('  refresh_token:', localStorage.getItem('refresh_token') ? 'EXISTS' : 'MISSING');
console.log('  user_data:', localStorage.getItem('user_data') ? 'EXISTS' : 'MISSING');
console.log('  user:', localStorage.getItem('user') ? 'EXISTS' : 'MISSING');

// Also check sessionStorage
console.log('[Auth Check] sessionStorage contents:');
for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    console.log('  ' + key + ':', sessionStorage.getItem(key));
}