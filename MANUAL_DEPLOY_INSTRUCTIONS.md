# Manual Deployment Instructions

Since I cannot directly access your server, please follow these steps to deploy the backend:

## Quick Deployment Steps

### 1. Upload Backend Code

```bash
# From your local machine
cd /Users/MAC/chrome/bank-statement-converter-unified
scp -r backend ubuntu@3.235.19.83:/home/ubuntu/
scp test-analyze-api.html ubuntu@3.235.19.83:/home/ubuntu/
```

### 2. Upload Updated Frontend Files

```bash
# Upload the fixed JavaScript files
scp js/api-config.js ubuntu@3.235.19.83:/home/ubuntu/
scp js/analyze-transactions-api.js ubuntu@3.235.19.83:/home/ubuntu/
```

### 3. SSH to Server and Deploy

```bash
# Connect to server
ssh ubuntu@3.235.19.83

# Move frontend files to web root (adjust path if needed)
sudo cp /home/ubuntu/api-config.js /var/www/html/js/
sudo cp /home/ubuntu/analyze-transactions-api.js /var/www/html/js/
sudo cp /home/ubuntu/test-analyze-api.html /var/www/html/

# Run the quick fix script
cd /home/ubuntu/backend/deploy
sudo bash quick-fix-analyze.sh
```

### 4. Test the Deployment

Open these URLs in your browser:
- https://bankcsvconverter.com/test-analyze-api.html
- Click "Test Health Endpoint" - should show "API is accessible"
- Upload a PDF and test analyze functionality

## If Quick Fix Fails

### Manual Backend Setup:

```bash
# On the server
cd /home/ubuntu/backend

# Create Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pandas PyPDF2 tabula-py pdfplumber
pip install python-multipart sqlalchemy python-dotenv

# Create .env file
echo "DATABASE_URL=sqlite:///./bank_statements.db" > .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Run backend manually to test
python -m uvicorn main:app --host 127.0.0.1 --port 5000
```

### Configure Nginx:

```bash
# Edit nginx config
sudo nano /etc/nginx/sites-available/default

# Add this inside the server block:
location /api/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 50M;
}

# Save and test
sudo nginx -t
sudo systemctl reload nginx
```

### Create Service:

```bash
# Create systemd service
sudo nano /etc/systemd/system/bankcsv-api.service

# Add:
[Unit]
Description=BankCSV API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
ExecStart=/home/ubuntu/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target

# Save and start
sudo systemctl daemon-reload
sudo systemctl enable bankcsv-api
sudo systemctl start bankcsv-api
```

## Verify Everything Works

1. Check service: `sudo systemctl status bankcsv-api`
2. Check logs: `sudo journalctl -u bankcsv-api -f`
3. Test API: `curl http://localhost:5000/health`
4. Test through nginx: `curl https://bankcsvconverter.com/api/health`

The analyze-transactions feature should now work with real PDF parsing!