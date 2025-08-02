# Deployment Guide - Authentication & Stripe System

## Prerequisites
- Ubuntu Server (20.04 or later)
- Python 3.8+
- PostgreSQL
- Nginx
- SSL Certificate (Let's Encrypt)

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual values
nano .env
```

### 3. Create systemd Service
```bash
sudo nano /etc/systemd/system/bankcsv-backend.service
```

Content:
```ini
[Unit]
Description=Bank CSV Converter Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
Environment="PATH=/home/ubuntu/backend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="FRONTEND_URL=https://bankcsvconverter.com"
EnvironmentFile=/home/ubuntu/backend/.env
ExecStart=/home/ubuntu/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Start Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable bankcsv-backend
sudo systemctl start bankcsv-backend
sudo systemctl status bankcsv-backend
```

## Frontend Deployment

### 1. Copy Files
```bash
# Copy all HTML files to web root
cp *.html /var/www/html/

# Copy JS files
cp -r js/ /var/www/html/js/

# Copy CSS files (if any)
cp -r css/ /var/www/html/css/
```

### 2. Update File Permissions
```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html
```

## Nginx Configuration

### 1. Create Site Configuration
```bash
sudo nano /etc/nginx/sites-available/bankcsvconverter
```

Content:
```nginx
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    ssl_certificate /etc/letsencrypt/live/bankcsvconverter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bankcsvconverter.com/privkey.pem;

    root /var/www/html;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # V2 API proxy (cookie auth)
    location /v2/api/ {
        proxy_pass http://localhost:5000/v2/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location / {
        try_files $uri $uri/ =404;
    }
}
```

### 2. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/bankcsvconverter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate Setup
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d bankcsvconverter.com -d www.bankcsvconverter.com
```

## Database Setup

### 1. Create Database
```sql
CREATE DATABASE bankcsv;
CREATE USER bankcsv WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bankcsv TO bankcsv;
```

### 2. Run Migrations
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## Stripe Configuration

### 1. Add Webhook Endpoint in Stripe Dashboard
- URL: `https://bankcsvconverter.com/api/stripe/webhook`
- Events: `checkout.session.completed`, `customer.subscription.*`

### 2. Update Price IDs in .env
- Get price IDs from Stripe Dashboard
- Update all STRIPE_*_PRICE_ID values

## Testing

### 1. Test Authentication
```bash
# Cookie auth
curl -X POST https://bankcsvconverter.com/v2/api/auth/csrf
curl -X POST https://bankcsvconverter.com/v2/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### 2. Test Stripe Integration
- Visit https://bankcsvconverter.com/pricing.html
- Click a buy button
- Should redirect to Stripe checkout

## Monitoring

### 1. Check Logs
```bash
# Backend logs
sudo journalctl -u bankcsv-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Check
```bash
curl https://bankcsvconverter.com/health
```

## Troubleshooting

### Auth Issues
1. Check JWT_SECRET_KEY is set
2. Verify CSRF middleware exclusions
3. Check cookie domain settings

### Stripe Issues
1. Verify all price IDs are correct
2. Check webhook secret is set
3. Ensure FRONTEND_URL is correct

### CORS Issues
1. Check allowed origins in main.py
2. Verify proxy headers in Nginx

## Backup & Recovery

### Daily Backup Script
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/bankcsv/$DATE"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump bankcsv > $BACKUP_DIR/database.sql

# Backup code
tar -czf $BACKUP_DIR/backend.tar.gz /home/ubuntu/backend
tar -czf $BACKUP_DIR/frontend.tar.gz /var/www/html

# Backup config
cp /home/ubuntu/backend/.env $BACKUP_DIR/
cp /etc/nginx/sites-available/bankcsvconverter $BACKUP_DIR/

# Keep only last 7 days
find /backup/bankcsv -type d -mtime +7 -exec rm -rf {} \;
```

## Security Checklist
- [ ] Change default JWT_SECRET_KEY
- [ ] Use strong database password
- [ ] Enable firewall (ufw)
- [ ] Regular security updates
- [ ] Monitor failed login attempts
- [ ] Implement rate limiting
- [ ] Regular backups
- [ ] SSL certificate auto-renewal