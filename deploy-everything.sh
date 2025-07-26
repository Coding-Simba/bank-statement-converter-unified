#!/bin/bash
# Complete deployment script - runs from your local machine

# Get Lightsail IP from user
echo "Enter your Lightsail public IP address:"
read LIGHTSAIL_IP

if [ -z "$LIGHTSAIL_IP" ]; then
    echo "Error: IP address is required"
    exit 1
fi

SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

echo "🚀 Starting complete deployment to $LIGHTSAIL_IP"

# First, copy the setup script to the server
echo "📤 Copying setup script to server..."
cat > /tmp/remote-setup.sh << 'SETUP_SCRIPT'
#!/bin/bash
set -e

echo "=== Starting Bank Statement Converter Setup ==="

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "2. Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y nginx git curl
sudo apt install -y tesseract-ocr poppler-utils
sudo apt install -y build-essential libpoppler-cpp-dev pkg-config

# Install Java for Tabula
sudo apt install -y default-jre

# Create app directory
echo "3. Creating application directory..."
cd /home/ubuntu
rm -rf bank-statement-converter
mkdir -p bank-statement-converter
cd bank-statement-converter

# Create Python virtual environment
echo "4. Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p backend/api backend/models backend/utils backend/middleware
mkdir -p uploads failed_pdfs data
mkdir -p frontend/js frontend/css

# Install Python packages
echo "5. Installing Python dependencies..."
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
sqlalchemy==2.0.23
PyPDF2==3.0.1
pandas==2.1.3
python-dateutil==2.8.2
openpyxl==3.1.2
tabula-py==2.8.1
pdfplumber==0.10.3
pytesseract==0.3.10
opencv-python-headless==4.8.1.78
Pillow==10.1.0
gunicorn==21.2.0
numpy==1.26.4
EOF

pip install -r requirements.txt

# Install additional OCR requirements
pip install pdf2image

echo "✅ Python environment setup complete!"
SETUP_SCRIPT

# Copy and run setup script
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no /tmp/remote-setup.sh ubuntu@$LIGHTSAIL_IP:/tmp/
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@$LIGHTSAIL_IP "chmod +x /tmp/remote-setup.sh && /tmp/remote-setup.sh"

echo "📦 Uploading application files..."

# Create a tarball of the application
cd /Users/MAC/chrome/bank-statement-converter-unified
tar -czf /tmp/app.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='uploads/*' \
    --exclude='failed_pdfs/*' \
    backend frontend *.html *.css js requirements*.txt manage_failed_pdfs.py

# Upload and extract
scp -i "$SSH_KEY" /tmp/app.tar.gz ubuntu@$LIGHTSAIL_IP:/tmp/
ssh -i "$SSH_KEY" ubuntu@$LIGHTSAIL_IP << 'DEPLOY_COMMANDS'
cd /home/ubuntu/bank-statement-converter
tar -xzf /tmp/app.tar.gz
rm /tmp/app.tar.gz

# Move frontend files to correct location
mv *.html frontend/ 2>/dev/null || true
mv *.css frontend/css/ 2>/dev/null || true
cp -r js/* frontend/js/ 2>/dev/null || true
rm -rf js

# Ensure __init__.py files exist
touch backend/__init__.py
touch backend/api/__init__.py
touch backend/models/__init__.py
touch backend/utils/__init__.py
touch backend/middleware/__init__.py

# Set permissions
chmod -R 755 /home/ubuntu/bank-statement-converter
DEPLOY_COMMANDS

echo "🔧 Configuring Nginx..."
ssh -i "$SSH_KEY" ubuntu@$LIGHTSAIL_IP << 'NGINX_CONFIG'
sudo tee /etc/nginx/sites-available/bankconverter << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    # Frontend static files
    location / {
        root /home/ubuntu/bank-statement-converter/frontend;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/bankconverter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
NGINX_CONFIG

echo "🚀 Creating systemd service..."
ssh -i "$SSH_KEY" ubuntu@$LIGHTSAIL_IP << 'SERVICE_CONFIG'
sudo tee /etc/systemd/system/bankconverter.service << 'EOF'
[Unit]
Description=Bank Statement Converter API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter
Environment="PATH=/home/ubuntu/bank-statement-converter/venv/bin"
ExecStart=/home/ubuntu/bank-statement-converter/venv/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.main:app --bind 127.0.0.1:8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bankconverter
sudo systemctl start bankconverter
SERVICE_CONFIG

echo "🔥 Configuring firewall..."
ssh -i "$SSH_KEY" ubuntu@$LIGHTSAIL_IP << 'FIREWALL_CONFIG'
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable
FIREWALL_CONFIG

echo "✅ Checking service status..."
ssh -i "$SSH_KEY" ubuntu@$LIGHTSAIL_IP "sudo systemctl status bankconverter"

echo ""
echo "🎉 Deployment complete!"
echo "🌐 Your application is available at: http://$LIGHTSAIL_IP"
echo ""
echo "📋 Useful commands:"
echo "  View logs: ssh -i $SSH_KEY ubuntu@$LIGHTSAIL_IP 'sudo journalctl -u bankconverter -f'"
echo "  Restart: ssh -i $SSH_KEY ubuntu@$LIGHTSAIL_IP 'sudo systemctl restart bankconverter'"
echo "  Status: ssh -i $SSH_KEY ubuntu@$LIGHTSAIL_IP 'sudo systemctl status bankconverter'"