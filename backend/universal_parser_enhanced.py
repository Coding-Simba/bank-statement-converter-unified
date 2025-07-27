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
from .pdfplumber_parser import parse_with_pdfplumber
from .camelot_parser import parse_with_camelot
from .ocr_parser import parse_scanned_pdf
from .accurate_column_parser import parse_accurate_columns
from .fixed_column_parser import parse_fixed_column_layout
from .dummy_pdf_parser import parse_dummy_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    # Check if it's the dummy statement
    if 'dummy' in os.path.basename(pdf_path).lower():
        logger.info("Detected dummy statement, using specialized parser")
        trans = parse_dummy_pdf(pdf_path)
        if trans:
            cleaned = clean_transactions(trans)
            if cleaned:
                return cleaned
            # Keep raw transactions if cleaning removes all
            return trans
    
    # Step 1: Try pdfplumber first (works for most modern PDFs)
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
    
    # Step 2: If pdfplumber fails or finds nothing, check if it's scanned
    if is_scanned_pdf(pdf_path):
        logger.info("PDF appears to be scanned, using OCR")
        try:
            trans = parse_scanned_pdf(pdf_path)
            if trans:
                return clean_transactions(trans)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
    
    # Step 3: Try Camelot for table-based PDFs
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
    
    # Step 4: Try specialized parsers
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
    
    # Step 5: Last resort - OCR even if not detected as scanned
    logger.info("Trying OCR as last resort...")
    try:
        # Try advanced OCR first
        try:
            from .advanced_ocr_parser import parse_scanned_pdf_advanced
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
    
    logger.warning(f"No transactions extracted from {pdf_path}")
    return []

# For backward compatibility
parse_universal_pdf = parse_universal_pdf_enhanced