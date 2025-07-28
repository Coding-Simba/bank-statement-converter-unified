#!/bin/bash

cd /home/ubuntu/bank-statement-converter-unified/backend

# Install required dependencies
echo "Installing dependencies..."
pip3 install pydantic-settings httpx python-multipart passlib[bcrypt] python-jose[cryptography]

# Stop any existing backend process
echo "Stopping existing backend..."
sudo pkill -f "python.*main.py" || true

# Create systemd service
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

# Start the service
sudo systemctl daemon-reload
sudo systemctl enable bank-converter-backend
sudo systemctl start bank-converter-backend

# Update nginx configuration
echo "Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
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
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;
}
EOF

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Check service status
echo "Checking service status..."
sudo systemctl status bank-converter-backend --no-pager

# Create production env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating production .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./production.db

# JWT Settings - CHANGE THIS!
JWT_SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING

# OAuth Settings (to be configured)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# URLs
FRONTEND_URL=https://bankcsvconverter.com
API_URL=https://bankcsvconverter.com

# OAuth Redirect URIs
GOOGLE_REDIRECT_URI=https://bankcsvconverter.com/api/auth/google/callback
MICROSOFT_REDIRECT_URI=https://bankcsvconverter.com/api/auth/microsoft/callback
EOF
fi

echo "✅ Backend setup complete!"
echo ""
echo "⚠️  IMPORTANT: Edit /home/ubuntu/bank-statement-converter-unified/backend/.env to:"
echo "1. Set a secure JWT_SECRET_KEY"
echo "2. Add OAuth credentials when available"
echo ""
echo "📝 Test the API at: https://bankcsvconverter.com/api/"