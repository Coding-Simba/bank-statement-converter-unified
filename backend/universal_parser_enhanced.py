#!/usr/bin/env python3
"""
Enhanced Universal PDF Parser
Primary strategy: Use pdfplumber for modern PDFs, OCR for scanned PDFs
"""
import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pdfplumber
from PyPDF2 import PdfReader

# Import other parsers
from pdfplumber_parser import parse_with_pdfplumber
from camelot_parser import parse_with_camelot
from ocr_parser import parse_scanned_pdf
from accurate_column_parser import parse_accurate_columns
from fixed_column_parser import parse_fixed_column_layout
# Removed dummy parsers - they contained hard-coded transactions
from rabobank_parser import parse_rabobank_pdf
from woodforest_parser_enhanced import parse_woodforest

# Import custom bank parsers
from parsers.anz_parser import ANZParser
from parsers.becu_parser import BECUParser
from parsers.citizens_parser import CitizensParser
from parsers.commonwealth_parser import CommonwealthParser
from parsers.discover_parser import DiscoverParser
from parsers.green_dot_parser import GreenDotParser
from parsers.lloyds_parser import LloydsParser
from parsers.metro_parser import MetroParser
from parsers.nationwide_parser import NationwideParser
from parsers.netspend_parser import NetspendParser
from parsers.paypal_parser import PaypalParser
from parsers.scotiabank_parser import ScotiabankParser
from parsers.suntrust_parser import SuntrustParser
from parsers.walmart_parser import WalmartParser
from parsers.westpac_parser import WestpacParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bank detection patterns
BANK_PATTERNS = {
    'anz': {
        'filename_patterns': ['anz'],
        'content_patterns': ['anz', 'australia and new zealand banking']
    },
    'becu': {
        'filename_patterns': ['becu'],
        'content_patterns': ['becu', 'boeing employees', 'boeing employees credit union']
    },
    'citizens': {
        'filename_patterns': ['citizens'],
        'content_patterns': ['citizens bank', 'citizens financial']
    },
    'commonwealth': {
        'filename_patterns': ['commonwealth'],
        'content_patterns': ['commonwealth bank', 'commbank', 'cba']
    },
    'discover': {
        'filename_patterns': ['discover'],
        'content_patterns': ['discover bank', 'discover card', 'discover financial']
    },
    'green_dot': {
        'filename_patterns': ['green dot', 'greendot'],
        'content_patterns': ['green dot', 'greendot bank', 'green dot bank']
    },
    'lloyds': {
        'filename_patterns': ['lloyds'],
        'content_patterns': ['lloyds bank', 'lloyds banking group']
    },
    'metro': {
        'filename_patterns': ['metro'],
        'content_patterns': ['metro bank', 'metrobank']
    },
    'nationwide': {
        'filename_patterns': ['nationwide'],
        'content_patterns': ['nationwide', 'nationwide building society']
    },
    'netspend': {
        'filename_patterns': ['netspend'],
        'content_patterns': ['netspend', 'netspend corporation']
    },
    'paypal': {
        'filename_patterns': ['paypal'],
        'content_patterns': ['paypal', 'paypal account', 'paypal.com']
    },
    'scotiabank': {
        'filename_patterns': ['scotia'],
        'content_patterns': ['scotiabank', 'bank of nova scotia', 'scotia bank']
    },
    'suntrust': {
        'filename_patterns': ['suntrust'],
        'content_patterns': ['suntrust', 'suntrust bank', 'truist']
    },
    'walmart': {
        'filename_patterns': ['walmart'],
        'content_patterns': ['walmart moneycard', 'walmart money card', 'green dot bank']
    },
    'westpac': {
        'filename_patterns': ['westpac'],
        'content_patterns': ['westpac', 'westpac banking corporation']
    }
}

# Bank parser mapping
BANK_PARSERS = {
    'anz': ANZParser,
    'becu': BECUParser,
    'citizens': CitizensParser,
    'commonwealth': CommonwealthParser,
    'discover': DiscoverParser,
    'green_dot': GreenDotParser,
    'lloyds': LloydsParser,
    'metro': MetroParser,
    'nationwide': NationwideParser,
    'netspend': NetspendParser,
    'paypal': PaypalParser,
    'scotiabank': ScotiabankParser,
    'suntrust': SuntrustParser,
    'walmart': WalmartParser,
    'westpac': WestpacParser
}

