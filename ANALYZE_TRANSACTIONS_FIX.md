# Analyze Transactions Fix Summary

## Issue
The analyze-transactions.html page is showing demo/sample transaction data instead of real parsed data from uploaded PDFs.

## Root Cause
1. The backend API endpoints are not accessible at https://bankcsvconverter.com/api/*
2. The backend service may not be running on the production server
3. Nginx is not configured to proxy /api requests to the backend running on port 5000

## Changes Made

### 1. Fixed API Configuration
**File**: `/js/api-config.js`
- Updated `getBaseUrl()` to use the main domain without port in production
- Previously tried to connect to port 5000 directly, which is blocked by firewall

### 2. Enhanced Error Handling
**File**: `/js/analyze-transactions-api.js`
- Added better error messages when backend is unavailable
- Provides clear information about what might be wrong

### 3. Created Diagnostic Tool
**File**: `/test-analyze-api.html`
- Tests API connectivity
- Verifies analyze endpoint functionality
- Helps diagnose configuration issues

## What Needs to Be Done on Server

### 1. Configure Nginx
Add to nginx configuration (usually `/etc/nginx/sites-available/default`):

```nginx
location /api/ {
    proxy_pass http://localhost:5000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 2. Ensure Backend is Running
```bash
# Check service status
sudo systemctl status backend

# If not running, start it
sudo systemctl start backend

# Enable auto-start
sudo systemctl enable backend

# Check logs
sudo journalctl -u backend -f
```

### 3. Verify Backend Dependencies
The backend requires these Python packages for the analyze endpoint:
- pandas
- PyPDF2
- tabula-py
- pdfplumber

```bash
# Install if missing
cd /home/ubuntu/backend
source venv/bin/activate
pip install pandas PyPDF2 tabula-py pdfplumber
```

## Testing

1. Open https://bankcsvconverter.com/test-analyze-api.html
2. Click "Check API URL" to verify configuration
3. Click "Test Health Endpoint" to check backend connectivity
4. Upload a PDF and click "Test Analyze" to verify the full flow

## Temporary Workaround

If the backend cannot be fixed immediately, you could:
1. Use client-side PDF parsing (less accurate)
2. Show a maintenance message
3. Redirect to the main converter tool which might still work

## Backend Architecture

The analyze-transactions feature uses:
- **Frontend**: `/analyze-transactions.html` with `/js/analyze-transactions-api.js`
- **Backend**: `/api/analyze-transactions` endpoint in `backend/api/analyze_transactions.py`
- **Parser**: `backend/universal_parser.py` with bank-specific parsers

The backend extracts transactions from PDFs and provides:
- Transaction categorization
- Spending analysis
- Monthly breakdowns
- Financial insights
- Alerts and recommendations