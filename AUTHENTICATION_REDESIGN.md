# Professional JWT Authentication System Redesign

## Current Issues
1. JWT tokens stored in localStorage (vulnerable to XSS)
2. No token persistence across page refreshes
3. Tokens cleared on API errors
4. No refresh token rotation
5. Multiple conflicting auth scripts
6. Users get logged out randomly

## New Architecture (Industry Standard 2025)

### 1. Token Storage
- **Access Token**: HTTP-only cookie (15 minute expiry)
- **Refresh Token**: HTTP-only cookie (7 day expiry with rotation)
- **No localStorage usage** for sensitive data

### 2. Cookie Configuration
```python
# Backend cookie settings
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,      # Prevents JavaScript access
    secure=True,        # HTTPS only
    samesite="lax",     # CSRF protection
    max_age=900,        # 15 minutes
    path="/"
)

response.set_cookie(
    key="refresh_token", 
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="lax",
    max_age=604800,     # 7 days
    path="/api/auth/refresh"  # Only sent to refresh endpoint
)
```

### 3. Frontend Changes
```javascript
// All API calls must include credentials
fetch('/api/endpoint', {
    method: 'GET',
    credentials: 'include',  // Automatically sends cookies
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken  // CSRF protection
    }
})
```

### 4. Authentication Flow

#### Login Flow
1. User submits credentials to `/api/auth/login`
2. Backend validates credentials
3. Backend creates access_token (15m) and refresh_token (7d)
4. Backend sets both tokens as HTTP-only cookies
5. Backend returns user data (no tokens in response body)
6. Frontend stores only non-sensitive user data in localStorage

#### Token Refresh Flow
1. Access token expires after 15 minutes
2. API call returns 401
3. Frontend automatically calls `/api/auth/refresh`
4. Backend validates refresh token from cookie
5. Backend generates new access_token AND new refresh_token (rotation)
6. Backend sets new cookies
7. Frontend retries original request

#### Logout Flow
1. Frontend calls `/api/auth/logout`
2. Backend clears both cookies
3. Frontend clears localStorage user data
4. Redirect to login page

### 5. Security Features

#### CSRF Protection
```python
# Backend generates CSRF token
@router.get("/api/auth/csrf")
async def get_csrf_token(response: Response):
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Frontend needs to read this
        secure=True,
        samesite="strict"
    )
    return {"csrf_token": csrf_token}
```

#### Refresh Token Rotation
- Each refresh token can only be used once
- Using an old refresh token invalidates all tokens (breach detection)
- Store refresh token family ID in database

### 6. Backend Implementation

#### Updated Auth Endpoints
```python
# auth.py
@router.post("/login")
async def login(
    response: Response,
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    # Validate user...
    
    # Create tokens
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,
        path="/api/auth/refresh"
    )
    
    # Return only user data
    return {"user": user_data}
```

#### Token Validation Middleware
```python
# auth_middleware.py
async def validate_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401)
    
    try:
        payload = decode_token(access_token)
        return payload
    except JWTError:
        raise HTTPException(status_code=401)
```

### 7. Frontend Implementation

#### New Auth Service
```javascript
// auth-service.js
class AuthService {
    constructor() {
        this.baseURL = window.location.origin;
        this.csrfToken = null;
    }
    
    async initialize() {
        // Get CSRF token on page load
        const response = await fetch('/api/auth/csrf', {
            credentials: 'include'
        });
        const data = await response.json();
        this.csrfToken = data.csrf_token;
    }
    
    async login(email, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.csrfToken
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            // Store only non-sensitive user data
            localStorage.setItem('user', JSON.stringify(data.user));
            return data;
        }
        throw new Error('Login failed');
    }
    
    async makeAuthenticatedRequest(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken
            }
        });
        
        if (response.status === 401) {
            // Try to refresh token
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry original request
                return fetch(url, {
                    ...options,
                    credentials: 'include',
                    headers: {
                        ...options.headers,
                        'X-CSRF-Token': this.csrfToken
                    }
                });
            }
        }
        
        return response;
    }
    
    async refreshToken() {
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });
            
            return response.ok;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }
    
    isAuthenticated() {
        // Check if user data exists (cookies are HTTP-only)
        return !!localStorage.getItem('user');
    }
    
    logout() {
        fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'X-CSRF-Token': this.csrfToken
            }
        });
        localStorage.removeItem('user');
        window.location.href = '/login.html';
    }
}

// Initialize on every page
const authService = new AuthService();
document.addEventListener('DOMContentLoaded', () => {
    authService.initialize();
});
```

### 8. Migration Plan

1. **Phase 1**: Update backend to support both cookie and header auth
2. **Phase 2**: Deploy new auth-service.js to all pages
3. **Phase 3**: Update all API calls to use credentials: 'include'
4. **Phase 4**: Remove localStorage token storage
5. **Phase 5**: Remove old auth scripts
6. **Phase 6**: Enable strict cookie-only auth

### 9. Benefits

1. **Security**: Immune to XSS attacks
2. **Persistence**: Survives page refresh
3. **Automatic**: Browser handles cookie storage
4. **Seamless**: Silent token refresh
5. **Professional**: Industry standard approach

### 10. Testing Checklist

- [ ] Login sets HTTP-only cookies
- [ ] Cookies persist across page refresh
- [ ] API calls include cookies automatically
- [ ] Token refresh works silently
- [ ] Logout clears all cookies
- [ ] CSRF protection prevents attacks
- [ ] Old refresh tokens are invalidated
- [ ] 401 triggers automatic refresh