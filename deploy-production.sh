#!/bin/bash

# Production Deployment Script for Bank Statement Converter
# Deploys to AWS Lightsail at 3.235.19.83

echo "🚀 Bank Statement Converter - Production Deployment"
echo "=================================================="
echo ""

# Configuration
SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"
DOMAIN="bankcsvconverter.com"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

echo "1. Preparing production files..."

# Update production nginx configuration
cat > backend/deploy/nginx-production.conf << 'EOF'
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    # SSL certificates (managed by Cloudflare)
    ssl_certificate /etc/ssl/certs/cloudflare.crt;
    ssl_certificate_key /etc/ssl/private/cloudflare.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend files
    root /home/ubuntu/bank-statement-converter;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # API proxy - legacy endpoints
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Cookie $http_cookie;
        proxy_cookie_domain localhost $host;
        proxy_cookie_path / /;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # V2 API proxy - unified authentication endpoints
    location /v2/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Cookie $http_cookie;
        proxy_cookie_domain localhost $host;
        proxy_cookie_path / /;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload limits
    client_max_body_size 50M;
}
EOF

echo -e "${GREEN}✓ Production nginx config created${NC}"

# Create deployment package
echo ""
echo "2. Creating deployment package..."

# Clean build directory
rm -rf deployment-build
mkdir -p deployment-build

# Copy backend files
echo "   Copying backend files..."
cp -r backend deployment-build/
rm -rf deployment-build/backend/venv
rm -rf deployment-build/backend/__pycache__
rm -rf deployment-build/backend/**/__pycache__
rm -rf deployment-build/backend/.pytest_cache

# Copy frontend files
echo "   Copying frontend files..."
mkdir -p deployment-build/frontend
cp -r *.html deployment-build/frontend/
cp -r js deployment-build/frontend/
cp -r css deployment-build/frontend/
cp -r images deployment-build/frontend/
cp -r fonts deployment-build/frontend/ 2>/dev/null || true

# Create deployment archive
echo "   Creating deployment archive..."
cd deployment-build
tar -czf ../bank-statement-deployment.tar.gz .
cd ..

echo -e "${GREEN}✓ Deployment package created${NC}"

# Deploy to server
echo ""
echo "3. Deploying to production server..."

# Upload deployment package
echo "   Uploading files..."
scp -i "$SSH_KEY" bank-statement-deployment.tar.gz "$SERVER_USER@$SERVER_IP:/tmp/"

# Deploy via SSH
echo "   Executing deployment..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

echo "   Extracting deployment package..."
cd /home/ubuntu
rm -rf bank-statement-converter-new
mkdir bank-statement-converter-new
cd bank-statement-converter-new
tar -xzf /tmp/bank-statement-deployment.tar.gz

echo "   Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "   Copying production environment..."
cp /home/ubuntu/bank-statement-converter/backend/.env.production .env

echo "   Initializing database..."
python -c "from models.database import init_db; init_db()"

echo "   Setting up frontend..."
cd ../frontend
cp -r * /home/ubuntu/bank-statement-converter-new/

echo "   Updating nginx configuration..."
sudo cp /home/ubuntu/bank-statement-converter-new/backend/deploy/nginx-production.conf /etc/nginx/sites-available/bankcsvconverter
sudo ln -sf /etc/nginx/sites-available/bankcsvconverter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "   Switching to new deployment..."
cd /home/ubuntu
rm -rf bank-statement-converter-old
mv bank-statement-converter bank-statement-converter-old || true
mv bank-statement-converter-new bank-statement-converter

echo "   Restarting backend service..."
sudo systemctl restart bank-statement-backend

echo "   Cleaning up..."
rm /tmp/bank-statement-deployment.tar.gz

echo "✓ Deployment complete!"
ENDSSH

echo -e "${GREEN}✓ Production deployment complete!${NC}"

# Clean up local files
rm -rf deployment-build
rm -f bank-statement-deployment.tar.gz

echo ""
echo "4. Deployment Summary:"
echo "   - Frontend: https://bankcsvconverter.com"
echo "   - Backend API: https://bankcsvconverter.com/api"
echo "   - V2 Auth API: https://bankcsvconverter.com/v2/api/auth"
echo ""
echo "Next: Running comprehensive tests with 20 parallel agents..."