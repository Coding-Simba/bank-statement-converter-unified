"""Camelot parser for extracting tables from PDFs with debugging"""

import camelot
import pandas as pd
from datetime import datetime
import re

def debug_print(message):
    """Print debug messages with timestamp"""
    print(f"[CAMELOT DEBUG {datetime.now().strftime('%H:%M:%S')}] {message}")

def is_valid_transaction(row_data):
    """
    Validate if a row contains actual transaction data.
    Filters out headers, addresses, and other non-transaction content.
    """
    # Convert row to string for analysis
    row_text = ' '.join(str(cell) for cell in row_data if cell)
    
    # List of header/non-transaction patterns to exclude
    exclude_patterns = [
        # Bank names and headers
        r'bank\s*of\s*america',
        r'wells\s*fargo',
        r'chase',
        r'citibank',
        r'capital\s*one',
        
        # Address patterns
        r'p\.?o\.?\s*box',
        r'customer\s*service',
        r'member\s*fdic',
        r'your\s*account\s*statement',
        r'statement\s*of\s*account',
        r'issue\s*date',
        r'period:',
        r'account\s*number',
        r'routing\s*number',
        
        # Page headers/footers
        r'page\s*\d+\s*of',
        r'continued\s*on\s*next',
        r'subtotal',
        r'total',
        r'balance\s*forward',
        
        # Column headers
        r'date\s*description\s*amount',
        r'transaction\s*date',
        r'posting\s*date',
        r'reference\s*number',
        
        # Empty or minimal content
        r'^\s*$',  # Empty rows
        r'^[-\s]+$',  # Separator lines
    ]
    
    # Check if row matches any exclude pattern
    for pattern in exclude_patterns:
        if re.search(pattern, row_text, re.IGNORECASE):
            debug_print(f"Filtered out: {row_text[:100]}...")
            return False
    
    # Check if row has minimum required data
    # Should have at least 2 non-empty cells
    non_empty_cells = [cell for cell in row_data if cell and str(cell).strip()]
    if len(non_empty_cells) < 2:
        debug_print(f"Too few cells: {row_data}")
        return False
    
    # Check if there's at least one potential amount
    has_amount = False
    for cell in row_data:
        if cell and re.search(r'\d+\.?\d*', str(cell)):
            has_amount = True
            break
    
    if not has_amount:
        debug_print(f"No amount found: {row_data}")
        return False
    
    return True

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    date_formats = [
        '%m/%d/%Y',
        '%m-%d-%Y', 
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%b %d, %Y',
        '%B %d, %Y',
        '%m/%d/%y',
        '%d-%b-%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except ValueError:
            continue
    return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    try:
        if not amount_str:
            return None
            
        # Clean the string
        cleaned = str(amount_str).strip()
        
        # Remove currency symbols
        cleaned = re.sub(r'[€$£¥₹]', '', cleaned)
        
        # Remove commas (thousand separators)
        cleaned = cleaned.replace(',', '')
        
        # Handle parentheses for negative amounts
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + re.sub(r'[()]', '', cleaned)
        
        # Convert to float
        return float(cleaned)
        
    except Exception as e:
        return None

def parse_with_camelot(pdf_path):
    """Extract transactions using Camelot with debugging"""
    transactions = []
    
    try:
        debug_print(f"Starting Camelot extraction for: {pdf_path}")
        
        # Try different Camelot extraction methods
        methods = ['lattice', 'stream']
        
        for method in methods:
            debug_print(f"Trying Camelot with method: {method}")
            
            try:
                # Extract tables using Camelot
                tables = camelot.read_pdf(pdf_path, pages='all', flavor=method)
                debug_print(f"Found {len(tables)} tables with {method} method")
                
                for i, table in enumerate(tables):
                    debug_print(f"Processing table {i+1}/{len(tables)}")
                    
                    # Convert to pandas DataFrame
                    df = table.df
                    debug_print(f"Table shape: {df.shape}")
                    
                    if df.empty:
                        continue
                    
                    # Process each row
                    for idx, row in df.iterrows():
                        row_data = row.tolist()
                        
                        # Skip invalid rows
                        if not is_valid_transaction(row_data):
                            continue
                        
                        transaction = {}
                        
                        # Try to extract date, description, and amount
                        for j, cell in enumerate(row_data):
                            if not cell:
                                continue
                            
                            cell_str = str(cell).strip()
                            
                            # Try to parse as date
                            if 'date' not in transaction:
                                date = parse_date(cell_str)
                                if date:
                                    transaction['date'] = date
                                    transaction['date_string'] = cell_str
                                    continue
                            
                            # Try to parse as amount
                            if 'amount' not in transaction:
                                amount = extract_amount(cell_str)
                                if amount is not None and amount != 0:
                                    transaction['amount'] = amount
                                    transaction['amount_string'] = cell_str
                                    continue
                            
                            # Use as description if we don't have one
                            if 'description' not in transaction and len(cell_str) > 3:
                                transaction['description'] = cell_str
                        
                        # Only add if we have required fields
                        if 'date' in transaction and 'amount' in transaction:
                            if 'description' not in transaction:
                                transaction['description'] = "Transaction"
                            
                            debug_print(f"Valid transaction: {transaction}")
                            transactions.append(transaction)
                
                # If we found transactions, stop trying other methods
                if transactions:
                    debug_print(f"Found {len(transactions)} transactions with {method} method")
                    break
                    
            except Exception as e:
                debug_print(f"Error with {method} method: {str(e)}")
                continue
        
        debug_print(f"Total transactions extracted: {len(transactions)}")
        
    except Exception as e:
        debug_print(f"Camelot extraction failed: {str(e)}")
        raise
    
    return transactions

def parse_with_pdfplumber(pdf_path):
    """Fallback parser using pdfplumber with debugging"""
    import pdfplumber
    
    transactions = []
    
    try:
        debug_print(f"Starting pdfplumber extraction for: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                debug_print(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                
                # Extract tables
                tables = page.extract_tables()
                
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue
                    
                    debug_print(f"Found table {table_idx + 1} with {len(table)} rows")
                    
                    for row in table:
                        if not is_valid_transaction(row):
                            continue
                        
                        transaction = {}
                        
                        # Process each cell in the row
                        for cell in row:
                            if not cell:
                                continue
                            
                            cell_str = str(cell).strip()
                            
                            # Try to parse as date
                            if 'date' not in transaction:
                                date = parse_date(cell_str)
                                if date:
                                    transaction['date'] = date
                                    transaction['date_string'] = cell_str
                                    continue
                            
                            # Try to parse as amount
                            if 'amount' not in transaction:
                                amount = extract_amount(cell_str)
                                if amount is not None and amount != 0:
                                    transaction['amount'] = amount
                                    transaction['amount_string'] = cell_str
                                    continue
                            
                            # Use as description
                            if 'description' not in transaction and len(cell_str) > 3:
                                transaction['description'] = cell_str
                        
                        # Only add if we have required fields
                        if 'date' in transaction and 'amount' in transaction:
                            if 'description' not in transaction:
                                transaction['description'] = "Transaction"
                            
                            debug_print(f"Valid transaction: {transaction}")
                            transactions.append(transaction)
        
        debug_print(f"Total transactions extracted with pdfplumber: {len(transactions)}")
        
    except Exception as e:
        debug_print(f"pdfplumber extraction failed: {str(e)}")
        raise
    
    return transactions