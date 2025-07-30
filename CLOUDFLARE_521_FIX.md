# Cloudflare 521 Error Fix

## Server Status ✅
- Nginx: Running on port 80
- Backend: Running on port 8000
- Direct access works: http://3.235.19.83/
- Firewall: Ports 80, 443, 22 open

## Quick Fix Steps

### 1. In Cloudflare Dashboard:
1. Go to DNS settings
2. Find the A record for bankcsvconverter.com
3. Make sure it points to: **3.235.19.83**
4. Click the orange cloud to make it gray (bypass proxy temporarily)
5. Wait 2-3 minutes for DNS propagation

### 2. Test Direct Access:
```bash
curl http://bankcsvconverter.com/
```

### 3. If Direct Access Works:
1. Go back to Cloudflare DNS
2. Click the gray cloud to make it orange again (re-enable proxy)
3. Go to SSL/TLS settings
4. Set encryption mode to **Flexible** (not Full or Full Strict)
5. Wait 2-3 minutes

### 4. Alternative: Cloudflare Page Rules
1. Go to Page Rules
2. Add rule: `*bankcsvconverter.com/*`
3. Settings:
   - SSL: Flexible
   - Cache Level: Standard
   - Always Online: On

## Server Configuration Summary
- Frontend: `/home/ubuntu/bank-statement-converter/frontend`
- Backend: Port 8000 (proxied through nginx)
- Nginx: Configured to accept Cloudflare IPs
- Services: bankconverter.service (active)

## If Still Not Working:
1. Check AWS Lightsail firewall rules
2. Ensure instance is running
3. Try accessing via IP: http://3.235.19.83/
4. Check Cloudflare is not blocking your origin IP