"""Enhanced parser for Woodforest National Bank statements with better compatibility"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import pdfplumber
import logging

logger = logging.getLogger(__name__)

def parse_date_woodforest(date_str: str, statement_year: Optional[int] = None) -> Optional[datetime]:
    """Parse Woodforest date format (MM-DD) with smart year detection"""
    try:
        # Extract month and day
        match = re.match(r'(\d{1,2})[/-](\d{1,2})', date_str)
        if not match:
            return None
            
        month = int(match.group(1))
        day = int(match.group(2))
        
        # Use provided year or current year
        year = statement_year or datetime.now().year
        
        # Create date
        date = datetime(year, month, day)
        
        # If date is in the future, it might be from previous year
        if date > datetime.now() and not statement_year:
            date = datetime(year - 1, month, day)
            
        return date
    except:
        return None

def extract_amount(amount_str: str) -> Optional[float]:
    """Extract numeric amount from string"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Handle parentheses for negative amounts
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + re.sub(r'[()]', '', cleaned)
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def detect_statement_year(text: str) -> Optional[int]:
    """Detect the statement year from the document text"""
    # Look for statement period or date patterns
    year_patterns = [
        r'Statement Period:.*?(\d{4})',
        r'Statement Date:.*?(\d{4})',
        r'(\d{1,2}/\d{1,2}/(\d{4}))',
        r'(\d{4})-\d{2}-\d{2}',
        r'For the period.*?(\d{4})',
        r'Statement.*?(\d{4})'
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year_str = match.group(1) if match.lastindex == 1 else match.group(2)
            try:
                year = int(year_str)
                if 2000 <= year <= 2100:  # Reasonable year range
                    return year
            except:
                continue
    
    return None

def parse_woodforest_enhanced(pdf_path: str) -> List[Dict]:
    """Enhanced parser for Woodforest National Bank statements"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract all text first to detect year
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Detect statement year
            statement_year = detect_statement_year(full_text)
            logger.info(f"Detected statement year: {statement_year}")
            
            # Process each page
            for page_num, page in enumerate(pdf.pages):
                # Try table extraction first
                tables = page.extract_tables()
                
                if tables:
                    # Process tables
                    for table in tables:
                        transactions.extend(parse_woodforest_table(table, statement_year))
                
                # Also try text extraction with layout
                text = page.extract_text()
                if text:
                    transactions.extend(parse_woodforest_text(text, statement_year))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_transactions = []
        for trans in transactions:
            key = (trans.get('date_string'), trans.get('amount'), trans.get('description', '')[:20])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(trans)
        
        # Sort by date
        unique_transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return unique_transactions
        
    except Exception as e:
        logger.error(f"Error parsing Woodforest statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions

def parse_woodforest_table(table: List[List], statement_year: Optional[int]) -> List[Dict]:
    """Parse transactions from a table"""
    transactions = []
    
    if not table or len(table) < 2:
        return transactions
    
    # Find header row
    header_row = None
    header_idx = 0
    
    for i, row in enumerate(table):
        if row and any('date' in str(cell).lower() for cell in row):
            header_row = [str(cell).lower() for cell in row]
            header_idx = i
            break
    
    if not header_row:
        return transactions
    
    # Find column indices
    date_col = next((i for i, h in enumerate(header_row) if 'date' in h), None)
    credit_col = next((i for i, h in enumerate(header_row) if 'credit' in h), None)
    debit_col = next((i for i, h in enumerate(header_row) if 'debit' in h), None)
    desc_col = next((i for i, h in enumerate(header_row) if 'desc' in h), None)
    
    # If no description column, it might be in a different position
    if desc_col is None:
        # Try to find it after balance column
        balance_col = next((i for i, h in enumerate(header_row) if 'balance' in h), None)
        if balance_col is not None and balance_col < len(header_row) - 1:
            desc_col = balance_col + 1
    
    # Process data rows
    for row in table[header_idx + 1:]:
        if not row or date_col is None or date_col >= len(row):
            continue
        
        date_str = str(row[date_col]).strip()
        if not re.match(r'\d{1,2}[/-]\d{1,2}', date_str):
            continue
        
        trans_date = parse_date_woodforest(date_str, statement_year)
        if not trans_date:
            continue
        
        # Extract amount
        amount = None
        if credit_col is not None and credit_col < len(row):
            credit_amount = extract_amount(str(row[credit_col]))
            if credit_amount:
                amount = credit_amount
        
        if debit_col is not None and debit_col < len(row):
            debit_amount = extract_amount(str(row[debit_col]))
            if debit_amount:
                amount = -debit_amount
        
        if amount is None:
            continue
        
        # Extract description
        description = ""
        if desc_col is not None and desc_col < len(row):
            description = str(row[desc_col]).strip()
        
        transaction = {
            'date': trans_date,
            'date_string': date_str,
            'description': description,
            'amount': amount,
            'amount_string': f"{abs(amount):.2f}"
        }
        
        transactions.append(transaction)
    
    return transactions

def parse_woodforest_text(text: str, statement_year: Optional[int]) -> List[Dict]:
    """Parse transactions from text with flexible column detection"""
    transactions = []
    lines = text.split('\n')
    
    in_transaction_section = False
    
    for i, line in enumerate(lines):
        # Look for transaction section markers
        if 'transactions' in line.lower():
            if i + 1 < len(lines):
                next_line = lines[i + 1].lower()
                if 'date' in next_line and ('credit' in next_line or 'debit' in next_line):
                    in_transaction_section = True
                    continue
        
        # End markers
        if any(marker in line.lower() for marker in ['total for', 'account summary', 'ending balance']):
            in_transaction_section = False
            continue
        
        if not in_transaction_section or not line.strip():
            continue
        
        # Skip headers
        if 'date' in line.lower() and 'credit' in line.lower():
            continue
        
        # Look for transaction patterns
        # Pattern 1: Date at start of line
        date_match = re.match(r'^\s*(\d{1,2}[/-]\d{1,2})', line)
        
        if date_match:
            date_str = date_match.group(1)
            trans_date = parse_date_woodforest(date_str, statement_year)
            
            if trans_date:
                # Look for amounts in the line
                # Find all numbers that look like amounts
                amount_pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})'
                amounts = re.findall(amount_pattern, line)
                
                if amounts:
                    # Determine credit vs debit by position or context
                    # Usually credits come before debits in the line
                    amount = None
                    
                    # Look for debit indicators
                    if any(indicator in line.upper() for indicator in ['DB', 'WDL', 'WITHDRAWAL', 'FEE', 'CHARGE']):
                        # It's likely a debit
                        amount = -extract_amount(amounts[0])
                    else:
                        # Check if it's explicitly a deposit
                        if 'DEPOSIT' in line.upper():
                            amount = extract_amount(amounts[0])
                        else:
                            # Use position heuristic - if there are multiple amounts, 
                            # first might be credit, second might be debit
                            if len(amounts) >= 2:
                                # Has both credit and debit columns
                                credit_val = extract_amount(amounts[0])
                                debit_val = extract_amount(amounts[1])
                                
                                if credit_val and credit_val > 0:
                                    amount = credit_val
                                elif debit_val and debit_val > 0:
                                    amount = -debit_val
                            else:
                                # Single amount - need to determine from context
                                amount = extract_amount(amounts[0])
                                if amount and 'DEPOSIT' not in line.upper():
                                    amount = -amount
                    
                    if amount is not None:
                        # Extract description - usually after the amounts
                        desc_start = line.rfind(amounts[-1]) + len(amounts[-1])
                        description = line[desc_start:].strip()
                        
                        # If no description found, try to get text after date but before amounts
                        if not description:
                            date_end = line.find(date_str) + len(date_str)
                            first_amount_pos = line.find(amounts[0])
                            if first_amount_pos > date_end:
                                description = line[date_end:first_amount_pos].strip()
                        
                        transaction = {
                            'date': trans_date,
                            'date_string': date_str,
                            'description': description,
                            'amount': amount,
                            'amount_string': f"{abs(amount):.2f}"
                        }
                        
                        transactions.append(transaction)
    
    return transactions

# Keep the original function name for compatibility
def parse_woodforest(pdf_path: str) -> List[Dict]:
    """Wrapper for backward compatibility"""
    return parse_woodforest_enhanced(pdf_path)