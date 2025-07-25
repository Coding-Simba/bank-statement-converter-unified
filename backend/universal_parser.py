"""Universal PDF parser for bank statements - supports multiple banks and formats"""

import re
import pandas as pd
from datetime import datetime
import PyPDF2
import tabula
from .rabobank_parser import parse_rabobank_pdf
from .pdftotext_parser import parse_pdftotext_output
from .ocr_parser import parse_scanned_pdf, is_scanned_pdf, check_ocr_requirements
try:
    from .advanced_ocr_parser import parse_scanned_pdf_advanced
    ADVANCED_OCR_AVAILABLE = True
except ImportError:
    ADVANCED_OCR_AVAILABLE = False
try:
    from .dummy_pdf_parser import parse_dummy_pdf
    DUMMY_PARSER_AVAILABLE = True
except ImportError:
    DUMMY_PARSER_AVAILABLE = False
try:
    from .camelot_parser import parse_with_camelot, parse_with_pdfplumber
    CAMELOT_PARSER_AVAILABLE = True
except ImportError:
    CAMELOT_PARSER_AVAILABLE = False
    print("Camelot parser not available")
try:
    from .failed_pdf_manager import FailedPDFManager
    FAILED_PDF_MANAGER_AVAILABLE = True
except ImportError:
    FAILED_PDF_MANAGER_AVAILABLE = False

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
        cleaned = amount_str.strip()
        
        # Remove currency symbols
        cleaned = re.sub(r'[€$£¥₹]', '', cleaned)
        
        # Remove spaces
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
        # If there's both comma and dot, the last one is the decimal separator
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # Comma is decimal separator (European format)
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Dot is decimal separator (US format)
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Check if comma is thousand separator or decimal
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely thousand separator
                cleaned = cleaned.replace(',', '')
        
        # Convert to float
        result = float(sign + cleaned)
        return result
        
    except Exception as e:
        # Silently fail for non-numeric values like headers
        return None

def extract_transactions_from_dataframe(df):
    """Extract transactions from a pandas DataFrame"""
    transactions = []
    
    if df.empty:
        return transactions
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    # Common column name patterns for dates, descriptions, and amounts
    date_patterns = ['date', 'datum', 'transaction date', 'posting date', 'value date']
    desc_patterns = ['description', 'beschrijving', 'details', 'particulars', 'transaction', 'omschrijving']
    amount_patterns = ['amount', 'bedrag', 'debit', 'credit', 'af', 'bij', 'value', 'withdrawal', 'deposit']
    
    # Find columns
    date_col = None
    desc_col = None
    amount_cols = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Find date column
        if any(pattern in col_lower for pattern in date_patterns):
            date_col = col
        
        # Find description column
        elif any(pattern in col_lower for pattern in desc_patterns):
            desc_col = col
        
        # Find amount columns
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
        
        # Try to find date in other columns if not found
        if 'date' not in transaction:
            for col in df.columns:
                if pd.notna(row[col]):
                    date = parse_date(str(row[col]))
                    if date:
                        transaction['date'] = date
                        transaction['date_string'] = str(row[col])
                        break
        
        # Extract description
        if desc_col and pd.notna(row[desc_col]):
            transaction['description'] = str(row[desc_col]).strip()
        else:
            # Try to find description in non-numeric columns
            for col in df.columns:
                if col != date_col and pd.notna(row[col]):
                    val = str(row[col]).strip()
                    if val and not val.replace('-', '').replace('.', '').replace(',', '').isdigit():
                        transaction['description'] = val
                        break
        
        # Extract amount
        for col in amount_cols:
            if pd.notna(row[col]):
                amount = extract_amount(str(row[col]))
                if amount is not None:
                    transaction['amount'] = amount
                    transaction['amount_string'] = str(row[col])
                    break
        
        # If no amount found in designated columns, check all columns
        if 'amount' not in transaction:
            for col in df.columns:
                if col not in [date_col, desc_col] and pd.notna(row[col]):
                    amount = extract_amount(str(row[col]))
                    if amount is not None and amount != 0:
                        transaction['amount'] = amount
                        transaction['amount_string'] = str(row[col])
                        break
        
        # Only add if we have at least date and amount
        if 'date' in transaction and 'amount' in transaction:
            transactions.append(transaction)
    
    return transactions

