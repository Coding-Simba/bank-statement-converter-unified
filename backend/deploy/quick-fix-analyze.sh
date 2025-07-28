#!/bin/bash
# Quick fix script to get analyze-transactions working

echo "=== Quick Fix for Analyze Transactions ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# 1. Check if backend code exists
if [ ! -d "/home/ubuntu/backend" ]; then
    echo "✗ Backend code not found in /home/ubuntu/backend"
    echo "Please upload the backend code first"
    exit 1
fi

echo "✓ Backend code found"

# 2. Quick setup without creating new user
echo "Setting up backend in /home/ubuntu/backend..."
cd /home/ubuntu/backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Install minimal requirements for analyze endpoint
echo "Installing Python packages..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install fastapi uvicorn python-multipart aiofiles
./venv/bin/pip install sqlalchemy python-dotenv pydantic-settings
./venv/bin/pip install pandas PyPDF2 tabula-py pdfplumber
./venv/bin/pip install python-jose passlib email-validator

# 3. Create minimal .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DATABASE_URL=sqlite:///./bank_statements.db
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
EOF
fi

# 4. Create simple systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/bankcsv-api.service << EOF
[Unit]
Description=BankCSV API Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
Environment="PATH=/home/ubuntu/backend/venv/bin"
ExecStart=/home/ubuntu/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Start the service
echo "Starting backend service..."
systemctl daemon-reload
systemctl stop bankcsv-api 2>/dev/null || true
systemctl start bankcsv-api
systemctl enable bankcsv-api

# Wait for service to start
sleep 3

# 6. Check if service is running
if systemctl is-active --quiet bankcsv-api; then
    echo "✓ Backend service is running"
else
    echo "✗ Backend service failed to start"
    echo "Check logs: journalctl -u bankcsv-api -n 50"
    exit 1
fi

# 7. Add nginx proxy configuration
echo "Configuring nginx..."

# Find the nginx config file
NGINX_CONF=""
if [ -f "/etc/nginx/sites-available/default" ]; then
    NGINX_CONF="/etc/nginx/sites-available/default"
elif [ -f "/etc/nginx/sites-available/bankcsvconverter" ]; then
    NGINX_CONF="/etc/nginx/sites-available/bankcsvconverter"
elif [ -f "/etc/nginx/nginx.conf" ]; then
    NGINX_CONF="/etc/nginx/nginx.conf"
fi

if [ -z "$NGINX_CONF" ]; then
    echo "✗ Could not find nginx configuration file"
    echo "Please manually add the proxy configuration"
else
    # Check if proxy already configured
    if grep -q "location /api/" "$NGINX_CONF"; then
        echo "✓ Nginx proxy already configured"
    else
        echo "Adding proxy configuration to nginx..."
        # Create backup
        cp "$NGINX_CONF" "$NGINX_CONF.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Add proxy config before the last closing brace
        # This is a simplified approach - may need manual adjustment
        cat >> "$NGINX_CONF" << 'EOF'

    # API proxy for analyze-transactions
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
EOF
        echo "⚠ Nginx configuration modified - please review manually"
    fi
fi

# 8. Test and reload nginx
if nginx -t; then
    echo "✓ Nginx configuration is valid"
    systemctl reload nginx
    echo "✓ Nginx reloaded"
else
    echo "✗ Nginx configuration has errors"
    echo "Please fix manually and run: nginx -t && systemctl reload nginx"
fi

# 9. Test the API
echo ""
echo "Testing API endpoints..."
sleep 2

# Test health endpoint
if curl -s http://localhost:5000/health | grep -q "healthy"; then
    echo "✓ Backend API is responding locally"
else
    echo "✗ Backend API not responding"
fi

# Test through nginx
DOMAIN="bankcsvconverter.com"
if curl -s https://$DOMAIN/api/health 2>/dev/null | grep -q "healthy"; then
    echo "✓ API is accessible through nginx"
    echo ""
    echo "=== SUCCESS ==="
    echo "The analyze-transactions feature should now work!"
    echo "Test it at: https://$DOMAIN/analyze-transactions.html"
else
    echo "✗ API not accessible through nginx"
    echo "Check nginx error logs: tail -f /var/log/nginx/error.log"
fi

echo ""
echo "Useful commands:"
echo "- View backend logs: journalctl -u bankcsv-api -f"
echo "- Restart backend: systemctl restart bankcsv-api"
echo "- Check status: systemctl status bankcsv-api"