"""Universal bank statement parser using Unstructured.io"""

import os
import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Check if Unstructured is available
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import Table, Text, Title, NarrativeText
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    logger.warning("Unstructured library not installed. Install with: pip install unstructured[pdf]")

def parse_unstructured_pdf(pdf_path: str) -> List[Dict]:
    """Parse PDF using Unstructured.io library which handles complex layouts automatically"""
    
    if not UNSTRUCTURED_AVAILABLE:
        raise ImportError("Unstructured library not installed. Install with: pip install unstructured[pdf]")
    
    transactions = []
    
    try:
        # Partition PDF into elements
        # This automatically handles tables, text, OCR, and complex layouts
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",  # Use high resolution strategy for better accuracy
            infer_table_structure=True,  # Detect and parse tables
            include_page_breaks=True,
            languages=["eng"],  # Specify languages for OCR
        )
        
        logger.info(f"Extracted {len(elements)} elements from PDF")
        
        # Process elements
        current_section = None
        in_transaction_table = False
        
        for i, element in enumerate(elements):
            element_text = str(element).strip()
            
            # Skip empty elements
            if not element_text:
                continue
                
            # Detect transaction sections
            if isinstance(element, (Title, Text)):
                text_lower = element_text.lower()
                if any(keyword in text_lower for keyword in [
                    'transaction', 'deposit', 'withdrawal', 'debit', 'credit',
                    'checks paid', 'atm', 'pos purchase', 'payment'
                ]):
                    current_section = element_text
                    in_transaction_table = True
                    logger.info(f"Found transaction section: {current_section}")
                    continue
            
            # Process tables
            if isinstance(element, Table):
                logger.info(f"Processing table with content: {element_text[:100]}...")
                table_transactions = extract_transactions_from_table(element_text)
                if table_transactions:
                    transactions.extend(table_transactions)
                continue
            
            # Process text that might contain transactions
            if in_transaction_table and isinstance(element, (Text, NarrativeText)):
                # Look for transaction patterns in text
                text_transactions = extract_transactions_from_text(element_text)
                if text_transactions:
                    transactions.extend(text_transactions)
        
        # If no structured transactions found, try a more aggressive approach
        if not transactions:
            logger.info("No transactions found with structured approach, trying pattern matching")
            full_text = '\n'.join(str(element) for element in elements)
            transactions = extract_transactions_with_patterns(full_text)
        
    except Exception as e:
        logger.error(f"Unstructured parsing failed: {e}")
        raise
    
    return transactions

def extract_transactions_from_table(table_text: str) -> List[Dict]:
    """Extract transactions from table text"""
    transactions = []
    lines = table_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip header rows
        if any(header in line.lower() for header in ['date', 'description', 'amount', 'balance']):
            continue
        
        # Parse transaction line
        transaction = parse_transaction_line(line)
        if transaction:
            transactions.append(transaction)
    
    return transactions

def extract_transactions_from_text(text: str) -> List[Dict]:
    """Extract transactions from regular text"""
    transactions = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line:
            transaction = parse_transaction_line(line)
            if transaction:
                transactions.append(transaction)
    
    return transactions