def is_valid_date(date_str: str) -> bool:
    """
    Validate if a string is a legitimate date (not a phone number)
    """
    if not date_str:
        return False
    
    # Common phone number patterns to reject
    phone_patterns = [
        r'^1-\d{2,3}$',  # 1-80, 1-800, etc.
        r'^\d{2}-\d{2}$',  # 16-15, 82-50 (likely not dates)
        r'^1-\d{3}-\d{3}-\d{4}$',  # Full phone numbers
    ]
    
    for pattern in phone_patterns:
        if re.match(pattern, date_str):
            return False
    
    # Check if it looks like a real date
    date_patterns = [
        r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # MM/DD/YYYY or MM-DD-YYYY
        r'^\d{1,2}[/-]\d{1,2}$',  # MM/DD or MM-DD (no year)
        r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',  # YYYY-MM-DD
        r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}$',  # DD MMM YYYY
        r'^[A-Za-z]{3}\s+\d{1,2},?\s+\d{2,4}$',  # MMM DD, YYYY
    ]
    
    return any(re.match(pattern, date_str) for pattern in date_patterns)

def is_realistic_amount(amount: float) -> bool:
    """
    Check if an amount is realistic for a bank transaction
    """
    # Most bank transactions are under $1 million
    return -1000000 < amount < 1000000

def clean_transactions(transactions: List[Dict]) -> List[Dict]:
    """
    Clean and validate transactions
    """
    cleaned = []
    
    for trans in transactions:
        # Skip if no valid date
        date_str = trans.get('date_string', '')
        if not is_valid_date(date_str):
            continue
        
        # Skip if unrealistic amount
        amount = trans.get('amount', 0)
        if not is_realistic_amount(amount):
            continue
        
        # Skip if no description
        desc = trans.get('description', '').strip()
        if not desc or len(desc) < 3:
            continue
        
        cleaned.append(trans)
    
    return cleaned

def detect_bank(pdf_path: str) -> Optional[str]:
    """Detect which bank the PDF is from"""
    filename_lower = os.path.basename(pdf_path).lower()
    
    # Check filename first - this takes priority
    for bank, patterns in BANK_PATTERNS.items():
        for pattern in patterns['filename_patterns']:
            if pattern in filename_lower:
                logger.info(f"Detected {bank} from filename")
                return bank
    
    # Check content with more specific matching
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first few pages
            text = ""
            for i in range(min(3, len(pdf.pages))):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text += page_text.lower() + "\n"
            
            # Special check for Woodforest first (since it might mention PayPal in transactions)
            if 'woodforest' in text or 'woodforest national bank' in text or 'wfnnb.com' in text:
                logger.info("Detected woodforest from content")
                return 'woodforest'
            
            # Check other content patterns
            for bank, patterns in BANK_PATTERNS.items():
                if bank == 'paypal':
                    # PayPal needs more specific detection to avoid false positives
                    if 'paypal account statement' in text or 'paypal balance' in text:
                        logger.info(f"Detected {bank} from content")
                        return bank
                else:
                    for pattern in patterns['content_patterns']:
                        if pattern in text:
                            logger.info(f"Detected {bank} from content")
                            return bank
    except Exception as e:
        logger.warning(f"Error detecting bank from content: {e}")
    
    return None

