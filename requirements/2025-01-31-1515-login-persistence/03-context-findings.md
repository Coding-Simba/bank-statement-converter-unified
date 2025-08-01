# Context Findings

## Current Authentication Implementation

### Architecture Overview
- **Backend**: FastAPI with JWT authentication
- **Frontend**: Mix of localStorage-based and cookie-based auth scripts
- **Database**: SQLite with User model supporting refresh token rotation

### Key Issues Identified

#### 1. Multiple Conflicting Authentication Scripts
- `js/auth.js` - Uses localStorage for tokens
- `js/auth-persistent.js` - Attempts to add persistence
- `js/auth-service.js` - Modern cookie-based implementation (not fully deployed)
- `js/auth-fixed.js`, `js/auth-universal.js` - Various patches and fixes

#### 2. Token Storage Problems
- Currently using `localStorage` for JWT tokens (vulnerable to XSS)
- Tokens are cleared on various API errors
- No consistent token refresh mechanism
- Cookie domain not properly set (`COOKIE_DOMAIN = None`)

#### 3. Login Form Has "Remember Me" But Not Implemented
- HTML checkbox exists: `<input id="remember" name="remember" type="checkbox"/>`
- Backend doesn't process the remember me flag
- No differentiation in token lifetime based on remember me

#### 4. Token Expiration Issues
- Access tokens: 24 hours (too long for security)
- Refresh tokens: 30 days
- No automatic refresh mechanism in frontend
- No session management for multi-device support

### Files That Need Modification

#### Backend Files
1. `/backend/api/auth.py` - Main auth endpoints
2. `/backend/api/auth_cookie.py` - Cookie-based auth (needs deployment)
3. `/backend/utils/auth.py` - Token creation utilities
4. `/backend/models/database.py` - User model with refresh token fields
5. `/backend/main.py` - CORS and middleware configuration

#### Frontend Files
1. `/js/auth.js` - Primary auth script (needs replacement)
2. `/login.html` - Login form
3. `/pricing.html` - Protected page example
4. All HTML files - Need consistent auth script inclusion

### Similar Features Analyzed

#### Successful Cookie-Based Auth Pattern
```python
# From auth_cookie.py
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=production,
    samesite="lax",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/",
    domain=COOKIE_DOMAIN  # This needs to be set!
)
```

#### Current Login Flow
1. User enters credentials
2. Frontend calls `/api/auth/login`
3. Backend returns tokens in response body
4. Frontend stores in localStorage
5. Tokens lost on page refresh or navigation

### Technical Constraints

1. **CORS Configuration**: Already allows credentials
2. **Database Schema**: Has refresh token family fields
3. **GDPR/CCPA Compliance**: Need configurable session timeouts
4. **Multi-device Support**: Need session tracking

### Integration Points

1. **Nginx Configuration**: Needs to proxy cookie headers correctly
2. **API Endpoints**: All need to support credential inclusion
3. **Frontend Fetch Calls**: Need `credentials: 'include'`
4. **Stripe Integration**: Must work with cookie auth

### Best Practices (Industry Standard 2025)

1. **Token Lifetimes**:
   - Access token: 15 minutes
   - Refresh token (no remember me): 24 hours
   - Refresh token (with remember me): 30-90 days

2. **Storage**:
   - Access & Refresh tokens in HTTP-only cookies
   - Only non-sensitive user data in localStorage

3. **Security**:
   - CSRF protection required
   - Token rotation on refresh
   - Revocation mechanism needed

### Root Cause Analysis

The main issue is that the website is using multiple conflicting authentication systems:
1. Old localStorage-based system (still active)
2. Partially implemented cookie-based system
3. Various patches trying to fix persistence

The solution requires:
1. Complete removal of localStorage token storage
2. Full deployment of cookie-based auth
3. Proper cookie domain configuration
4. Remember me functionality implementation
5. Automatic token refresh mechanism