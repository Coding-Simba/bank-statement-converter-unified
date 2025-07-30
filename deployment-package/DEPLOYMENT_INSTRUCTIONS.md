# Stripe Integration Deployment Instructions

## Files to Deploy

This package contains the following updated files that need to be deployed:

1. **JavaScript Files** (copy to `/var/www/html/js/`):
   - `stripe-integration.js` - Updated Stripe integration with fixed price handling
   - `auth.js` - Authentication module with dynamic API configuration
   - `dashboard.js` - Dashboard with subscription status display

2. **Backend Environment** (update `/home/bankcsv/backend/.env`):
   - `backend.env` - Contains the SWITCHED price IDs for correct monthly/yearly pricing

## Deployment Steps

### 1. SSH into the server
```bash
ssh ubuntu@3.235.19.83
```

### 2. Backup existing files
```bash
# Backup JavaScript files
sudo cp /var/www/html/js/stripe-integration.js /var/www/html/js/stripe-integration.js.backup
sudo cp /var/www/html/js/auth.js /var/www/html/js/auth.js.backup
sudo cp /var/www/html/js/dashboard.js /var/www/html/js/dashboard.js.backup

# Backup backend env
sudo cp /home/bankcsv/backend/.env /home/bankcsv/backend/.env.backup
```

### 3. Upload new files
From your local machine, upload the files:
```bash
# Upload JavaScript files
scp stripe-integration.js auth.js dashboard.js ubuntu@3.235.19.83:/tmp/

# Upload backend env
scp backend.env ubuntu@3.235.19.83:/tmp/
```

### 4. Deploy the files on server
```bash
# Copy JavaScript files
sudo cp /tmp/stripe-integration.js /var/www/html/js/
sudo cp /tmp/auth.js /var/www/html/js/
sudo cp /tmp/dashboard.js /var/www/html/js/

# Update backend .env (IMPORTANT: Check the price IDs are switched)
sudo cp /tmp/backend.env /home/bankcsv/backend/.env

# Set correct permissions
sudo chown www-data:www-data /var/www/html/js/*.js
sudo chmod 644 /var/www/html/js/*.js
sudo chown www-data:www-data /home/bankcsv/backend/.env
sudo chmod 600 /home/bankcsv/backend/.env
```

### 5. Restart backend service
```bash
sudo systemctl restart bankcsv-backend
sudo systemctl status bankcsv-backend
```

### 6. Clear CloudFlare cache
1. Log into CloudFlare dashboard
2. Go to Caching > Configuration
3. Click "Purge Everything"

Or use CloudFlare API:
```bash
# Purge specific files
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
     -H "X-Auth-Email: {email}" \
     -H "X-Auth-Key: {api_key}" \
     -H "Content-Type: application/json" \
     --data '{"files":["https://bankcsvconverter.com/js/stripe-integration.js","https://bankcsvconverter.com/js/auth.js","https://bankcsvconverter.com/js/dashboard.js"]}'
```

## Key Changes Made

1. **Stripe Price IDs**: Monthly and yearly price IDs have been SWITCHED in the .env file to show correct pricing
2. **JavaScript Error Fixes**: Fixed duplicate `getApiBase` declarations using IIFE pattern
3. **Dashboard Updates**: Added subscription status display and proper monthly/yearly usage tracking

## Verification Steps

After deployment:

1. **Test Stripe pricing**:
   - Go to https://bankcsvconverter.com/pricing.html
   - Verify monthly toggle shows monthly prices
   - Click a Buy button and verify Stripe checkout shows correct price

2. **Test authentication**:
   - Try logging in at https://bankcsvconverter.com/login.html
   - Verify no JavaScript errors in console

3. **Test dashboard**:
   - Go to https://bankcsvconverter.com/dashboard.html
   - Verify subscription status displays correctly
   - Check usage statistics show properly

## Troubleshooting

If you see errors:

1. **Check backend logs**:
   ```bash
   sudo journalctl -u bankcsv-backend -n 100 -f
   ```

2. **Check nginx logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Verify files were updated**:
   ```bash
   # Check file timestamps
   ls -la /var/www/html/js/stripe-integration.js
   ls -la /home/bankcsv/backend/.env
   ```

4. **Force reload without cache**:
   - In Chrome: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
   - Or open DevTools > Network tab > Check "Disable cache"