def parse_transaction_line(line: str) -> Optional[Dict]:
    """Parse a single line that might contain a transaction"""
    
    # Common transaction patterns
    patterns = [
        # Date at start, description, amount at end
        r'^(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)\s*$',
        
        # Check entries: "1234 10/05 $9.98"
        r'^(\d{4})\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.?\d*)$',
        
        # Date, Check Number, Amount, Reference
        r'^(\d{1,2}[-/]\d{1,2})\s+(\d{3,4})\s+([\d,]+\.?\d*)\s+(\d+)$',
        
        # Description with amount
        r'^(.+?)\s+([-+]?\$?[\d,]+\.?\d*)\s*$',
        
        # Commerce Bank format: "05-12 1001 75.00 00012576589"
        r'^(\d{2}-\d{2})\s+(\d{4})\s+([\d,]+\.?\d*)\s+(\d+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            groups = match.groups()
            
            # Handle different pattern types
            if len(groups) == 4 and re.match(r'^\d{2}-\d{2}$', groups[0]):
                # Commerce Bank check format
                return {
                    'date_string': groups[0],
                    'date': parse_date_string(groups[0]),
                    'description': f'CHECK {groups[1]}',
                    'amount': -float(groups[2].replace(',', ''))  # Checks are negative
                }
            elif len(groups) == 3 and re.match(r'^\d{4}$', groups[0]):
                # Check entry format
                return {
                    'date_string': groups[1],
                    'date': parse_date_string(groups[1]),
                    'description': f'CHECK {groups[0]}',
                    'amount': -float(groups[2].replace(',', ''))
                }
            elif len(groups) >= 3:
                # Standard format with date
                date_str = groups[0]
                description = groups[1]
                amount_str = groups[2]
                
                date = parse_date_string(date_str)
                if date:
                    amount = parse_amount(amount_str)
                    if amount is not None:
                        return {
                            'date': date,
                            'date_string': date_str,
                            'description': description.strip(),
                            'amount': amount
                        }
            elif len(groups) == 2:
                # Description and amount only
                description = groups[0]
                amount = parse_amount(groups[1])
                if amount is not None and len(description) > 3:
                    return {
                        'description': description.strip(),
                        'amount': amount
                    }
    
    return None

def extract_transactions_with_patterns(text: str) -> List[Dict]:
    """Extract transactions using aggressive pattern matching"""
    transactions = []
    
    # Split into lines
    lines = text.split('\n')
    
    # Track context
    current_date = None
    in_deposits = False
    in_withdrawals = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Update context
        if 'deposits' in line.lower() and 'credits' in line.lower():
            in_deposits = True
            in_withdrawals = False
        elif 'withdrawals' in line.lower() or 'debits' in line.lower():
            in_deposits = False
            in_withdrawals = True
        
        # Look for dates
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)', line)
        if date_match:
            current_date = parse_date_string(date_match.group(1))
            current_date_str = date_match.group(1)
        
        # Look for amounts
        amount_matches = re.findall(r'[-+]?\$?([\d,]+\.?\d*)', line)
        
        for amount_str in amount_matches:
            amount = parse_amount(amount_str)
            if amount is not None and amount != 0:
                # Try to extract description
                description = line
                
                # Remove date from description
                if date_match:
                    description = description.replace(date_match.group(0), '')
                
                # Remove amount from description
                description = re.sub(r'[-+]?\$?[\d,]+\.?\d*', '', description)
                
                # Clean description
                description = ' '.join(description.split()).strip()
                
                # Skip if no meaningful description
                if not description or len(description) < 3:
                    continue
                
                # Apply sign based on context
                if in_deposits:
                    amount = abs(amount)
                elif in_withdrawals:
                    amount = -abs(amount)
                
                transaction = {
                    'description': description,
                    'amount': amount
                }
                
                if current_date:
                    transaction['date'] = current_date
                    transaction['date_string'] = current_date_str
                
                transactions.append(transaction)
                break  # Only take first amount in line
    
    return transactions

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse various date formats"""
    if not date_str:
        return None
        
    # Clean date string
    date_str = date_str.strip()
    
    # Common date formats
    formats = [
        '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
        '%m/%d/%y', '%m-%d-%y',
        '%m/%d', '%m-%d',  # Month/day only
        '%d/%m/%Y', '%d-%m-%Y',  # European format
        '%b %d, %Y', '%B %d, %Y',  # Named months
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            
            # If no year, use current year
            if parsed.year == 1900:
                current_year = datetime.now().year
                parsed = parsed.replace(year=current_year)
                
            return parsed
        except ValueError:
            continue
    
    return None

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string to float"""
    if not amount_str:
        return None
        
    try:
        # Clean amount string
        amount_str = amount_str.strip()
        
        # Remove currency symbols
        amount_str = re.sub(r'[$€£¥₹]', '', amount_str)
        
        # Check for negative indicators
        is_negative = amount_str.startswith('-') or amount_str.startswith('(')
        
        # Remove signs and parentheses
        amount_str = re.sub(r'[()-+]', '', amount_str)
        
        # Remove commas
        amount_str = amount_str.replace(',', '')
        
        # Convert to float
        amount = float(amount_str)
        
        # Apply sign
        if is_negative:
            amount = -amount
            
        return amount
    except ValueError:
        return None