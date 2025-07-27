"""Specialized parser for scanned/image-based statement PDFs with specific layouts"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

def parse_dummy_pdf(pdf_path: str) -> List[Dict]:
    """Parse scanned/image-based PDFs with check entries and transaction tables"""
    if not OCR_AVAILABLE:
        raise ImportError("OCR dependencies not installed")
    
    transactions = []
    
    # Convert PDF to images with high DPI for better OCR
    images = convert_from_path(pdf_path, dpi=300)
    
    for page_num, image in enumerate(images):
        # Get OCR text with detailed data
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Look for check entries pattern
        if has_check_pattern(text):
            transactions.extend(parse_page1_checks(text))
        
        # Look for detailed transaction patterns
        if has_transaction_sections(text):
            transactions.extend(parse_page2_transactions(text))
        
        # Also try structured data extraction
        transactions.extend(extract_from_ocr_data(data))
    
    # Remove duplicates
    return deduplicate_transactions(transactions)

def has_check_pattern(text: str) -> bool:
    """Check if text contains check entry patterns"""
    # Look for patterns like "1234 10/05 $9.98" or "CHECK 1234"
    check_patterns = [
        r'\d{4}\*?\s+\d{1,2}/\d{1,2}\s+\$?[\d,]+\.?\d*',
        r'CHECK\s+\d{4}',
        r'\d{4}\s+\d{1,2}/\d{1,2}'
    ]
    
    for pattern in check_patterns:
        if re.search(pattern, text):
            return True
    return False

def has_transaction_sections(text: str) -> bool:
    """Check if text contains transaction section headers"""
    section_keywords = [
        'deposits and other credits',
        'withdrawals and other debits',
        'transaction history',
        'account activity'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in section_keywords)

def parse_page1_checks(text: str) -> List[Dict]:
    """Parse check entries from page 1 table"""
    transactions = []
    lines = text.split('\n')
    
    # Look for check entries like "1234 10/05 $9.98"
    check_pattern = r'^(\d{4})\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.?\d*)'
    
    for line in lines:
        line = line.strip()
        match = re.match(check_pattern, line)
        if match:
            check_num = match.group(1)
            date_str = match.group(2)
            amount_str = match.group(3)
            
            # Parse date (add current year)
            try:
                current_year = datetime.now().year
                date = datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
            except:
                date = None
            
            # Parse amount (checks are withdrawals)
            try:
                amount = -float(amount_str.replace(',', ''))
            except:
                continue
            
            transactions.append({
                'date': date,
                'date_string': date_str,
                'description': f'CHECK {check_num}',
                'amount': amount
            })
    
    # Also look for POS/ATM transactions on page 1
    # Pattern: "10/02 POS PURCHASE 73.00"
    trans_pattern = r'^(\d{1,2}/\d{1,2})\s+(POS PURCHASE|ATM WITHDRAWAL|PREAUTHORIZED CREDIT).*?\s+([\d,]+\.?\d*)'
    
    for line in lines:
        match = re.search(trans_pattern, line)
        if match:
            date_str = match.group(1)
            trans_type = match.group(2)
            amount_str = match.group(3)
            
            # Parse date
            try:
                current_year = datetime.now().year
                date = datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
            except:
                date = None
            
            # Parse amount
            try:
                amount = float(amount_str.replace(',', ''))
                # Credits are positive, others are negative
                if 'CREDIT' not in trans_type:
                    amount = -amount
            except:
                continue
            
            transactions.append({
                'date': date,
                'date_string': date_str,
                'description': trans_type,
                'amount': amount
            })
    
    return transactions

def parse_page2_transactions(text: str) -> List[Dict]:
    """Parse detailed transactions from page 2"""
    transactions = []
    lines = text.split('\n')
    
    # Track whether we're in deposits or withdrawals section
    in_deposits = False
    in_withdrawals = False
    
    # Try to extract amounts from the text using regex patterns
    amount_pattern = r'\$?([\d,]+\.\d{2})'
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check section headers
        if 'Deposits and Other Credits' in line:
            in_deposits = True
            in_withdrawals = False
            continue
        elif 'Withdrawals and Other Debits' in line:
            in_deposits = False
            in_withdrawals = True
            continue
        
        # Skip headers and empty lines
        if not line or line.lower() == 'date description' or line.lower() == 'date' or line.lower() == 'description':
            continue
        
        # Look for transactions starting with date
        date_match = re.match(r'^(\d{1,2}/\d{1,2})\s+(.+)', line)
        if date_match and (in_deposits or in_withdrawals):
            date_str = date_match.group(1)
            description = date_match.group(2)
            
            # Parse date
            try:
                current_year = datetime.now().year
                date = datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
            except:
                date = None
            
            # Clean description - remove terminal IDs and extra numbers
            description = re.sub(r'TERMINAL\s+\d+', 'TERMINAL', description)
            description = re.sub(r'\s+\d{6,}', '', description)  # Remove long numbers
            description = re.sub(r'\s+00-00-00.*', '', description)  # Remove timestamps
            description = re.sub(r'\s+[A-Z0-9]{16,}', '', description)  # Remove long IDs
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Try to find amount in the line or next lines
            amount = None
            
            # Look for amount in the same line
            amount_match = re.search(amount_pattern, line)
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace(',', ''))
                except:
                    pass
            
            # If no amount found in current line, check next line
            if amount is None and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                amount_match = re.search(amount_pattern, next_line)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Skip transaction if no amount found
            if amount is None:
                continue
            
            # Apply sign based on section
            if in_deposits:
                amount = abs(amount)
            else:
                amount = -abs(amount)
            
            transactions.append({
                'date': date,
                'date_string': date_str,
                'description': description,
                'amount': amount
            })
    
    return transactions

def extract_from_ocr_data(data: Dict) -> List[Dict]:
    """Extract transactions from OCR data with positional information"""
    transactions = []
    
    # Group text by lines based on vertical position
    lines = {}
    for i in range(len(data['text'])):
        if data['text'][i].strip() and data['conf'][i] > 30:  # Confidence threshold
            top = data['top'][i]
            line_key = round(top / 10) * 10
            
            if line_key not in lines:
                lines[line_key] = []
            
            lines[line_key].append({
                'text': data['text'][i],
                'left': data['left'][i],
                'conf': data['conf'][i]
            })
    
    # Process each line
    for _, line_items in sorted(lines.items()):
        line_items.sort(key=lambda x: x['left'])
        line_text = ' '.join(item['text'] for item in line_items)
        
        # Try to parse as transaction
        transaction = parse_transaction_line(line_text)
        if transaction:
            transactions.append(transaction)
    
    return transactions

def parse_transaction_line(line: str) -> Optional[Dict]:
    """Parse a single line that might be a transaction"""
    # Common transaction patterns
    patterns = [
        # Date Description Amount
        r'^(\d{1,2}[/\-\.]\d{1,2}(?:[/\-\.]\d{2,4})?)\s+(.+?)\s+\$?([\d,]+\.?\d*)$',
        # Check pattern: check# date amount
        r'^(\d{4})\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.?\d*)$',
        # Date and description (amount might be on next line)
        r'^(\d{1,2}[/\-\.]\d{1,2})\s+(.+?)$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line.strip())
        if match:
            if len(match.groups()) == 3:
                if re.match(r'^\d{4}', match.group(1)):
                    # Check pattern
                    return {
                        'date_string': match.group(2),
                        'description': f'CHECK {match.group(1)}',
                        'amount': -float(match.group(3).replace(',', ''))
                    }
                else:
                    # Regular transaction
                    return {
                        'date_string': match.group(1),
                        'description': match.group(2).strip(),
                        'amount': float(match.group(3).replace(',', ''))
                    }
            elif len(match.groups()) == 2:
                # Date and description only
                return {
                    'date_string': match.group(1),
                    'description': match.group(2).strip(),
                    'amount': None  # Will need to find amount elsewhere
                }
    
    return None

def deduplicate_transactions(transactions: List[Dict]) -> List[Dict]:
    """Remove duplicate transactions based on date, description, and amount"""
    seen = set()
    unique = []
    
    for trans in transactions:
        # Skip incomplete transactions
        if not trans.get('description') or trans.get('amount') is None:
            continue
            
        # Create unique key
        key = (
            trans.get('date_string', ''),
            trans.get('description', ''),
            trans.get('amount', 0)
        )
        
        if key not in seen:
            seen.add(key)
            # Parse date if needed
            if 'date' not in trans and trans.get('date_string'):
                try:
                    date_str = trans['date_string']
                    # Add current year if not present
                    if len(date_str.split('/')[-1]) <= 2:
                        current_year = datetime.now().year
                        trans['date'] = datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
                    else:
                        trans['date'] = datetime.strptime(date_str, "%m/%d/%Y")
                except:
                    trans['date'] = None
            
            unique.append(trans)
    
    return unique