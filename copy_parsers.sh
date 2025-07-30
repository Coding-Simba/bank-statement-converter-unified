#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Copying bank parsers to production server..."

# Copy individual parsers
for parser in westpac_parser.py citizens_parser.py suntrust_parser.py woodforest_parser.py \
             walmart_parser.py green_dot_parser.py becu_parser.py; do
    if [ -f "backend/parsers/$parser" ]; then
        echo "Copying $parser..."
        scp -i "$KEY_PATH" "backend/parsers/$parser" "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/"
    fi
done

# Copy the fixed universal parser
echo "Copying fixed universal parser..."
scp -i "$KEY_PATH" universal_parser_enhanced_fixed.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/universal_parser_enhanced.py"

# Restart service
echo "Restarting service..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'sudo systemctl restart bankconverter'

echo "✅ Done\!"

