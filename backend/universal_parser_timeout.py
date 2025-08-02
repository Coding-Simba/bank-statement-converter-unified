"""Universal PDF parser with timeout handling to prevent hanging"""

import re
import pandas as pd
from datetime import datetime
import PyPDF2
import tabula
import pdfplumber
import signal
import functools
from contextlib import contextmanager

# Timeout decorator
class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    """Context manager for timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")
    
    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore original handler and cancel alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def with_timeout(seconds):
    """Decorator to add timeout to functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with timeout(seconds):
                    return func(*args, **kwargs)
            except TimeoutException as e:
                print(f"Timeout in {func.__name__}: {e}")
                return None
        return wrapper
    return decorator

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    date_formats = [
        '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y',
        '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y', '%m/%d/%y', '%d-%b-%Y'
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
        cleaned = amount_str.strip()
        cleaned = re.sub(r'[€$£¥₹]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Handle parentheses for negative amounts
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + re.sub(r'[()]', '', cleaned)
        
        # Check if it's already negative
        is_negative = cleaned.startswith('-') or cleaned.startswith('+')
        if is_negative:
            sign = cleaned[0]
            cleaned = cleaned[1:]
        else:
            sign = ''
        
        # Determine decimal separator
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        result = float(sign + cleaned)
        return result
        
    except Exception:
        return None

def extract_transactions_from_dataframe(df):
    """Extract transactions from a pandas DataFrame"""
    transactions = []
    
    if df.empty:
        return transactions
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    # Common column name patterns
    date_patterns = ['date', 'datum', 'transaction date', 'posting date', 'value date']
    desc_patterns = ['description', 'beschrijving', 'details', 'particulars', 'transaction']
    amount_patterns = ['amount', 'bedrag', 'debit', 'credit', 'af', 'bij', 'value']
    
    # Find columns
    date_col = None
    desc_col = None
    amount_cols = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        if any(pattern in col_lower for pattern in date_patterns):
            date_col = col
        elif any(pattern in col_lower for pattern in desc_patterns):
            desc_col = col
        elif any(pattern in col_lower for pattern in amount_patterns):
            amount_cols.append(col)
    
    # Process each row
    for _, row in df.iterrows():
        transaction = {}
        
        # Extract date
        if date_col and pd.notna(row[date_col]):
            date = parse_date(str(row[date_col]))
            if date:
                transaction['date'] = date
                transaction['date_string'] = str(row[date_col])
        
        # Extract description
        if desc_col and pd.notna(row[desc_col]):
            transaction['description'] = str(row[desc_col]).strip()
        
        # Extract amount
        for col in amount_cols:
            if pd.notna(row[col]):
                amount = extract_amount(str(row[col]))
                if amount is not None:
                    transaction['amount'] = amount
                    transaction['amount_string'] = str(row[col])
                    break
        
        # Only add if we have at least date and amount
        if 'date' in transaction and 'amount' in transaction:
            transactions.append(transaction)
    
    return transactions

@with_timeout(10)  # 10 second timeout
def try_tabula_extraction(pdf_path):
    """Try tabula extraction with timeout"""
    transactions = []
    strategies = [
        {'lattice': True, 'pages': 'all'},
        {'stream': True, 'pages': 'all'},
    ]
    
    for strategy in strategies:
        try:
            tables = tabula.read_pdf(pdf_path, multiple_tables=True, silent=True, **strategy)
            
            for table in tables:
                if isinstance(table, pd.DataFrame) and len(table.columns) >= 2:
                    extracted = extract_transactions_from_dataframe(table)
                    if extracted:
                        transactions.extend(extracted)
                        
            if transactions:
                break
        except Exception as e:
            print(f"Tabula strategy failed: {e}")
            continue
    
    return transactions

@with_timeout(10)  # 10 second timeout
def try_pdfplumber_extraction(pdf_path):
    """Try pdfplumber extraction with timeout"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Limit to first 20 pages to prevent hanging
            for page in pdf.pages[:20]:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 0:
                        df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                        extracted = extract_transactions_from_dataframe(df)
                        if extracted:
                            transactions.extend(extracted)
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
    
    return transactions

@with_timeout(5)  # 5 second timeout for simple extraction
def try_pypdf2_extraction(pdf_path):
    """Try PyPDF2 extraction with timeout"""
    transactions = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Limit to first 20 pages
            pages_to_read = min(len(pdf_reader.pages), 20)
            full_text = ""
            
            for page_num in range(pages_to_read):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                full_text += text + "\n"
            
            # Simple regex pattern for common transaction formats
            pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([-+]?\s*[€$£]?\s*[\d.,]+)'
            
            for match in re.finditer(pattern, full_text, re.MULTILINE):
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                
                date = parse_date(date_str)
                amount = extract_amount(amount_str)
                
                if date and amount is not None:
                    transactions.append({
                        'date': date,
                        'date_string': date_str,
                        'description': description,
                        'amount': amount,
                        'amount_string': amount_str
                    })
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
    
    return transactions

def parse_universal_pdf_timeout(pdf_path):
    """Extract transactions from PDF with timeout protection"""
    print(f"Starting PDF parsing with timeout protection: {pdf_path}")
    transactions = []
    
    # Method 1: Try tabula (most reliable for tables)
    print("Trying tabula extraction...")
    result = try_tabula_extraction(pdf_path)
    if result:
        transactions.extend(result)
        print(f"Tabula extracted {len(result)} transactions")
    
    # Method 2: Try pdfplumber if no transactions yet
    if not transactions:
        print("Trying pdfplumber extraction...")
        result = try_pdfplumber_extraction(pdf_path)
        if result:
            transactions.extend(result)
            print(f"pdfplumber extracted {len(result)} transactions")
    
    # Method 3: Try PyPDF2 as last resort
    if not transactions:
        print("Trying PyPDF2 extraction...")
        result = try_pypdf2_extraction(pdf_path)
        if result:
            transactions.extend(result)
            print(f"PyPDF2 extracted {len(result)} transactions")
    
    # Remove duplicates
    seen = set()
    unique_transactions = []
    for trans in transactions:
        key = (trans.get('date'), trans.get('description', ''), trans.get('amount'))
        if key not in seen:
            seen.add(key)
            unique_transactions.append(trans)
    
    print(f"Total unique transactions extracted: {len(unique_transactions)}")
    return unique_transactions

# Make this the default parser
parse_universal_pdf = parse_universal_pdf_timeout