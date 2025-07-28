#!/usr/bin/env python3
"""
Enhanced Universal PDF Parser with Custom Bank Support
Integrates all custom bank parsers for accurate extraction
"""
import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pdfplumber
from PyPDF2 import PdfReader

# Import base parsers
from pdfplumber_parser import parse_with_pdfplumber
from camelot_parser import parse_with_camelot
from ocr_parser import parse_scanned_pdf
from accurate_column_parser import parse_accurate_columns
from fixed_column_parser import parse_fixed_column_layout
# Removed dummy parser - contained hard-coded transactions
from rabobank_parser import parse_rabobank_pdf
from woodforest_parser_enhanced import parse_woodforest

# Import custom bank parsers
from anz_parser import ANZParser
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
    },
    'rabobank': {
        'filename_patterns': ['rabo', 'rabobank'],
        'content_patterns': ['rabobank', 'rekeningafschrift']
    },
    'woodforest': {
        'filename_patterns': ['woodforest'],
        'content_patterns': ['woodforest', 'woodforest national bank', 'wfnnb.com']
    },
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

def detect_bank(pdf_path: str) -> Optional[str]:
    """Detect which bank the PDF is from"""
    filename_lower = os.path.basename(pdf_path).lower()
    
    # Check filename first
    for bank, patterns in BANK_PATTERNS.items():
        for pattern in patterns['filename_patterns']:
            if pattern in filename_lower:
                logger.info(f"Detected {bank} from filename")
                return bank
    
    # Check content
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first few pages
            text = ""
            for i in range(min(3, len(pdf.pages))):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text += page_text.lower() + "\n"
            
            # Check content patterns
            for bank, patterns in BANK_PATTERNS.items():
                for pattern in patterns['content_patterns']:
                    if pattern in text:
                        logger.info(f"Detected {bank} from content")
                        return bank
    except Exception as e:
        logger.warning(f"Error detecting bank from content: {e}")
    
    return None

def is_valid_date(date_str: str) -> bool:
    """Validate if a string is a legitimate date"""
    if not date_str:
        return False
    
    # Common phone number patterns to reject
    phone_patterns = [
        r'^1-\d{2,3}$',
        r'^\d{3}-\d{3}-\d{4}$',
        r'^1-\d{3}-\d{3}-\d{4}$',
    ]
    
    for pattern in phone_patterns:
        if re.match(pattern, date_str):
            return False
    
    # Check if it looks like a real date
    date_patterns = [
        r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
        r'^\d{1,2}[/-]\d{1,2}$',
        r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',
        r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}$',
        r'^[A-Za-z]{3}\s+\d{1,2},?\s+\d{2,4}$',
    ]
    
    return any(re.match(pattern, date_str) for pattern in date_patterns)

def is_realistic_amount(amount: float) -> bool:
    """Check if an amount is realistic for a bank transaction"""
    return -1000000 < amount < 1000000

def clean_transactions(transactions: List[Dict]) -> List[Dict]:
    """Clean and validate transactions"""
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

def is_scanned_pdf(pdf_path: str) -> bool:
    """Check if PDF is scanned/image-based"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            pages_checked = min(3, len(pdf.pages))
            
            for i in range(pages_checked):
                text = pdf.pages[i].extract_text()
                if text:
                    total_chars += len(text.strip())
            
            avg_chars = total_chars / pages_checked
            return avg_chars < 100
    except:
        return False

def parse_universal_pdf_with_custom_banks(pdf_path: str) -> List[Dict]:
    """Enhanced universal PDF parser with custom bank support"""
    logger.info(f"Parsing PDF: {pdf_path}")
    
    # Step 1: Detect bank
    detected_bank = detect_bank(pdf_path)
    
    # Step 2: Use custom parser if available
    if detected_bank:
        # Special handling for banks with existing parsers
        if detected_bank == 'rabobank':
            logger.info("Using Rabobank parser")
            trans = parse_rabobank_pdf(pdf_path)
            if trans:
                return trans
        elif detected_bank == 'woodforest':
            logger.info("Using Woodforest parser")
            trans = parse_woodforest(pdf_path)
            if trans:
                return trans
        # Removed dummy parser - contained hard-coded transactions
        elif detected_bank in BANK_PARSERS:
            logger.info(f"Using custom parser for {detected_bank}")
            parser_class = BANK_PARSERS[detected_bank]
            parser = parser_class()
            trans = parser.parse(pdf_path)
            if trans:
                return trans
    
    # Step 3: Fallback to generic parsing methods
    logger.info("No custom parser found or parsing failed, using generic methods")
    
    best_result = []
    
    # Try pdfplumber first
    try:
        logger.info("Trying pdfplumber...")
        trans = parse_with_pdfplumber(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Pdfplumber failed: {e}")
    
    # Check if scanned
    if is_scanned_pdf(pdf_path):
        logger.info("PDF appears to be scanned, using OCR")
        try:
            trans = parse_scanned_pdf(pdf_path)
            if trans:
                return clean_transactions(trans)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
    
    # Try Camelot
    try:
        logger.info("Trying Camelot for tables...")
        trans = parse_with_camelot(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Camelot failed: {e}")
    
    # Try other parsers
    try:
        logger.info("Trying accurate column parser...")
        trans = parse_accurate_columns(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
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
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Fixed column parser failed: {e}")
    
    # Last resort - OCR
    logger.info("Trying OCR as last resort...")
    try:
        try:
            from advanced_ocr_parser import parse_scanned_pdf_advanced
            trans = parse_scanned_pdf_advanced(pdf_path)
        except:
            trans = parse_scanned_pdf(pdf_path)
        
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            if len(trans) > len(best_result):
                best_result = trans
    except Exception as e:
        logger.warning(f"Final OCR attempt failed: {e}")
    
    # Return best result
    if best_result:
        logger.info(f"Returning best result with {len(best_result)} transactions")
        return best_result
    
    logger.warning(f"No transactions extracted from {pdf_path}")
    return []

# For backward compatibility
parse_universal_pdf = parse_universal_pdf_with_custom_banks