def extract_transactions_from_text(text):
    """Extract transactions from plain text using regex patterns"""
    transactions = []
    
    # Common transaction patterns for various banks
    patterns = [
        # Standard format: Date Description Amount
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([-+]?\s*[€$£]?\s*[\d.,]+(?:\.\d{2})?)\s*$',
        
        # Rabobank format: DD-MM-YYYY description amount (AF/BIJ)
        r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d.,]+)\s+(AF|BIJ)',
        
        # European format with comma as decimal separator
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([-+]?\s*€?\s*[\d.]+,\d{2})',
        
        # Date at start with various separators
        r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s+(.+?)\s+([-+]?\s*[€$£]?\s*[\d,]+\.?\d*)',
        
        # Date with month name: 01-Jan-2024
        r'(\d{1,2}-\w{3}-\d{2,4})\s+(.+?)\s+([-+]?\s*[€$£]?\s*[\d,]+\.?\d*)',
        
        # With reference numbers
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d+\s+(.+?)\s+([-+]?\s*[€$£]?\s*[\d,]+\.?\d*)',
        
        # Multiline transaction (date on one line, details below)
        r'^(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s*$',
    ]
    
    # Additional patterns for amount extraction
    amount_patterns = [
        r'([-+]?\s*[€$£]?\s*[\d.,]+(?:[,.]\d{2})?)\s*(?:AF|BIJ|DR|CR)?',
        r'(?:AF|BIJ|DR|CR)\s*([\d.,]+(?:[,.]\d{2})?)',
    ]
    
    lines = text.split('\n')
    
    # Try line-by-line extraction
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        transaction_found = False
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) >= 3:
                    # Standard pattern with date, description, amount
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3)
                    
                    # Check for AF/BIJ indicator (Rabobank)
                    is_debit = False
                    if len(match.groups()) >= 4:
                        indicator = match.group(4)
                        is_debit = indicator == 'AF'
                    
                    date = parse_date(date_str)
                    if date:
                        amount = extract_amount(amount_str)
                        if amount is not None:
                            if is_debit:
                                amount = -abs(amount)
                            
                            transactions.append({
                                'date': date,
                                'date_string': date_str,
                                'description': description,
                                'amount': amount,
                                'amount_string': amount_str
                            })
                            transaction_found = True
                            break
                elif len(match.groups()) == 1:
                    # Date only pattern - look for details in next lines
                    date_str = match.group(1)
                    date = parse_date(date_str)
                    if date and i + 1 < len(lines):
                        # Look for description and amount in next lines
                        desc_line = lines[i + 1].strip()
                        amount_line = lines[i + 2].strip() if i + 2 < len(lines) else ""
                        
                        # Extract amount from current or next lines
                        amount = None
                        amount_str = ""
                        for amt_pattern in amount_patterns:
                            amt_match = re.search(amt_pattern, desc_line + " " + amount_line)
                            if amt_match:
                                amount_str = amt_match.group(1)
                                amount = extract_amount(amount_str)
                                break
                        
                        if amount is not None:
                            # Clean description
                            description = re.sub(r'[-+]?\s*[€$£]?\s*[\d.,]+(?:[,.]\d{2})?\s*(?:AF|BIJ|DR|CR)?', '', desc_line).strip()
                            
                            transactions.append({
                                'date': date,
                                'date_string': date_str,
                                'description': description or "Transaction",
                                'amount': amount,
                                'amount_string': amount_str
                            })
                            transaction_found = True
                            i += 2  # Skip processed lines
                            break
        
        if not transaction_found:
            i += 1
    
    return transactions

