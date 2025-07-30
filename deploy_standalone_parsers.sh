#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying standalone parsers..."
echo "==============================="

# Copy standalone parsers
echo "1. Copying Westpac parser..."
scp -i "$KEY_PATH" westpac_parser_standalone.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/westpac_parser.py"

echo "2. Copying Woodforest parser..."
scp -i "$KEY_PATH" woodforest_parser_standalone.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/woodforest_parser.py"

# Test parsers on server
echo -e "\n3. Testing parsers on server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'SSHEOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "Testing parser imports..."
python3 -c "
try:
    from westpac_parser import parse_westpac
    print('✅ Westpac parser imported successfully')
except Exception as e:
    print(f'❌ Westpac error: {e}')

try:
    from woodforest_parser import parse_woodforest
    print('✅ Woodforest parser imported successfully')
except Exception as e:
    print(f'❌ Woodforest error: {e}')

print('\nRestarting service...')
"

sudo systemctl restart bankconverter

echo "✅ Deployment complete\!"

SSHEOF
