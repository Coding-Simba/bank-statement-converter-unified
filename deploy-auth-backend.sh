#!/bin/bash

# Deployment script for authentication backend
echo "🚀 Deploying authentication backend to production server..."

# Server details
SERVER="ubuntu@3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
REMOTE_DIR="/home/ubuntu/bank-statement-converter-unified"

# First, create a production configuration file
echo "📝 Creating production configuration..."
cat > backend/.env.production << EOF
# Database
DATABASE_URL=sqlite:///./production.db

# JWT Settings
JWT_SECRET_KEY=$(openssl rand -hex 32)

# OAuth Settings (to be configured)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Frontend URL
FRONTEND_URL=https://bankcsvconverter.com

# API URL
API_URL=https://bankcsvconverter.com
EOF

echo "📦 Copying backend files to server..."
# Copy the backend directory
scp -i "$KEY_PATH" -r backend "$SERVER:$REMOTE_DIR/"

# Copy frontend auth files
echo "📄 Copying frontend authentication files..."
scp -i "$KEY_PATH" js/auth.js "$SERVER:$REMOTE_DIR/js/"
scp -i "$KEY_PATH" js/dashboard.js "$SERVER:$REMOTE_DIR/js/"
scp -i "$KEY_PATH" css/auth.css "$SERVER:$REMOTE_DIR/css/"
scp -i "$KEY_PATH" css/dashboard.css "$SERVER:$REMOTE_DIR/css/"
scp -i "$KEY_PATH" signup.html "$SERVER:$REMOTE_DIR/"
scp -i "$KEY_PATH" login.html "$SERVER:$REMOTE_DIR/"
scp -i "$KEY_PATH" dashboard.html "$SERVER:$REMOTE_DIR/"
scp -i "$KEY_PATH" oauth-callback.html "$SERVER:$REMOTE_DIR/"

echo "🔧 Setting up backend on server..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter-unified/backend

# Install new dependencies
echo "Installing dependencies..."
pip3 install pydantic-settings httpx python-multipart

# Stop existing backend if running
echo "Stopping existing backend..."
sudo pkill -f "python.*main.py" || true

# Create systemd service for backend
echo "Creating systemd service..."
sudo tee /etc/systemd/system/bank-converter-backend.service > /dev/null << 'EOF'
[Unit]
Description=Bank Statement Converter Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter-unified/backend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/bank-statement-converter-unified/backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable bank-converter-backend
sudo systemctl start bank-converter-backend

# Update nginx configuration to proxy API requests
echo "Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    
    ssl_certificate /etc/letsencrypt/live/bankcsvconverter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bankcsvconverter.com/privkey.pem;
    
    root /home/ubuntu/bank-statement-converter-unified;
    index index.html;
    
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
    }
    
    # Static files
    location / {
        try_files $uri $uri/ =404;
    }
}
EOF

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Check service status
echo "Checking service status..."
sudo systemctl status bank-converter-backend --no-pager

echo "✅ Backend deployment complete!"
ENDSSH

echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Configure OAuth credentials in /home/ubuntu/bank-statement-converter-unified/backend/.env.production"
echo "2. Update frontend URLs to use production API (https://bankcsvconverter.com/api)"
echo "3. Test authentication at https://bankcsvconverter.com/signup.html"