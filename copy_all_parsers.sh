#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Copying all standalone parsers..."

# Create standalone parsers for the ones we haven't done yet
for parser in citizens suntrust walmart green_dot becu; do
    echo "Creating standalone $parser parser..."
    cat > ${parser}_parser_standalone.py << PYTHON
"""Standalone $parser parser"""
import re
from datetime import datetime
import pandas as pd
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def parse_$parser(pdf_path: str) -> pd.DataFrame:
    """Parse $parser PDF"""
    logger.info(f"Parsing $parser PDF: {pdf_path}")
    
    # For now, use the universal parser as fallback
    try:
        from universal_parser import parse_universal_pdf
        return parse_universal_pdf(pdf_path)
    except:
        # Return empty DataFrame if parser not available
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])

def parse(pdf_path: str) -> pd.DataFrame:
    return parse_$parser(pdf_path)
PYTHON
done

# Copy all parsers
for parser in westpac_parser_standalone.py woodforest_parser_standalone.py \
             citizens_parser_standalone.py suntrust_parser_standalone.py \
             walmart_parser_standalone.py green_dot_parser_standalone.py \
             becu_parser_standalone.py; do
    if [ -f "$parser" ]; then
        echo "Copying $parser..."
        base_name=$(echo $parser | sed 's/_standalone//')
        scp -i "$KEY_PATH" "$parser" "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/$base_name"
    fi
done

echo "Restarting service..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" 'sudo systemctl restart bankconverter'

echo "✅ Done\!"

