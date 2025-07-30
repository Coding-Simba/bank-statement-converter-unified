#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"

echo "Fixing parser initialization issue..."

ssh -i "$KEY_PATH" ubuntu@$SERVER_IP << 'SSHEOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "Adding debug logging to universal parser..."

# Add debug logging
cat >> universal_parser_enhanced.py << 'PYTHON'

# Debug: Log available parsers on module load
logger.info(f"Module loaded with parsers: {list(available_parsers.keys())}")
PYTHON

echo -e "\nAlso checking if parsers are being loaded lazily..."

# Check the import section
grep -A 5 "available_parsers\[bank\]" universal_parser_enhanced.py

echo -e "\nRestarting service with debug..."
sudo systemctl restart bankconverter

echo "Done\!"

SSHEOF
