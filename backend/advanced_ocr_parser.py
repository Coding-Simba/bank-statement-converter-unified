"""Advanced OCR parser for complex bank statement layouts"""

import re
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import logging

logger = logging.getLogger(__name__)

def parse_scanned_pdf_advanced(pdf_path):
    """Parse scanned PDFs with advanced multi-line transaction handling"""
    transactions = []
    
    try:
        # Convert PDF to images with high DPI
        images = convert_from_path(pdf_path, dpi=300)
        logger.info(f"Converted PDF to {len(images)} images")
        
        for page_num, image in enumerate(images):
            logger.info(f"Processing page {page_num + 1}")
            
            # Enhance image for better OCR
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            image = image.filter(ImageFilter.SHARPEN)
            
            # Extract text with table mode
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            
            # Parse transactions from this page
            page_transactions = parse_multiline_transactions(text)
            
            if page_transactions:
                logger.info(f"Found {len(page_transactions)} transactions on page {page_num + 1}")
                transactions.extend(page_transactions)
    
    except Exception as e:
        logger.error(f"Advanced OCR parsing failed: {e}")
        raise
    
    return transactions

def parse_multiline_transactions(text):
    """Parse transactions from OCR text with multi-line format"""
    transactions = []
    lines = text.split('\n')
    
    # State machine for parsing
    in_deposits_section = False
    in_withdrawals_section = False
    current_transactions = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headers
        if 'deposits and other additions' in line.lower():
            in_deposits_section = True
            in_withdrawals_section = False
            current_transactions = []
            i += 1
            continue
            
        if 'withdrawals and other subtractions' in line.lower():
            in_deposits_section = False
            in_withdrawals_section = True
            # Process any pending deposits
            if current_transactions:
                transactions.extend(process_transaction_group(current_transactions, is_withdrawal=False))
            current_transactions = []
            i += 1
            continue
        
        # Check for "Total" lines to end sections
        if line.lower().startswith('total'):
            if current_transactions:
                is_withdrawal = in_withdrawals_section
                transactions.extend(process_transaction_group(current_transactions, is_withdrawal))
            current_transactions = []
            in_deposits_section = False
            in_withdrawals_section = False
            i += 1
            continue
        
        # Look for transaction lines (date at start)
        date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)', line)
        if date_match and (in_deposits_section or in_withdrawals_section):
            date_str = date_match.group(1)
            description = date_match.group(2).strip()
            
            # Check if amount is on the same line - look for number at end
            amount_match = re.search(r'([-]?\$?[\d,]+\.?\d+)\s*$', description)
            if amount_match:
                amount_str = amount_match.group(1)
                description = description[:amount_match.start()].strip()
                
                transaction = {
                    'date_string': date_str,
                    'description': description,
                    'amount_string': amount_str
                }
                current_transactions.append(transaction)
            else:
                # Amount might be on next line(s)
                transaction = {
                    'date_string': date_str,
                    'description': description,
                    'amount_string': None
                }
                current_transactions.append(transaction)
        
        # Look for standalone amounts
        elif re.match(r'^[-]?\$?[\d,]+\.?\d+$', line) and current_transactions:
            # This is likely an amount for a previous transaction
            for trans in reversed(current_transactions):
                if trans['amount_string'] is None:
                    trans['amount_string'] = line
                    break
        
        i += 1
    
    # Process any remaining transactions
    if current_transactions:
        is_withdrawal = in_withdrawals_section
        transactions.extend(process_transaction_group(current_transactions, is_withdrawal))
    
    return transactions

def process_transaction_group(transaction_group, is_withdrawal=False):
    """Process a group of transactions and extract amounts"""
    processed = []
    
    for trans in transaction_group:
        if trans['amount_string'] is None:
            continue
            
        # Parse date
        date = parse_date(trans['date_string'])
        if not date:
            continue
            
        # Parse amount
        amount = extract_amount(trans['amount_string'])
        if amount is None:
            continue
        
        # Apply sign based on section
        if is_withdrawal and amount > 0:
            amount = -amount
        
        processed_trans = {
            'date': date,
            'date_string': trans['date_string'],
            'description': clean_description(trans['description']),
            'amount': amount,
            'amount_string': trans['amount_string']
        }
        
        processed.append(processed_trans)
    
    return processed

def parse_date(date_str):
    """Parse date from OCR text"""
    if not date_str:
        return None
    
    # Clean OCR errors
    date_str = date_str.replace('O', '0').replace('o', '0')
    date_str = date_str.replace('l', '1').replace('I', '1')
    
    formats = [
        '%d/%m/%y', '%d/%m/%Y',
        '%m/%d/%y', '%m/%d/%Y',
        '%d-%m-%y', '%d-%m-%Y',
        '%m-%d-%y', '%m-%d-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    if not amount_str:
        return None
        
    try:
        # Clean the string
        amount_str = amount_str.strip()
        amount_str = re.sub(r'[€$£¥₹]', '', amount_str)
        amount_str = amount_str.replace(',', '')
        amount_str = amount_str.replace(' ', '')
        
        # Handle negative amounts
        is_negative = amount_str.startswith('-')
        if is_negative:
            amount_str = amount_str[1:]
        
        amount = float(amount_str)
        
        if is_negative:
            amount = -amount
            
        return amount
        
    except:
        return None

def clean_description(desc):
    """Clean transaction description"""
    # Remove excessive spaces
    desc = ' '.join(desc.split())
    
    # Remove common OCR artifacts
    desc = re.sub(r'[|_]{2,}', '', desc)
    
    return desc