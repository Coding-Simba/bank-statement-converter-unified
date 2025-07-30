"""Enhanced Universal PDF Parser with Bank-Specific Parser Support"""

import os
import sys
import logging
from typing import List, Dict, Optional, Any, Union
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import bank-specific parsers
parser_imports = {
    'westpac': ('westpac_parser', 'parse_westpac'),
    'citizens': ('citizens_parser', 'parse_citizens'),
    'suntrust': ('suntrust_parser', 'parse_suntrust'),
    'woodforest': ('woodforest_parser', 'parse_woodforest'),
    'commonwealth': ('commonwealth_parser', 'parse_commonwealth'),
    'wellsfargo': ('wellsfargo_parser', 'parse_wellsfargo'),
    'chase': ('chase_parser', 'parse_chase'),
    'bank_of_america': ('bofa_parser', 'parse_bofa'),
    'pnc': ('pnc_parser', 'parse_pnc'),
    'discover': ('discover_parser', 'parse_discover'),
    'becu': ('becu_parser', 'parse_becu'),
    'paypal': ('paypal_parser', 'parse_paypal'),
    'walmart': ('walmart_parser', 'parse_walmart'),
    'green_dot': ('green_dot_parser', 'parse_green_dot'),
    'netspend': ('netspend_parser', 'parse_netspend'),
    'lloyds': ('lloyds_parser', 'parse_lloyds'),
    'metro': ('metro_parser', 'parse_metro'),
    'nationwide': ('nationwide_parser', 'parse_nationwide'),
    'scotiabank': ('scotiabank_parser', 'parse_scotiabank'),
    'rabobank': ('rabobank_parser', 'parse_rabobank')
}

# Try to import parsers
available_parsers = {}
for bank, (module_name, func_name) in parser_imports.items():
    try:
        module = __import__(module_name)
        if hasattr(module, func_name):
            available_parsers[bank] = getattr(module, func_name)
            logger.info(f"Loaded {bank} parser")
    except Exception as e:
        logger.debug(f"Could not load {bank} parser: {e}")

# Import fallback parser
try:
    from universal_parser import parse_universal_pdf as fallback_parser
    FALLBACK_PARSER_AVAILABLE = True
    logger.info("Fallback parser loaded")
except ImportError as e:
    logger.warning(f"Fallback parser not available: {e}")
    FALLBACK_PARSER_AVAILABLE = False

def to_transaction_list(result: Union[pd.DataFrame, List, None]) -> List[Dict]:
    """Convert parser result to list of transaction dictionaries"""
    if result is None:
        return []
    
    if isinstance(result, pd.DataFrame):
        if result.empty:
            return []
        # Convert DataFrame to list of dicts
        transactions = result.to_dict('records')
        # Ensure proper field names
        for trans in transactions:
            # Convert date to string if it's a datetime object (API expects 'date' lowercase)
            if 'Date' in trans:
                date_val = trans.pop('Date')
                if hasattr(date_val, 'strftime'):
                    trans['date'] = date_val.strftime('%Y-%m-%d')
                else:
                    trans['date'] = str(date_val)
            elif 'date' in trans and hasattr(trans['date'], 'strftime'):
                trans['date'] = trans['date'].strftime('%Y-%m-%d')
            
            # Ensure lowercase field names (API expects lowercase)
            if 'Description' in trans and 'description' not in trans:
                trans['description'] = trans.pop('Description')
            if 'Amount' in trans and 'amount' not in trans:
                trans['amount'] = trans.pop('Amount')
            if 'Balance' in trans and 'balance' not in trans:
                trans['balance'] = trans.pop('Balance')
            
            # Make sure we have lowercase versions
            if 'description' not in trans:
                trans['description'] = trans.get('Description', 'Unknown')
            if 'amount' not in trans:
                trans['amount'] = trans.get('Amount', 0.0)
            if 'balance' not in trans:
                trans['balance'] = trans.get('Balance', 0.0)
        
        return transactions
    
    elif isinstance(result, list):
        return result
    
    else:
        logger.error(f"Unexpected result type: {type(result)}")
        return []

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

def parse_universal_pdf_enhanced(pdf_path: str) -> List[Dict]:
    """Enhanced parser that uses bank-specific parsers when available"""
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Detect bank type
    bank_type = detect_bank_from_pdf(pdf_path)
    
    # Try bank-specific parser first
    if bank_type and bank_type in available_parsers:
        try:
            logger.info(f"Using {bank_type} specific parser")
            result = available_parsers[bank_type](pdf_path)
            transactions = to_transaction_list(result)
            if transactions:
                logger.info(f"Successfully parsed with {bank_type} parser: {len(transactions)} transactions")
                return transactions
        except Exception as e:
            logger.error(f"Error with {bank_type} parser: {e}")
    
    # Fallback to universal parser
    if FALLBACK_PARSER_AVAILABLE:
        try:
            logger.info("Using fallback universal parser")
            result = fallback_parser(pdf_path)
            transactions = to_transaction_list(result)
            if transactions:
                logger.info(f"Parsed with fallback parser: {len(transactions)} transactions")
                return transactions
        except Exception as e:
            logger.error(f"Error with fallback parser: {e}")
    
    # Last resort - return error transaction
    logger.warning("All parsers failed, returning error transaction")
    return [{
        'date': datetime.now().strftime('%Y-%m-%d'),
        'description': 'Failed to parse PDF - please try manual entry',
        'amount': 0.00,
        'balance': 0.00
    }]

# For backward compatibility
parse_enhanced = parse_universal_pdf_enhanced
parse_universal_pdf = parse_universal_pdf_enhanced

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_universal_pdf_enhanced(sys.argv[1])
        print(f"Parsed {len(result)} transactions")
        for trans in result[:5]:
            print(trans)