def parse_universal_pdf(pdf_path):
    """Extract transactions from PDF using multiple methods"""
    transactions = []
    
    # Method 0: Check for specific PDF formats with dedicated parsers
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) > 0:
                first_page = pdf_reader.pages[0].extract_text()
                
                # Check for dummy PDF format
                # Since dummy PDF might be scanned, also check filename
                is_dummy = ('SAMPLE' in first_page and 'Statement of Account' in first_page and 'JAMES C. MORRISON' in first_page) or \
                          'dummy' in pdf_path.lower()
                
                if DUMMY_PARSER_AVAILABLE and is_dummy:
                    print("Detected dummy statement PDF, using specialized parser")
                    transactions = parse_dummy_pdf(pdf_path)
                    if transactions:
                        return transactions
                
                # Check for Rabobank format
                if 'Rabobank' in first_page and 'Rekeningafschrift' in first_page:
                    print("Detected Rabobank PDF, using dedicated parser")
                    transactions = parse_rabobank_pdf(pdf_path)
                    if transactions:
                        return transactions
    except Exception as e:
        print(f"Format detection failed: {e}")
    
    # Method 1: Try tabula-py for table extraction (most reliable for bank statements)
    try:
        # Try different extraction strategies
        strategies = [
            {'lattice': True, 'pages': 'all'},  # For tables with visible borders
            {'stream': True, 'pages': 'all'},   # For tables without borders
            {'lattice': False, 'stream': True, 'pages': 'all', 'guess': True}  # Auto-detect
        ]
        
        for strategy in strategies:
            try:
                tables = tabula.read_pdf(pdf_path, multiple_tables=True, silent=True, **strategy)
                
                for table in tables:
                    if isinstance(table, pd.DataFrame) and len(table.columns) >= 2:
                        # Process each table
                        extracted = extract_transactions_from_dataframe(table)
                        if extracted:
                            transactions.extend(extracted)
                            
                if transactions:
                    break  # If we found transactions, stop trying other strategies
            except Exception as e:
                print(f"Tabula strategy failed: {e}")
                continue
    except Exception as e:
        print(f"Tabula extraction failed completely: {e}")
    
    # Method 2: Use pdfplumber for better text extraction
    if not transactions:
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 0:
                            # Convert to DataFrame for easier processing
                            df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                            extracted = extract_transactions_from_dataframe(df)
                            if extracted:
                                transactions.extend(extracted)
                    
                    # Also extract text for regex parsing
                    text = page.extract_text()
                    if text:
                        extracted = extract_transactions_from_text(text)
                        if extracted:
                            transactions.extend(extracted)
        except ImportError:
            print("pdfplumber not installed, falling back to PyPDF2")
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
    
    # Method 3: Try Camelot for better table extraction
    if not transactions and CAMELOT_PARSER_AVAILABLE:
        try:
            print("Trying Camelot for table extraction...")
            extracted = parse_with_camelot(pdf_path)
            if extracted:
                transactions.extend(extracted)
                print(f"Extracted {len(extracted)} transactions using Camelot")
        except Exception as e:
            print(f"Camelot extraction failed: {e}")
            # Try pdfplumber as fallback
            try:
                print("Trying pdfplumber as fallback...")
                extracted = parse_with_pdfplumber(pdf_path)
                if extracted:
                    transactions.extend(extracted)
                    print(f"Extracted {len(extracted)} transactions using pdfplumber")
            except Exception as e2:
                print(f"pdfplumber extraction also failed: {e2}")
    
    # Method 4: Try pdftotext command line tool
    if not transactions:
        try:
            extracted = parse_pdftotext_output(pdf_path)
            if extracted:
                transactions.extend(extracted)
                print(f"Extracted {len(extracted)} transactions using pdftotext")
        except Exception as e:
            print(f"pdftotext extraction failed: {e}")
    
    # Method 5: Fallback to PyPDF2 for text extraction
    if not transactions:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                full_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    full_text += text + "\n"
                
                # Extract transactions using regex patterns
                transactions = extract_transactions_from_text(full_text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
    
    # Method 6: OCR for scanned PDFs or complex layouts (last resort)
    # Always try OCR if we have very few transactions
    if len(transactions) <= 1:
        # Check if OCR is available
        ocr_ready, message = check_ocr_requirements()
        if ocr_ready:
            print(f"Only {len(transactions)} transactions found, attempting OCR for better extraction...")
            
            # Try advanced OCR parser first for complex layouts
            if ADVANCED_OCR_AVAILABLE:
                try:
                    print("Trying advanced OCR parser for complex layouts...")
                    ocr_transactions = parse_scanned_pdf_advanced(pdf_path)
                    if ocr_transactions and len(ocr_transactions) > len(transactions):
                        print(f"Successfully extracted {len(ocr_transactions)} transactions using advanced OCR")
                        transactions = ocr_transactions
                except Exception as e:
                    print(f"Advanced OCR extraction failed: {e}")
            
            # Fall back to standard OCR parser if advanced didn't work
            if len(transactions) <= 1:
                try:
                    print("Trying standard OCR parser...")
                    ocr_transactions = parse_scanned_pdf(pdf_path)
                    if ocr_transactions and len(ocr_transactions) > len(transactions):
                        print(f"Successfully extracted {len(ocr_transactions)} transactions using standard OCR")
                        transactions = ocr_transactions
                except Exception as e:
                    print(f"Standard OCR extraction failed: {e}")
        else:
            print(f"OCR not available: {message}")
    
    # Remove duplicates based on date, description, and amount
    seen = set()
    unique_transactions = []
    for trans in transactions:
        # Create a key for deduplication
        date_val = trans.get('date')
        desc_val = trans.get('description', '')
        amount_val = trans.get('amount')
        
        # Only skip if we have no useful data at all
        if not desc_val and amount_val is None:
            continue
            
        key = (date_val, desc_val, amount_val)
        if key not in seen:
            seen.add(key)
            unique_transactions.append(trans)
    
    # Check if parsing was successful and save failed PDFs
    if FAILED_PDF_MANAGER_AVAILABLE:
        try:
            manager = FailedPDFManager()
            success = manager.check_parsing_success(pdf_path, unique_transactions)
            
            if not success:
                # Parsing failed or was incomplete
                print(f"Parsing was incomplete for {pdf_path}, saving for improvement...")
                saved_path = manager.save_failed_pdf(pdf_path, unique_transactions)
                if saved_path:
                    print(f"Failed PDF saved to: {saved_path}")
        except Exception as e:
            print(f"Error in failed PDF management: {e}")
    
    return unique_transactions