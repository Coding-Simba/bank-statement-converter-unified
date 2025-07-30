#!/bin/bash

# Verify Production Parsers

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Verifying Production Parsers"
echo "============================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking parser imports in universal_parser.py:"
grep -A5 -B5 "westpac\|citizens\|suntrust\|woodforest" /home/ubuntu/bank-statement-converter/backend/universal_parser.py | head -20

echo -e "\n2. Checking if individual parsers exist:"
echo "Parsers in production backend:"
ls /home/ubuntu/bank-statement-converter/backend/parsers/*.py 2>/dev/null | wc -l
echo "Key parsers:"
ls /home/ubuntu/bank-statement-converter/backend/parsers/{westpac,woodforest,suntrust,citizens}_parser.py 2>/dev/null

echo -e "\n3. Comparing file sizes (to ensure copy worked):"
echo "Universal parser sizes:"
echo "Production: $(ls -la /home/ubuntu/bank-statement-converter/backend/universal_parser.py | awk '{print $5}') bytes"
echo "Unified: $(ls -la /home/ubuntu/bank-statement-converter-unified/backend/universal_parser.py | awk '{print $5}') bytes"

echo -e "\n4. Checking if parser has the westpac fix:"
grep -n "parse_westpac_date\|multiple transactions per line" /home/ubuntu/bank-statement-converter/backend/parsers/westpac_parser.py 2>/dev/null | head -5 || echo "Westpac parser not found or no fixes"

echo -e "\n5. Testing import in Python:"
cd /home/ubuntu/bank-statement-converter
/home/ubuntu/bank-statement-converter/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/home/ubuntu/bank-statement-converter/backend')
try:
    from universal_parser import UniversalPDFParser
    print('✅ Universal parser imports successfully')
    parser = UniversalPDFParser()
    print(f'✅ Parser instance created')
    # Check if it has bank-specific parsers
    import inspect
    methods = [m for m in dir(parser) if 'extract' in m and not m.startswith('_')]
    print(f'✅ Parser has {len(methods)} extract methods')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo -e "\n6. Recent backend logs (errors):"
tail -20 /home/ubuntu/bank-statement-converter/backend.log 2>/dev/null | grep -i error | tail -5

echo -e "\nDone checking. The parsers should now be working with all fixes."

EOF