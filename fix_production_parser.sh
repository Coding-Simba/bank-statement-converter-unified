#!/bin/bash

# Fix Production Parser to Use Bank-Specific Parsers

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Production Parser"
echo "========================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking current parser structure..."
echo "Universal parser enhanced imports:"
grep -n "from.*import\|parse.*pdf" universal_parser_enhanced.py | head -20

echo -e "\n2. Backing up current enhanced parser..."
cp universal_parser_enhanced.py universal_parser_enhanced.py.backup_$(date +%s)

echo -e "\n3. Creating new enhanced parser that uses bank-specific parsers..."
cat > universal_parser_enhanced.py << 'PARSER'
"""Enhanced Universal PDF Parser with Bank-Specific Parser Support"""

import os
import sys
import logging
from typing import List, Dict, Optional, Any
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import bank-specific parsers
try:
    from westpac_parser import parse_westpac
    WESTPAC_PARSER_AVAILABLE = True
    logger.info("Westpac parser loaded")
except ImportError as e:
    logger.warning(f"Westpac parser not available: {e}")
    WESTPAC_PARSER_AVAILABLE = False

try:
    from citizens_parser import parse_citizens
    CITIZENS_PARSER_AVAILABLE = True
    logger.info("Citizens parser loaded")
except ImportError as e:
    logger.warning(f"Citizens parser not available: {e}")
    CITIZENS_PARSER_AVAILABLE = False

try:
    from suntrust_parser import parse_suntrust
    SUNTRUST_PARSER_AVAILABLE = True
    logger.info("SunTrust parser loaded")
except ImportError as e:
    logger.warning(f"SunTrust parser not available: {e}")
    SUNTRUST_PARSER_AVAILABLE = False

try:
    from woodforest_parser import parse_woodforest
    WOODFOREST_PARSER_AVAILABLE = True
    logger.info("Woodforest parser loaded")
except ImportError as e:
    logger.warning(f"Woodforest parser not available: {e}")
    WOODFOREST_PARSER_AVAILABLE = False

try:
    from universal_parser import parse_universal_pdf as fallback_parser
    FALLBACK_PARSER_AVAILABLE = True
    logger.info("Fallback parser loaded")
except ImportError as e:
    logger.warning(f"Fallback parser not available: {e}")
    FALLBACK_PARSER_AVAILABLE = False

# Import other specific parsers
parser_modules = [
    'becu_parser', 'citizens_parser', 'commonwealth_parser', 'discover_parser',
    'green_dot_parser', 'lloyds_parser', 'metro_parser', 'nationwide_parser',
    'netspend_parser', 'paypal_parser', 'pnc_parser', 'rabobank_parser',
    'scotiabank_parser', 'suntrust_parser', 'walmart_parser', 'wellsfargo_parser'
]

available_parsers = {}

for module in parser_modules:
    try:
        parser_module = __import__(module)
        parser_func_name = f"parse_{module.replace('_parser', '')}"
        if hasattr(parser_module, parser_func_name):
            available_parsers[module.replace('_parser', '')] = getattr(parser_module, parser_func_name)
            logger.info(f"Loaded parser: {module}")
    except Exception as e:
        logger.debug(f"Could not load {module}: {e}")

def detect_bank_from_pdf(pdf_path: str) -> Optional[str]:
    """Detect bank from PDF content"""
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            # Check first few pages for bank identification
            text = ""
            for i in range(min(2, len(pdf.pages))):
                page_text = pdf.pages[i].extract_text() or ""
                text += page_text.lower()
            
            # Bank detection patterns
            bank_patterns = {
                'westpac': ['westpac', 'banking corporation'],
                'citizens': ['citizens bank', 'citizens financial'],
                'suntrust': ['suntrust', 'truist'],
                'woodforest': ['woodforest', 'woodforest national'],
                'commonwealth': ['commonwealth bank', 'commbank'],
                'wellsfargo': ['wells fargo', 'wellsfargo'],
                'chase': ['chase bank', 'jpmorgan chase'],
                'bank_of_america': ['bank of america', 'bofa'],
                'pnc': ['pnc bank', 'pnc financial'],
                'discover': ['discover bank', 'discover card'],
                'becu': ['becu', 'boeing employees'],
                'paypal': ['paypal', 'paypal credit'],
                'walmart': ['walmart', 'green dot'],
                'green_dot': ['green dot bank', 'greendot'],
                'netspend': ['netspend', 'metabank'],
                'lloyds': ['lloyds bank', 'lloyds tsb'],
                'metro': ['metro bank'],
                'nationwide': ['nationwide', 'nationwide building society'],
                'scotiabank': ['scotiabank', 'bank of nova scotia'],
                'rabobank': ['rabobank', 'rabobank nederland']
            }
            
            for bank, patterns in bank_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        logger.info(f"Detected bank: {bank}")
                        return bank
            
            logger.info("No specific bank detected")
            return None
            
    except Exception as e:
        logger.error(f"Error detecting bank: {e}")
        return None

