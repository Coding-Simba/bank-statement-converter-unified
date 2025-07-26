#!/bin/bash
# Copy and paste these commands into your Lightsail SSH terminal

# 1. System setup
echo "=== Step 1: System Setup ==="
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev nginx git curl
sudo apt install -y tesseract-ocr poppler-utils build-essential libpoppler-cpp-dev pkg-config default-jre

# 2. Create application structure
echo "=== Step 2: Creating Application Structure ==="
cd /home/ubuntu
mkdir -p bank-statement-converter
cd bank-statement-converter
python3 -m venv venv
source venv/bin/activate

# Create all directories
mkdir -p backend/api backend/models backend/utils backend/middleware
mkdir -p uploads failed_pdfs data frontend/js frontend/css

# 3. Install Python dependencies
echo "=== Step 3: Installing Python Dependencies ==="
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
pdf2image==1.16.3
EOF

pip install -r requirements.txt

# 4. Create __init__.py files
touch backend/__init__.py backend/api/__init__.py backend/models/__init__.py backend/utils/__init__.py backend/middleware/__init__.py

echo "✅ Environment setup complete!"
echo "Now you need to upload your code files."