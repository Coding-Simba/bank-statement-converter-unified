#!/usr/bin/env python3
"""
Modern PDF parser using pdfplumber for better extraction
"""
import pdfplumber
import re
from datetime import datetime
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def parse_with_pdfplumber(pdf_path: str) -> List[Dict]:
    """
    Extract transactions using pdfplumber with advanced text and table extraction
    """
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processing page {page_num}")
                
                # Method 1: Try table extraction first
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        table_transactions = parse_table(table)
                        transactions.extend(table_transactions)
                
                # Method 2: Extract text with layout preservation
                if not transactions:  # If no tables found
                    text = page.extract_text()
                    if text:
                        text_transactions = parse_text_with_layout(text)
                        transactions.extend(text_transactions)
                
                # Method 3: Extract words with bounding boxes for columnar data
                words = page.extract_words()
                if words:
                    word_transactions = parse_words_by_position(words)
                    transactions.extend(word_transactions)
    
    except Exception as e:
        logger.error(f"Error parsing PDF with pdfplumber: {e}")
    
    return deduplicate_transactions(transactions)

def parse_table(table: List[List]) -> List[Dict]:
    """Parse transactions from a table structure"""
    transactions = []
    
    # Common header patterns
    date_headers = ['date', 'posting date', 'transaction date', 'trans date']
    desc_headers = ['description', 'transaction', 'details', 'memo']
    amount_headers = ['amount', 'debit', 'credit', 'withdrawal', 'deposit']
    
    # Find column indices
    if not table or len(table) < 2:
        return transactions
    
    # Check first few rows for headers
    header_row = None
    for i in range(min(3, len(table))):
        row = table[i]
        if any(col and any(h in str(col).lower() for h in date_headers) for col in row):
            header_row = i
            break
    
    if header_row is None:
        # Try to parse without headers
        for row in table:
            trans = parse_table_row(row)
            if trans:
                transactions.append(trans)
    else:
        # Parse with headers
        headers = [str(h).lower() if h else '' for h in table[header_row]]
        
        # Find column indices
        date_col = find_column_index(headers, date_headers)
        desc_col = find_column_index(headers, desc_headers)
        amount_cols = find_amount_columns(headers, amount_headers)
        
        # Parse data rows
        for row in table[header_row + 1:]:
            trans = parse_table_row_with_columns(row, date_col, desc_col, amount_cols)
            if trans:
                transactions.append(trans)
    
    return transactions

def parse_table_row(row: List) -> Optional[Dict]:
    """Parse a table row without known column positions"""
    if not row or len(row) < 2:
        return None
    
    # Try to identify date, description, and amount
    date_val = None
    desc_val = None
    amount_val = None
    
    for cell in row:
        if not cell:
            continue
        
        cell_str = str(cell).strip()
        
        # Check for date
        if not date_val and is_date(cell_str):
            date_val = cell_str
        
        # Check for amount
        elif not amount_val and is_amount(cell_str):
            amount_val = parse_amount(cell_str)
        
        # Everything else is description
        elif not desc_val and len(cell_str) > 3 and not cell_str.isdigit():
            desc_val = cell_str
    
    if date_val and (desc_val or amount_val):
        return {
            'date_string': date_val,
            'description': desc_val or 'Transaction',
            'amount': amount_val or 0.0
        }
    
    return None

