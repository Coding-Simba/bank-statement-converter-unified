#!/bin/bash
# AWS Lightsail Setup Script for Bank Statement Converter
# Run this after SSH into your Lightsail instance

echo "=== Starting Bank Statement Converter Setup ==="

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "2. Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y nginx git curl
sudo apt install -y tesseract-ocr poppler-utils  # For PDF processing
sudo apt install -y build-essential libpoppler-cpp-dev  # For pdftotext

# Create app directory
echo "3. Creating application directory..."
cd /home/ubuntu
mkdir -p bank-statement-converter
cd bank-statement-converter

# Create Python virtual environment
echo "4. Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p backend uploads failed_pdfs data

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
EOF

pip install -r requirements.txt

# Setup Nginx
echo "6. Configuring Nginx..."
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
}
EOF

sudo ln -sf /etc/nginx/sites-available/bankconverter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Create systemd service
echo "7. Creating systemd service..."
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

# Create upload script
echo "8. Creating deployment helper..."
cat > deploy.sh << 'EOF'
#!/bin/bash
# Helper script to upload your code

echo "Upload your code using SCP:"
echo "scp -r backend/* ubuntu@YOUR_IP:/home/ubuntu/bank-statement-converter/backend/"
echo "scp -r *.html *.css js/ ubuntu@YOUR_IP:/home/ubuntu/bank-statement-converter/frontend/"
echo ""
echo "Or use git:"
echo "cd /home/ubuntu/bank-statement-converter"
echo "git init"
echo "git remote add origin YOUR_GITHUB_REPO"
echo "git pull origin main"
EOF
chmod +x deploy.sh

# Enable and start service
echo "9. Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable bankconverter

# Setup firewall
echo "10. Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Create frontend directory
mkdir -p frontend/js

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Upload your code to the server"
echo "2. Start the service: sudo systemctl start bankconverter"
echo "3. Check status: sudo systemctl status bankconverter"
echo "4. View logs: sudo journalctl -u bankconverter -f"
echo ""
echo "Your instance IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""