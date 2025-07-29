# AWS Server Fix Summary

## Root Cause of Daily Inaccessibility

Your server becomes inaccessible because:

1. **Multiple Conflicting Backend Services** - You have 3 different backend services running:
   - `bank-converter-backend.service` 
   - `bankconverter.service`
   - `bankcsv-api.service`
   
   These compete for resources and ports, causing conflicts.

2. **Import/Path Issues** - The backend has Python import errors preventing it from starting properly.

3. **No Resource Monitoring** - Without monitoring, issues accumulate until the server becomes unresponsive.

## What I've Done

✅ **Added 2GB Swap Space** - Prevents memory exhaustion
✅ **Set Up Automatic Cleanup** - Deletes old files daily
✅ **Configured Health Monitoring** - Checks every 5 minutes
✅ **Set Up Log Rotation** - Prevents disk fill
✅ **Added Service Memory Limits** - Prevents runaway processes
✅ **Disabled Duplicate Services** - Removed conflicting backends

## What Still Needs Fixing

The main backend service has an import error. To fix this when you can SSH in:

```bash
# SSH into server
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83

# Fix the Python path issue
cd /home/ubuntu/bank-statement-converter-unified
export PYTHONPATH=/home/ubuntu/bank-statement-converter-unified

# Test if backend runs
cd backend
python3 -c "import sys; sys.path.insert(0, '..'); from backend.main import app; print('Import successful')"

# If that works, update the service file
sudo nano /etc/systemd/system/bank-converter-backend.service
```

Replace with:
```ini
[Unit]
Description=Bank Statement Converter Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter-unified
Environment="PYTHONPATH=/home/ubuntu/bank-statement-converter-unified"
ExecStart=/usr/bin/python3 -m backend.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart bank-converter-backend
```

## Why Your 2GB Server Has Issues

Even with 2GB RAM, having multiple backend services running is problematic:
- Each Python process uses 150-200MB
- 3 services × 200MB = 600MB just for backends
- Plus nginx, system processes, etc.

With the fixes applied and only one backend service, your server should be stable.

## Monitor Your Server

Check the health monitor log:
```bash
tail -f /home/ubuntu/health-monitor.log
```

The monitoring script will automatically restart services if they fail.