# HTTPS Authentication Troubleshooting Guide

## Issues Found and Fixed

### 1. Cookie Secure Flag Issue
**Problem:** Cookies weren't being set with `secure=true` on HTTPS
**Cause:** Production detection was checking for exact hostname match
**Fix:** Updated `set_auth_cookies()` to properly detect HTTPS and production environment

### 2. Cookie Domain Issue
**Problem:** Cookies might not work across subdomains (www vs non-www)
**Fix:** Using `.bankcsvconverter.com` as cookie domain for cross-subdomain support

### 3. Old Auth Scripts
**Problem:** Old authentication scripts might still be loaded
**Fix:** Moved all old scripts to backup folder

## Quick Debugging Steps

1. **Check if scripts are loading:**
   ```javascript
   // In browser console
   console.log(typeof window.UnifiedAuth); // Should be 'object'
   ```

2. **Check cookies in DevTools:**
   - Open DevTools (F12)
   - Go to Application > Cookies
   - Look for `access_token` and `refresh_token`
   - Verify they have:
     - HttpOnly: ✓
     - Secure: ✓ (on HTTPS)
     - Domain: .bankcsvconverter.com

3. **Test authentication:**
   ```javascript
   // In browser console
   fetch('/v2/api/auth/check', { credentials: 'include' })
     .then(r => r.json())
     .then(console.log);
   ```

4. **Check for errors:**
   - Open DevTools Console
   - Look for any red errors
   - Check Network tab for failed requests

## Debug Tool

Visit: https://bankcsvconverter.com/debug-production-auth.html

This tool will:
- Check if auth-unified.js is loaded
- Test API endpoints
- Show cookie information
- Test registration/login
- Display console errors

## Common Issues and Solutions

### Issue: "UnifiedAuth is not defined"
**Solution:** auth-unified.js is not loading. Check:
- File exists at /js/auth-unified.js
- No 404 errors in Network tab
- Script tag is present in HTML

### Issue: Cookies not being set
**Solution:** Check:
- HTTPS is being used
- No CORS errors
- Backend is responding with Set-Cookie headers

### Issue: Authentication not persisting
**Solution:** Check:
- Cookies have correct domain (.bankcsvconverter.com)
- No JavaScript errors clearing cookies
- Cross-tab communication is working

### Issue: Logout not syncing across tabs
**Solution:** Check:
- BroadcastChannel is supported in browser
- No console errors about localStorage
- auth-unified.js is loaded on all pages

## Manual Test Checklist

1. [ ] Clear all cookies for bankcsvconverter.com
2. [ ] Register new account
3. [ ] Verify auto-login (should go to dashboard, not login page)
4. [ ] Open new tab, go to dashboard - should be logged in
5. [ ] Open another tab, go to settings - should be logged in
6. [ ] Logout in one tab - all tabs should logout

## Backend Verification

SSH to server and check:
```bash
# Check if backend is running
sudo systemctl status backend

# Check backend logs
sudo journalctl -u backend -n 100

# Check if auth_cookie.py was updated
grep "is_production" /home/ubuntu/backend/api/auth_cookie.py

# Check nginx logs for errors
sudo tail -f /var/log/nginx/error.log
```

## If Still Not Working

1. **Check CloudFlare settings:**
   - SSL/TLS mode should be "Full" or "Full (strict)"
   - Check if any Page Rules are interfering
   - Ensure cookies aren't being stripped

2. **Verify nginx configuration:**
   - Proxy passes are correct
   - Headers are being forwarded
   - Cookie path/domain aren't being modified

3. **Test with curl:**
   ```bash
   curl -v https://bankcsvconverter.com/v2/api/auth/csrf
   ```
   Look for Set-Cookie headers in response

## Emergency Rollback

If needed, old auth scripts are backed up in:
- `/var/www/html/js/old-auth-backup/`
- Local: `js/old-auth-backup/`

To rollback:
```bash
# On server
sudo mv /var/www/html/js/old-auth-backup/auth.js /var/www/html/js/
# Restore old HTML files from backup
```