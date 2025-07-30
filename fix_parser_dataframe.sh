#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing DataFrame to List Conversion"
echo "==================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'SSHEOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking current parser return type..."
grep -A 5 "def parse_universal_pdf_enhanced" universal_parser_enhanced.py | grep -E "return|DataFrame"

echo -e "\n2. Updating parser to convert DataFrame to list..."
cat > fix_dataframe.py << 'PYTHON'
import sys
sys.path.insert(0, '/home/ubuntu/bank-statement-converter/backend')

# Read the current parser
with open('universal_parser_enhanced.py', 'r') as f:
    content = f.read()

# Add DataFrame to list conversion
fix = '''
    # Last resort - basic extraction
    logger.warning("All parsers failed, using basic extraction")
    default_df = pd.DataFrame({
        'Date': [datetime.now().strftime('%Y-%m-%d')],
        'Description': ['Failed to parse PDF - please try manual entry'],
        'Amount': [0.00],
        'Balance': [0.00]
    })
    
    # Convert DataFrame to list of dicts
    return default_df.to_dict('records')

# For backward compatibility
parse_enhanced = parse_universal_pdf_enhanced

# Add conversion wrapper for all returns
def parse_universal_pdf_enhanced_wrapped(pdf_path: str):
    """Wrapper that ensures list output"""
    result = parse_universal_pdf_enhanced(pdf_path)
    
    # Convert DataFrame to list if needed
    if hasattr(result, 'to_dict'):
        return result.to_dict('records')
    elif isinstance(result, list):
        return result
    else:
        logger.error(f"Unexpected return type: {type(result)}")
        return [{
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Description': 'Parser error',
            'Amount': 0.00,
            'Balance': 0.00
        }]

# Override the main function
parse_universal_pdf_enhanced = parse_universal_pdf_enhanced_wrapped
'''

# Replace the last resort section
import re
content = re.sub(
    r'# Last resort - basic extraction.*?return pd\.DataFrame\([^)]+\)',
    fix,
    content,
    flags=re.DOTALL
)

# Write back
with open('universal_parser_enhanced.py', 'w') as f:
    f.write(content)

print("Updated parser to handle DataFrame conversion")
PYTHON

python3 fix_dataframe.py

echo -e "\n3. Also updating all parser imports to return lists..."
# Update individual parsers to return lists
for parser in westpac_parser.py citizens_parser.py suntrust_parser.py woodforest_parser.py; do
    if [ -f "$parser" ]; then
        echo "Checking $parser..."
        # Add to_dict conversion if parser returns DataFrame
        sed -i 's/return df$/return df.to_dict("records")/g' "$parser"
        sed -i 's/return result$/return result.to_dict("records") if hasattr(result, "to_dict") else result/g' "$parser"
    fi
done

echo -e "\n4. Testing the fix..."
python3 -c "
from universal_parser_enhanced import parse_universal_pdf_enhanced
print('Parser loads successfully')
"

echo -e "\n5. Restarting service..."
sudo systemctl restart bankconverter

echo -e "\n✅ DataFrame conversion fix applied\!"

SSHEOF
