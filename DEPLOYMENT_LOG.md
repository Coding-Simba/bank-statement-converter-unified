# Deployment Log

## 2025-08-02 - Login Page Fix

### Issue
- Login page showing "Uncaught SyntaxError: Invalid or unexpected token" 
- auth-unified.js had escaped operators (\!)
- Login page was loading wrong auth script (auth-unified.js instead of auth-cookie.js)

### Fix
1. Copied correct auth-unified.js from local to server
2. Copied correct login.html that loads auth-cookie.js
3. Verified no more syntax errors

### Files Updated on Server
- `/home/ubuntu/bank-statement-converter/frontend/js/auth-unified.js`
- `/home/ubuntu/bank-statement-converter/frontend/login.html`

### Status
✅ Login page working correctly

## 2025-08-02 - Nginx V2 Routing Fix

### Issue
- Login showing "An unexpected error occurred"
- V2 API endpoints (/v2/api/auth/*) not routed by nginx
- Health endpoint returning HTML instead of JSON

### Fix
1. Fixed nginx configuration to route /v2/ and /health endpoints
2. Removed duplicate proxy_pass directives
3. Deployed clean nginx configuration

### Files Updated
- `/etc/nginx/sites-enabled/bank-converter` - Complete rewrite with proper routing

### Status
✅ All API endpoints working (Cloudflare may show 521 temporarily)