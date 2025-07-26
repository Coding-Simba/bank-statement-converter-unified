"""Bank statement parser using Camelot for better table extraction"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if Camelot is available
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logger.warning("Camelot not installed. Install with: pip install camelot-py[cv]")

# Check if pdfplumber is available as fallback
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")

def parse_with_camelot(pdf_path: str) -> List[Dict]:
    """Parse PDF using Camelot which is specifically designed for table extraction"""
    
    if not CAMELOT_AVAILABLE:
        raise ImportError("Camelot not installed. Install with: pip install camelot-py[cv]")
    
    transactions = []
    
    try:
        # Read all tables from the PDF
        # Use both methods to maximize extraction
        methods = ['stream', 'lattice']
        
        for method in methods:
            try:
                logger.info(f"Trying Camelot with {method} method")
                tables = camelot.read_pdf(pdf_path, pages='all', flavor=method, suppress_stdout=True)
                
                if tables.n > 0:
                    logger.info(f"Found {tables.n} tables using {method} method")
                    
                    for i, table in enumerate(tables):
                        # Convert to pandas DataFrame
                        df = table.df
                        
                        # Try to extract transactions from the DataFrame
                        table_transactions = extract_transactions_from_dataframe(df)
                        if table_transactions:
                            transactions.extend(table_transactions)
                            logger.info(f"Extracted {len(table_transactions)} transactions from table {i+1}")
                
                # If we found transactions, don't try the other method
                if transactions:
                    break
                    
            except Exception as e:
                logger.warning(f"Camelot {method} method failed: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Camelot parsing failed: {e}")
        raise
    
    return transactions

def parse_with_pdfplumber(pdf_path: str) -> List[Dict]:
    """Parse PDF using pdfplumber as a fallback option"""
    
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
    
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables
                tables = page.extract_tables()
                
                for table_num, table in enumerate(tables):
                    if table:
                        logger.info(f"Found table on page {page_num + 1}")
                        # Process table rows
                        table_transactions = extract_transactions_from_table_data(table)
                        if table_transactions:
                            transactions.extend(table_transactions)
                
                # Also try text extraction for non-table transactions
                text = page.extract_text()
                if text:
                    text_transactions = extract_transactions_from_text(text)
                    if text_transactions:
                        transactions.extend(text_transactions)
        
    except Exception as e:
        logger.error(f"pdfplumber parsing failed: {e}")
        raise
    
    return transactions

def extract_transactions_from_dataframe(df) -> List[Dict]:
    """Extract transactions from a pandas DataFrame"""
    transactions = []
    
    # Clean column names
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    # Common column patterns
    date_cols = ['date', 'transaction date', 'posting date', 'date paid', 'trans date']
    desc_cols = ['description', 'transaction', 'details', 'memo', 'check number']
    amount_cols = ['amount', 'debit', 'credit', 'withdrawal', 'deposit', 'payment']
    
    # Find relevant columns
    date_col = None
    desc_col = None
    amount_cols_found = []
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        if any(pattern in col_lower for pattern in date_cols):
            date_col = col
        elif any(pattern in col_lower for pattern in desc_cols):
            desc_col = col
        elif any(pattern in col_lower for pattern in amount_cols):
            amount_cols_found.append(col)
    
    # Process rows
    for _, row in df.iterrows():
        transaction = {}
        
        # Extract date
        if date_col and pd.notna(row[date_col]):
            date = parse_date_string(str(row[date_col]))
            if date:
                transaction['date'] = date
                transaction['date_string'] = str(row[date_col])
        
        # Extract description
        if desc_col and pd.notna(row[desc_col]):
            transaction['description'] = str(row[desc_col]).strip()
        else:
            # Try to find description in any non-numeric column
            for col in df.columns:
                if col not in amount_cols_found and pd.notna(row[col]):
                    val = str(row[col]).strip()
                    if val and not is_numeric(val):
                        transaction['description'] = val
                        break
        
        # Extract amount
        for col in amount_cols_found:
            if pd.notna(row[col]):
                amount = parse_amount(str(row[col]))
                if amount is not None:
                    transaction['amount'] = amount
                    break
        
        # Only add if we have meaningful data
        if transaction.get('description') or transaction.get('amount') is not None:
            transactions.append(transaction)
    
    return transactions

def extract_transactions_from_table_data(table: List[List]) -> List[Dict]:
    """Extract transactions from raw table data (list of lists)"""
    transactions = []
    
    if not table or len(table) < 2:
        return transactions
    
    # First row might be headers
    headers = [str(cell).strip().lower() if cell else '' for cell in table[0]]
    
    # Find column indices
    date_idx = None
    desc_idx = None
    amount_idx = None
    
    for i, header in enumerate(headers):
        if any(pattern in header for pattern in ['date', 'trans', 'paid']):
            date_idx = i
        elif any(pattern in header for pattern in ['description', 'memo', 'details']):
            desc_idx = i
        elif any(pattern in header for pattern in ['amount', 'debit', 'credit', 'payment']):
            amount_idx = i
    
    # Process rows
    for row in table[1:]:  # Skip header row
        if not row or all(not cell for cell in row):
            continue
            
        transaction = {}
        
        # Extract date
        if date_idx is not None and date_idx < len(row) and row[date_idx]:
            date = parse_date_string(str(row[date_idx]))
            if date:
                transaction['date'] = date
                transaction['date_string'] = str(row[date_idx])
        
        # Extract description
        if desc_idx is not None and desc_idx < len(row) and row[desc_idx]:
            transaction['description'] = str(row[desc_idx]).strip()
        
        # Extract amount
        if amount_idx is not None and amount_idx < len(row) and row[amount_idx]:
            amount = parse_amount(str(row[amount_idx]))
            if amount is not None:
                transaction['amount'] = amount
        
        # If no specific columns found, try to parse the whole row
        if not transaction:
            transaction = parse_transaction_row(row)
        
        if transaction and (transaction.get('description') or transaction.get('amount') is not None):
            transactions.append(transaction)
    
    return transactions

def parse_transaction_row(row: List) -> Optional[Dict]:
    """Try to parse a transaction from a row of data"""
    if not row:
        return None
    
    transaction = {}
    
    # Convert all cells to strings
    row_strs = [str(cell).strip() if cell else '' for cell in row]
    
    # Look for date
    for cell in row_strs:
        date = parse_date_string(cell)
        if date:
            transaction['date'] = date
            transaction['date_string'] = cell
            break
    
    # Look for amount
    for cell in row_strs:
        amount = parse_amount(cell)
        if amount is not None:
            transaction['amount'] = amount
            break
    
    # Look for description (non-date, non-amount text)
    for cell in row_strs:
        if cell and not is_numeric(cell) and len(cell) > 3:
            # Skip if it's the date we already found
            if transaction.get('date_string') != cell:
                transaction['description'] = cell
                break
    
    return transaction if transaction else None

def extract_transactions_from_text(text: str) -> List[Dict]:
    """Extract transactions from plain text using patterns"""
    transactions = []
    lines = text.split('\n')
    
    # Common patterns for transactions
    patterns = [
        # Date, description, amount
        r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        # Check entries
        r'(\d{1,2}[-/]\d{1,2})\s+(\d{3,4})\s+([\d,]+\.?\d*)',
        # Description with amount
        r'^(.+?)\s+([-+]?\$?[\d,]+\.?\d*)$',
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
                    # Check if it's a check entry
                    if re.match(r'^\d{3,4}$', groups[1]):
                        # Check format
                        transaction = {
                            'date': parse_date_string(groups[0]),
                            'date_string': groups[0],
                            'description': f'CHECK {groups[1]}',
                            'amount': -abs(parse_amount(groups[2]) or 0)
                        }
                    else:
                        # Regular transaction
                        transaction = {
                            'date': parse_date_string(groups[0]),
                            'date_string': groups[0],
                            'description': groups[1].strip(),
                            'amount': parse_amount(groups[2])
                        }
                elif len(groups) == 2:
                    # Description and amount
                    transaction = {
                        'description': groups[0].strip(),
                        'amount': parse_amount(groups[1])
                    }
                else:
                    continue
                
                if transaction.get('description') or transaction.get('amount') is not None:
                    transactions.append(transaction)
                    break
    
    return transactions

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse various date formats"""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Common date formats
    formats = [
        '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
        '%m/%d/%y', '%m-%d-%y',
        '%m/%d', '%m-%d',
        '%d/%m/%Y', '%d-%m-%Y',
        '%b %d, %Y', '%B %d, %Y',
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
        # Clean the string
        amount_str = amount_str.strip()
        
        # Remove currency symbols
        amount_str = re.sub(r'[$€£¥₹]', '', amount_str)
        
        # Check for negative indicators
        is_negative = amount_str.startswith('-') or amount_str.startswith('(')
        
        # Remove signs and parentheses
        amount_str = re.sub(r'[()-+]', '', amount_str)
        
        # Remove commas
        amount_str = amount_str.replace(',', '')
        
        # Skip if not numeric
        if not re.search(r'\d', amount_str):
            return None
        
        # Convert to float
        amount = float(amount_str)
        
        # Apply sign
        if is_negative:
            amount = -amount
            
        return amount
    except ValueError:
        return None

def is_numeric(s: str) -> bool:
    """Check if string is numeric"""
    try:
        s = s.replace(',', '').replace('$', '').replace('-', '').replace('+', '')
        float(s)
        return True
    except:
        return False

# Import pandas if available
try:
    import pandas as pd
except ImportError:
    pd = None