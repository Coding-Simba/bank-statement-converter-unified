#!/bin/bash
# Run these commands on your Lightsail instance

echo "=== Starting Bank Statement Converter Setup ==="

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "2. Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y nginx git curl
sudo apt install -y tesseract-ocr poppler-utils
sudo apt install -y build-essential libpoppler-cpp-dev

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
mkdir -p backend uploads failed_pdfs data frontend/js frontend/css

# Create requirements file
echo "5. Creating requirements file..."
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

echo "Setup complete! Now you need to upload your code files."