def parse_text_with_layout(text: str) -> List[Dict]:
    """Parse transactions from text preserving layout"""
    transactions = []
    lines = text.split('\n')
    
    # Common transaction patterns
    patterns = [
        # Date Description Amount
        r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        # Date Amount Description
        r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+([-+]?\$?[\d,]+\.?\d*)\s+(.+)',
        # MM/DD Description $Amount
        r'(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
        # Date at start of line, amount at end
        r'^(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+?)\s+([-+]?[\d,]+\.?\d*)$',
        # YYYY-MM-DD format
        r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        # DD MMM YYYY format
        r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        # MMM DD, YYYY format
        r'([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # Determine order (date is always first)
                    date_str = groups[0]
                    
                    # Check if second group is amount or description
                    if is_amount(groups[1]):
                        amount_str = groups[1]
                        desc_str = groups[2]
                    else:
                        desc_str = groups[1]
                        amount_str = groups[2]
                    
                    trans = {
                        'date_string': date_str,
                        'description': desc_str.strip(),
                        'amount': parse_amount(amount_str)
                    }
                    
                    if trans['amount'] != 0:
                        transactions.append(trans)
                        break
    
    return transactions

def parse_words_by_position(words: List[Dict]) -> List[Dict]:
    """Parse transactions by analyzing word positions (for columnar data)"""
    transactions = []
    
    # Group words by y-coordinate (same line)
    lines = {}
    for word in words:
        y = round(word['top'])  # Round to group words on same line
        if y not in lines:
            lines[y] = []
        lines[y].append(word)
    
    # Sort lines by y-coordinate
    sorted_lines = sorted(lines.items(), key=lambda x: x[0])
    
    # Process each line
    for y, line_words in sorted_lines:
        # Sort words by x-coordinate (left to right)
        line_words.sort(key=lambda w: w['x0'])
        
        # Extract text from words
        line_text = ' '.join([w['text'] for w in line_words])
        
        # Try to parse as transaction
        trans = parse_transaction_line(line_text)
        if trans:
            transactions.append(trans)
    
    return transactions

def parse_transaction_line(line: str) -> Optional[Dict]:
    """Parse a single line as a transaction"""
    # Remove extra spaces
    line = ' '.join(line.split())
    
    # Look for date pattern
    date_match = re.search(r'\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?', line)
    if not date_match:
        return None
    
    date_str = date_match.group()
    
    # Look for amount pattern
    amount_match = re.search(r'[-+]?\$?[\d,]+\.?\d*', line)
    if not amount_match:
        return None
    
    amount_str = amount_match.group()
    amount = parse_amount(amount_str)
    
    if amount == 0:
        return None
    
    # Extract description (everything between date and amount)
    date_end = date_match.end()
    amount_start = amount_match.start()
    
    if amount_start > date_end:
        desc = line[date_end:amount_start].strip()
    else:
        # Amount before description
        desc = line[amount_match.end():].strip()
    
    # Clean description
    desc = desc.strip(' -,')
    
    if desc:
        return {
            'date_string': date_str,
            'description': desc,
            'amount': amount
        }
    
    return None

def find_column_index(headers: List[str], keywords: List[str]) -> Optional[int]:
    """Find column index by matching keywords"""
    for i, header in enumerate(headers):
        if any(keyword in header for keyword in keywords):
            return i
    return None

def find_amount_columns(headers: List[str], keywords: List[str]) -> Dict[str, int]:
    """Find debit/credit or amount columns"""
    columns = {}
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        
        if 'debit' in header_lower or 'withdrawal' in header_lower:
            columns['debit'] = i
        elif 'credit' in header_lower or 'deposit' in header_lower:
            columns['credit'] = i
        elif 'amount' in header_lower:
            columns['amount'] = i
    
    return columns

def parse_table_row_with_columns(row: List, date_col: int, desc_col: int, amount_cols: Dict) -> Optional[Dict]:
    """Parse row with known column positions"""
    if not row:
        return None
    
    # Extract date
    date_str = str(row[date_col]).strip() if date_col is not None and date_col < len(row) else None
    if not date_str or not is_date(date_str):
        return None
    
    # Extract description
    desc = str(row[desc_col]).strip() if desc_col is not None and desc_col < len(row) else 'Transaction'
    
    # Extract amount
    amount = 0.0
    
    if 'amount' in amount_cols and amount_cols['amount'] < len(row):
        amount = parse_amount(str(row[amount_cols['amount']]))
    elif 'debit' in amount_cols and 'credit' in amount_cols:
        debit = parse_amount(str(row[amount_cols['debit']])) if amount_cols['debit'] < len(row) else 0
        credit = parse_amount(str(row[amount_cols['credit']])) if amount_cols['credit'] < len(row) else 0
        
        if debit > 0:
            amount = -debit
        elif credit > 0:
            amount = credit
    
    if amount != 0:
        return {
            'date_string': date_str,
            'description': desc,
            'amount': amount
        }
    
    return None

def is_date(text: str) -> bool:
    """Check if text looks like a date"""
    date_patterns = [
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',
        r'^\d{1,2}[-/]\d{1,2}$',
        r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$',
        r'^[A-Za-z]{3}\s+\d{1,2},?\s+\d{2,4}$',
        r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}$'
    ]
    
    text = text.strip()
    return any(re.match(pattern, text) for pattern in date_patterns)

def is_amount(text: str) -> bool:
    """Check if text looks like an amount"""
    amount_pattern = r'^[-+]?\$?[\d,]+\.?\d*$'
    text = text.strip()
    return bool(re.match(amount_pattern, text))

def parse_amount(text: str) -> float:
    """Parse amount from text"""
    if not text:
        return 0.0
    
    # Remove currency symbols and spaces
    text = text.replace('$', '').replace(',', '').strip()
    
    # Handle negative amounts
    is_negative = False
    if text.startswith('(') and text.endswith(')'):
        is_negative = True
        text = text[1:-1]
    elif text.startswith('-'):
        is_negative = True
        text = text[1:]
    
    try:
        amount = float(text)
        return -amount if is_negative else amount
    except ValueError:
        return 0.0

def deduplicate_transactions(transactions: List[Dict]) -> List[Dict]:
    """Remove duplicate transactions"""
    seen = set()
    unique = []
    
    for trans in transactions:
        key = (
            trans.get('date_string', ''),
            trans.get('description', ''),
            trans.get('amount', 0)
        )
        
        if key not in seen:
            seen.add(key)
            unique.append(trans)
    
    return unique