def parse_universal_pdf_enhanced(pdf_path: str) -> pd.DataFrame:
    """Enhanced parser that uses bank-specific parsers when available"""
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Detect bank type
    bank_type = detect_bank_from_pdf(pdf_path)
    
    # Try bank-specific parser first
    if bank_type:
        # Check for specific parser
        if bank_type in available_parsers:
            try:
                logger.info(f"Using {bank_type} specific parser")
                result = available_parsers[bank_type](pdf_path)
                if result is not None and not result.empty:
                    logger.info(f"Successfully parsed with {bank_type} parser: {len(result)} transactions")
                    return result
            except Exception as e:
                logger.error(f"Error with {bank_type} parser: {e}")
        
        # Check individual parser availability
        if bank_type == 'westpac' and WESTPAC_PARSER_AVAILABLE:
            try:
                logger.info("Using Westpac specific parser")
                result = parse_westpac(pdf_path)
                if result is not None and not result.empty:
                    logger.info(f"Successfully parsed with Westpac parser: {len(result)} transactions")
                    return result
            except Exception as e:
                logger.error(f"Error with Westpac parser: {e}")
        
        elif bank_type == 'citizens' and CITIZENS_PARSER_AVAILABLE:
            try:
                logger.info("Using Citizens specific parser")
                result = parse_citizens(pdf_path)
                if result is not None and not result.empty:
                    logger.info(f"Successfully parsed with Citizens parser: {len(result)} transactions")
                    return result
            except Exception as e:
                logger.error(f"Error with Citizens parser: {e}")
        
        elif bank_type == 'suntrust' and SUNTRUST_PARSER_AVAILABLE:
            try:
                logger.info("Using SunTrust specific parser")
                result = parse_suntrust(pdf_path)
                if result is not None and not result.empty:
                    logger.info(f"Successfully parsed with SunTrust parser: {len(result)} transactions")
                    return result
            except Exception as e:
                logger.error(f"Error with SunTrust parser: {e}")
        
        elif bank_type == 'woodforest' and WOODFOREST_PARSER_AVAILABLE:
            try:
                logger.info("Using Woodforest specific parser")
                result = parse_woodforest(pdf_path)
                if result is not None and not result.empty:
                    logger.info(f"Successfully parsed with Woodforest parser: {len(result)} transactions")
                    return result
            except Exception as e:
                logger.error(f"Error with Woodforest parser: {e}")
    
    # Fallback to universal parser
    if FALLBACK_PARSER_AVAILABLE:
        try:
            logger.info("Using fallback universal parser")
            result = fallback_parser(pdf_path)
            if result is not None and not result.empty:
                logger.info(f"Parsed with fallback parser: {len(result)} transactions")
                return result
        except Exception as e:
            logger.error(f"Error with fallback parser: {e}")
    
    # Last resort - basic extraction
    logger.warning("All parsers failed, using basic extraction")
    return pd.DataFrame({
        'Date': [datetime.now().strftime('%Y-%m-%d')],
        'Description': ['Failed to parse PDF - please try manual entry'],
        'Amount': [0.00],
        'Balance': [0.00]
    })

# For backward compatibility
parse_enhanced = parse_universal_pdf_enhanced

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_universal_pdf_enhanced(sys.argv[1])
        print(result)
PARSER

echo -e "\n4. Testing the new parser..."
python3 -c "
from universal_parser_enhanced import parse_universal_pdf_enhanced
print('Enhanced parser loaded successfully')
"

echo -e "\n5. Restarting backend service..."
sudo systemctl restart bankconverter

echo -e "\n6. Testing with Westpac PDF..."
# Create test script
cat > test_parser.py << 'TEST'
import sys
sys.path.insert(0, '/home/ubuntu/bank-statement-converter/backend')
from universal_parser_enhanced import parse_universal_pdf_enhanced

# Test with uploaded Westpac PDF
pdf_path = '/home/ubuntu/bank-statement-converter/uploads/b5e5ad07-6170-416e-9044-4e64c87655fe.pdf'
try:
    result = parse_universal_pdf_enhanced(pdf_path)
    print(f"Parsed {len(result)} transactions")
    print("\nFirst 5 transactions:")
    print(result.head())
    print("\nDate values:")
    print(result['Date'].unique()[:5])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
TEST

python3 test_parser.py

echo -e "\n✅ Parser updated! Testing complete."

EOF