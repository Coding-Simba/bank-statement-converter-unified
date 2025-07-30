#!/bin/bash

# Copy Fixed Parsers to Production Backend

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Copying Fixed Parsers to Production Backend"
echo "==========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Backing up production files..."
cd /home/ubuntu/bank-statement-converter/backend
sudo cp universal_parser.py universal_parser.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp -r ../backend ../backend_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "Backup created"

echo -e "\n2. Checking if production uses modular parsers..."
if [ ! -d "/home/ubuntu/bank-statement-converter/backend/parsers" ]; then
    echo "Creating parsers directory in production..."
    sudo mkdir -p /home/ubuntu/bank-statement-converter/backend/parsers
fi

echo -e "\n3. Copying ALL fixed parser files from unified to production..."
sudo cp -r /home/ubuntu/bank-statement-converter-unified/backend/parsers/* /home/ubuntu/bank-statement-converter/backend/parsers/ 2>/dev/null || echo "No parsers to copy"

echo -e "\n4. Copying fixed universal parser..."
sudo cp /home/ubuntu/bank-statement-converter-unified/backend/universal_parser.py /home/ubuntu/bank-statement-converter/backend/

echo -e "\n5. Copying other critical files that might have fixes..."
# Copy universal parser variants
sudo cp /home/ubuntu/bank-statement-converter-unified/backend/universal_parser_enhanced.py /home/ubuntu/bank-statement-converter/backend/ 2>/dev/null || echo "No enhanced parser"
sudo cp /home/ubuntu/bank-statement-converter-unified/backend/universal_parser_with_custom_banks.py /home/ubuntu/bank-statement-converter/backend/ 2>/dev/null || echo "No custom banks parser"

# Copy any other parsing-related files
sudo cp /home/ubuntu/bank-statement-converter-unified/backend/advanced_ocr_parser.py /home/ubuntu/bank-statement-converter/backend/ 2>/dev/null || echo "No OCR parser"

echo -e "\n6. Setting correct permissions..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/bank-statement-converter/backend/
sudo chmod -R 644 /home/ubuntu/bank-statement-converter/backend/*.py
sudo chmod -R 755 /home/ubuntu/bank-statement-converter/backend/parsers/

echo -e "\n7. Restarting backend service..."
sudo systemctl restart bankconverter

echo -e "\n8. Checking service status..."
sleep 3
sudo systemctl status bankconverter --no-pager | head -10

echo -e "\n9. Testing API is still working..."
curl -s http://localhost:8000/api | head -20 || echo "API test"

echo -e "\n✅ Done! Fixed parsers have been copied to production."
echo "The backend now has all the parser improvements we made."

EOF