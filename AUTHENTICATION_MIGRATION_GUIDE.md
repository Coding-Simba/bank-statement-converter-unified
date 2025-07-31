# Authentication System Migration Guide

## Overview
This guide explains how to migrate from the broken localStorage-based authentication to the new professional cookie-based system.

## Why This Change?
- **Current Issues**: Users randomly logged out, tokens lost on refresh, vulnerable to XSS
- **New Benefits**: Persistent authentication, automatic token refresh, industry-standard security

## Migration Steps

### 1. Deploy Backend Changes
```bash
./deploy_cookie_auth.sh
```

This will:
- Deploy new cookie-based auth endpoints
- Add refresh token rotation to database
- Update CORS for credential support
- Keep old auth working during transition

### 2. Test New Authentication
Visit https://bankcsvconverter.com/login.html and check console for:
```
[AuthService] Initializing...
[AuthService] CSRF token obtained
[AuthService] Auth check completed
```

### 3. Gradual Migration
The system supports both old and new auth during migration:

- **Old endpoints**: `/api/auth/*` (localStorage)
- **New endpoints**: `/api/v2/auth/*` (cookies)

### 4. Update Remaining Pages
Once tested, update all pages to use new auth:

```javascript
// Old way (remove this)
const token = localStorage.getItem('access_token');
fetch('/api/endpoint', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// New way (use this)
const response = await window.authService.fetch('/api/endpoint');
```

### 5. Complete Migration
After all pages work with cookie auth:

1. Remove old auth scripts:
   - auth-fixed.js
   - auth-persistent.js
   - auth-universal.js
   - All other auth-*.js except auth-service.js

2. Update backend to remove old auth endpoints

3. Enable strict cookie-only mode

## Key Features

### Automatic Token Refresh
```javascript
// Tokens refresh automatically
const response = await authService.fetch('/api/protected');
// If 401, automatically refreshes and retries
```

### Persistent Login
- Survives page refresh ✓
- Survives browser restart ✓
- Works across all pages ✓

### Enhanced Security
- HTTP-only cookies (no JS access)
- CSRF protection
- Refresh token rotation
- Secure & SameSite flags

## Testing Checklist

- [ ] Login persists after page refresh
- [ ] Login persists across different pages
- [ ] Stripe checkout works when authenticated
- [ ] Token refresh happens silently (15 min)
- [ ] Logout clears all authentication
- [ ] CSRF token prevents attacks

## API Changes

### Login
```javascript
// Old
POST /api/auth/login
Response: { access_token, refresh_token, user }

// New
POST /api/v2/auth/login
Response: { user }  // Tokens in HTTP-only cookies
```

### Protected Requests
```javascript
// Old
fetch('/api/endpoint', {
    headers: { 'Authorization': 'Bearer TOKEN' }
})

// New
authService.fetch('/api/endpoint')  // Cookies sent automatically
```

## Troubleshooting

### "Not authenticated" after login
- Check cookies in DevTools > Application > Cookies
- Ensure `credentials: 'include'` in fetch calls
- Verify CORS allows your domain

### Tokens not refreshing
- Check refresh_token cookie exists
- Verify /api/v2/auth/refresh endpoint works
- Check token expiry times (15 min access, 7 day refresh)

### CSRF errors
- Ensure auth-service.js loads before other scripts
- Check X-CSRF-Token header is sent
- Verify csrf_token cookie exists

## Benefits After Migration

1. **No More Random Logouts** - Tokens persist properly
2. **Better Security** - Immune to XSS attacks
3. **Smoother UX** - Silent token refresh
4. **Professional Standard** - How Google, Facebook, etc. do it

## Support
If issues persist after migration:
1. Check browser console for [AuthService] logs
2. Verify all cookies are set correctly
3. Test with the test_cookie_auth.py script
4. Clear all site data and try fresh login