def is_scanned_pdf(pdf_path: str) -> bool:
    """
    Check if PDF is scanned/image-based
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first few pages
            total_chars = 0
            pages_checked = min(3, len(pdf.pages))
            
            for i in range(pages_checked):
                text = pdf.pages[i].extract_text()
                if text:
                    total_chars += len(text.strip())
            
            # If very little text, likely scanned
            avg_chars = total_chars / pages_checked
            return avg_chars < 100
    except:
        return False

def parse_universal_pdf_enhanced(pdf_path: str) -> List[Dict]:
    """
    Enhanced universal PDF parser with intelligent method selection
    """
    logger.info(f"Parsing PDF: {pdf_path}")
    all_transactions = []
    best_result = []
    
    # Step 1: Detect bank using the new detection system
    detected_bank = detect_bank(pdf_path)
    
    # Also check for legacy banks
    filename_lower = os.path.basename(pdf_path).lower()
    if not detected_bank:
        if 'rabo' in filename_lower or 'rabobank' in filename_lower:
            detected_bank = 'rabobank'
        # Removed dummy bank detection - contained hard-coded transactions
        elif 'woodforest' in filename_lower:
            detected_bank = 'woodforest'
        else:
            # Try to detect by content for legacy banks
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if reader.pages:
                        first_page_text = reader.pages[0].extract_text().lower()
                        if 'rabobank' in first_page_text or 'rekeningafschrift' in first_page_text:
                            detected_bank = 'rabobank'
                        # Removed dummy bank detection - contained hard-coded transactions
                        elif any(identifier in first_page_text for identifier in [
                            'woodforest', 
                            'woodforest national bank',
                            'wfnnb.com',
                            'member fdic'
                        ]) or (
                            ('checking' in first_page_text or 'savings' in first_page_text) and 
                            any(pattern in first_page_text for pattern in [
                                'summary of accounts',
                                'account summary', 
                                'daily balance summary',
                                'daily closing balance'
                            ])
                        ):
                            detected_bank = 'woodforest'
            except:
                pass
    
    # Step 2: Use appropriate parser based on detected bank
    if detected_bank:
        # Legacy parsers
        if detected_bank == 'rabobank':
            logger.info("Detected Rabobank statement, using specialized parser")
            trans = parse_rabobank_pdf(pdf_path)
            if trans:
                return trans
        # Removed dummy parser - contained hard-coded transactions
        elif detected_bank == 'woodforest':
            logger.info("Detected Woodforest statement, using specialized parser")
            trans = parse_woodforest(pdf_path)
            if trans:
                return trans
        # New custom bank parsers
        elif detected_bank in BANK_PARSERS:
            logger.info(f"Detected {detected_bank} statement, using custom parser")
            parser_class = BANK_PARSERS[detected_bank]
            parser = parser_class()
            trans = parser.parse(pdf_path)
            if trans:
                return trans
    
    # Step 3: If no custom parser or it failed, try generic methods
    logger.info("No custom parser found or parsing failed, using generic methods")
    
    # Try pdfplumber first (works for most modern PDFs)
    try:
        logger.info("Trying pdfplumber...")
        trans = parse_with_pdfplumber(pdf_path)
        if trans:
            logger.info(f"Pdfplumber found {len(trans)} raw transactions")
            cleaned = clean_transactions(trans)
            if cleaned:
                logger.info(f"After cleaning: {len(cleaned)} valid transactions")
                return cleaned
            # Keep the raw result as fallback
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Pdfplumber failed: {e}")
    
    # If pdfplumber fails or finds nothing, check if it's scanned
    if is_scanned_pdf(pdf_path):
        logger.info("PDF appears to be scanned, using OCR")
        try:
            trans = parse_scanned_pdf(pdf_path)
            if trans:
                return clean_transactions(trans)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
    
    # Try Camelot for table-based PDFs
    try:
        logger.info("Trying Camelot for tables...")
        trans = parse_with_camelot(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            # Keep the raw result as fallback
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Camelot failed: {e}")
    
    # Try specialized parsers
    try:
        logger.info("Trying accurate column parser...")
        trans = parse_accurate_columns(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            # Keep the raw result as fallback
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Accurate column parser failed: {e}")
    
    try:
        logger.info("Trying fixed column parser...")
        trans = parse_fixed_column_layout(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            # Keep the raw result as fallback
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Fixed column parser failed: {e}")
    
    # Last resort - OCR even if not detected as scanned
    logger.info("Trying OCR as last resort...")
    try:
        # Try advanced OCR first
        try:
            from advanced_ocr_parser import parse_scanned_pdf_advanced
            trans = parse_scanned_pdf_advanced(pdf_path)
            logger.info(f"Advanced OCR found {len(trans)} transactions")
        except Exception as e:
            logger.warning(f"Advanced OCR failed: {e}, trying basic OCR")
            trans = parse_scanned_pdf(pdf_path)
        
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            # Keep the raw result as fallback
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Final OCR attempt failed: {e}")
    
    # Return best result if we have any
    if best_result:
        logger.info(f"Returning best result with {len(best_result)} transactions (may include invalid dates/amounts)")
        return best_result
    
    # No fallback to dummy parser - it contained hard-coded transactions
    logger.warning(f"No transactions extracted from {pdf_path}")
    
    return []

# For backward compatibility
parse_universal_pdf = parse_universal_pdf_enhanced