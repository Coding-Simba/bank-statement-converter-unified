# BankCSV Backend Deployment Guide

## Quick Start

1. **Copy deployment files to server:**
   ```bash
   scp -r backend/deploy ubuntu@3.235.19.83:/home/ubuntu/
   scp -r backend ubuntu@3.235.19.83:/home/ubuntu/
   ```

2. **SSH into server and run setup:**
   ```bash
   ssh ubuntu@3.235.19.83
   sudo bash /home/ubuntu/deploy/setup-server.sh
   ```

3. **Configure OAuth credentials:**
   ```bash
   sudo nano /home/bankcsv/backend/.env
   # Add your Google and Microsoft OAuth credentials
   ```

4. **Check status:**
   ```bash
   sudo bash /home/ubuntu/deploy/check-server-status.sh
   ```

## Manual Deployment Steps

If the automated script doesn't work, follow these manual steps:

### 1. Install Backend Code

```bash
# Create directories
sudo mkdir -p /home/bankcsv/backend
sudo cp -r /home/ubuntu/backend/* /home/bankcsv/backend/

# Create virtual environment
cd /home/bankcsv/backend
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt
```

### 2. Configure Environment

Create `/home/bankcsv/backend/.env`:
```env
DATABASE_URL=sqlite:///./bank_statements.db
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

APP_NAME=BankCSV Converter
APP_URL=https://bankcsvconverter.com
FRONTEND_URL=https://bankcsvconverter.com
```

### 3. Create Systemd Service

Create `/etc/systemd/system/bankcsv-backend.service`:
```ini
[Unit]
Description=BankCSV Converter Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/home/bankcsv/backend
ExecStart=/home/bankcsv/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5000
Restart=always
Environment="PATH=/home/bankcsv/backend/venv/bin"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bankcsv-backend
sudo systemctl start bankcsv-backend
```

### 4. Configure Nginx

Add to your nginx site configuration:
```nginx
# API proxy
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
    client_max_body_size 50M;
}

# Health check
location /health {
    proxy_pass http://localhost:5000/health;
}
```

Reload nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Testing

1. **Test backend directly:**
   ```bash
   curl http://localhost:5000/health
   ```

2. **Test through nginx:**
   ```bash
   curl https://bankcsvconverter.com/api/health
   ```

3. **Test analyze endpoint:**
   Open https://bankcsvconverter.com/test-analyze-api.html

## Troubleshooting

### Backend not starting
```bash
# Check logs
sudo journalctl -u bankcsv-backend -n 100

# Run manually to see errors
cd /home/bankcsv/backend
sudo -u www-data ./venv/bin/python main.py
```

### 502 Bad Gateway
- Backend is not running
- Check if port 5000 is in use: `sudo lsof -i :5000`
- Restart backend: `sudo systemctl restart bankcsv-backend`

### 404 on API endpoints
- Nginx not configured properly
- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`

### PDF parsing fails
Install system dependencies:
```bash
sudo apt install -y poppler-utils tesseract-ocr default-jre
```

## Monitoring

### View logs
```bash
# Backend logs
sudo journalctl -u bankcsv-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check service status
```bash
sudo systemctl status bankcsv-backend
sudo systemctl status nginx
```

## Security Notes

1. Keep `.env` file secure (chmod 600)
2. Use strong JWT secret key
3. Configure firewall to block port 5000 from external access
4. Regular security updates: `sudo apt update && sudo apt upgrade`
5. Monitor logs for suspicious activity

## OAuth Setup

### Google OAuth
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - https://bankcsvconverter.com/api/auth/google/callback
6. Copy client ID and secret to .env

### Microsoft OAuth
1. Go to https://portal.azure.com/
2. Register new application
3. Add redirect URI:
   - https://bankcsvconverter.com/api/auth/microsoft/callback
4. Create client secret
5. Copy application ID and secret to .env