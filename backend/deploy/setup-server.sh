#!/bin/bash
# Server setup script for BankCSV Converter Backend
# Run this on your Ubuntu server as root or with sudo

set -e  # Exit on error

echo "=== BankCSV Converter Backend Setup ==="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
apt install -y python3 python3-pip python3-venv nginx git curl software-properties-common

# Install additional dependencies for PDF parsing
apt install -y poppler-utils tesseract-ocr libreoffice default-jre

# Create application user (if not exists)
if ! id -u bankcsv >/dev/null 2>&1; then
    echo "Creating bankcsv user..."
    useradd -m -s /bin/bash bankcsv
fi

# Create directories
echo "Creating directories..."
mkdir -p /var/www/bankcsvconverter
mkdir -p /home/bankcsv/backend
mkdir -p /home/bankcsv/logs

# Clone or update backend code
echo "Setting up backend code..."
if [ -d "/home/bankcsv/backend/.git" ]; then
    cd /home/bankcsv/backend
    git pull
else
    # You'll need to update this with your actual repository
    echo "Please manually copy your backend code to /home/bankcsv/backend"
    echo "Or update this script with your git repository URL"
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
cd /home/bankcsv/backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install wheel setuptools
pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt]
pip install python-multipart aiofiles python-dotenv email-validator
pip install authlib httpx itsdangerous pydantic-settings
pip install pandas PyPDF2 tabula-py pdfplumber
pip install pytesseract pdf2image camelot-py[cv]
pip install openpyxl xlsxwriter

# Create .env file if not exists
if [ ! -f "/home/bankcsv/backend/.env" ]; then
    echo "Creating .env file..."
    cat > /home/bankcsv/backend/.env << EOF
DATABASE_URL=sqlite:///./bank_statements.db
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OAuth settings (update with your actual credentials)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# App settings
APP_NAME=BankCSV Converter
APP_URL=https://bankcsvconverter.com
FRONTEND_URL=https://bankcsvconverter.com
EOF
    echo "Please update /home/bankcsv/backend/.env with your actual OAuth credentials"
fi

# Set permissions
echo "Setting permissions..."
chown -R bankcsv:bankcsv /home/bankcsv
chmod 600 /home/bankcsv/backend/.env

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/bankcsv-backend.service << EOF
[Unit]
Description=BankCSV Converter Backend
After=network.target

[Service]
Type=exec
User=bankcsv
Group=bankcsv
WorkingDirectory=/home/bankcsv/backend
Environment="PATH=/home/bankcsv/backend/venv/bin"
ExecStart=/home/bankcsv/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10
StandardOutput=append:/home/bankcsv/logs/backend.log
StandardError=append:/home/bankcsv/logs/backend.error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "Starting backend service..."
systemctl daemon-reload
systemctl enable bankcsv-backend
systemctl start bankcsv-backend

# Check service status
sleep 3
systemctl status bankcsv-backend --no-pager

# Set up nginx
echo "Configuring nginx..."
cp /home/bankcsv/backend/deploy/nginx-config.conf /etc/nginx/sites-available/bankcsvconverter
ln -sf /etc/nginx/sites-available/bankcsvconverter /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx

# Set up SSL with Let's Encrypt (optional)
echo "Setting up SSL..."
if ! [ -x "$(command -v certbot)" ]; then
    snap install core; snap refresh core
    snap install --classic certbot
    ln -s /snap/bin/certbot /usr/bin/certbot
fi

echo "To set up SSL, run:"
echo "certbot --nginx -d bankcsvconverter.com -d www.bankcsvconverter.com"

# Create update script
cat > /home/bankcsv/update-backend.sh << 'EOF'
#!/bin/bash
cd /home/bankcsv/backend
source venv/bin/activate
git pull
pip install -r requirements.txt
sudo systemctl restart bankcsv-backend
echo "Backend updated and restarted"
EOF
chmod +x /home/bankcsv/update-backend.sh
chown bankcsv:bankcsv /home/bankcsv/update-backend.sh

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy your backend code to /home/bankcsv/backend"
echo "2. Update /home/bankcsv/backend/.env with your OAuth credentials"
echo "3. Copy your frontend files to /var/www/bankcsvconverter"
echo "4. Run: certbot --nginx -d bankcsvconverter.com -d www.bankcsvconverter.com"
echo "5. Test the API at: https://bankcsvconverter.com/api/health"
echo ""
echo "Useful commands:"
echo "- Check backend logs: journalctl -u bankcsv-backend -f"
echo "- Restart backend: systemctl restart bankcsv-backend"
echo "- Update backend: /home/bankcsv/update-backend.sh"