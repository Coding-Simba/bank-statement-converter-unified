from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import PyPDF2
import re
import pandas as pd
from datetime import datetime, timedelta
import io
import os
from werkzeug.utils import secure_filename
import tempfile
import tabula
from rabobank_parser import parse_rabobank_pdf

app = Flask(__name__)
CORS(app, origins=['http://localhost:8080', 'http://localhost:*', 'http://127.0.0.1:*'])

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def extract_transactions_from_pdf(pdf_path):
    """Extract transactions from PDF using multiple methods"""
    transactions = []
    
    # Method 0: Check if it's a Rabobank PDF and use dedicated parser
    try:
        # Quick check for Rabobank format
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) > 0:
                first_page = pdf_reader.pages[0].extract_text()
                if 'Rabobank' in first_page and 'Rekeningafschrift' in first_page:
                    print("Detected Rabobank PDF, using dedicated parser")
                    transactions = parse_rabobank_pdf(pdf_path)
                    if transactions:
                        return transactions
    except Exception as e:
        print(f"Rabobank detection failed: {e}")
    
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
    
    # Method 3: Fallback to PyPDF2 for text extraction
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
    
    # Remove duplicates based on date, description, and amount
    seen = set()
    unique_transactions = []
    for trans in transactions:
        key = (trans.get('date'), trans.get('description', ''), trans.get('amount'))
        if key not in seen and key[0] is not None:  # Ensure date exists
            seen.add(key)
            unique_transactions.append(trans)
    
    return unique_transactions

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

def extract_transaction_from_row(row):
    """Extract transaction details from a dataframe row"""
    transaction = {}
    
    # Convert row to string values
    values = [str(val) for val in row.values if pd.notna(val) and str(val).strip()]
    
    if len(values) < 3:
        return None
    
    # Look for date in first few columns
    for i, val in enumerate(values[:3]):
        date = parse_date(val)
        if date:
            transaction['date'] = date
            transaction['date_string'] = val
            
            # Description is usually after date
            if i + 1 < len(values):
                transaction['description'] = values[i + 1]
            
            # Amount is usually last or second to last
            for j in range(len(values) - 1, max(i, 0), -1):
                amount = extract_amount(values[j])
                if amount is not None:
                    transaction['amount'] = amount
                    transaction['amount_string'] = values[j]
                    break
            
            if 'amount' in transaction:
                return transaction
    
    return None

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
        print(f"Failed to extract amount from '{amount_str}': {e}")
        return None

def filter_transactions_by_date(transactions, start_date, end_date):
    """Filter transactions within date range"""
    filtered = []
    
    for trans in transactions:
        if 'date' in trans and trans['date']:
            if start_date <= trans['date'] <= end_date:
                filtered.append(trans)
    
    return filtered

def get_date_range_from_preset(preset):
    """Get date range based on preset selection"""
    today = datetime.now()
    
    if preset == 'last_month':
        # First day of last month
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
        
        # Last day of last month
        if today.month == 1:
            end_date = datetime(today.year, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    
    elif preset == 'last_quarter':
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 1:
                end_date = datetime(today.year, 3, 31)
            elif current_quarter == 2:
                end_date = datetime(today.year, 6, 30)
            else:
                end_date = datetime(today.year, 9, 30)
    
    elif preset == 'last_3_months':
        end_date = today
        start_date = today - timedelta(days=90)
    
    elif preset == 'last_6_months':
        end_date = today
        start_date = today - timedelta(days=180)
    
    elif preset == 'year_to_date':
        start_date = datetime(today.year, 1, 1)
        end_date = today
    
    elif preset == 'last_year':
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
    
    else:
        # Default to last month
        return get_date_range_from_preset('last_month')
    
    return start_date, end_date

@app.route('/api/split-statement', methods=['POST'])
def split_statement():
    """API endpoint to split PDF statement by date range"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract date range from request
        data = request.form
        
        if 'preset' in data and data['preset']:
            start_date, end_date = get_date_range_from_preset(data['preset'])
        else:
            # Parse custom date range
            try:
                start_date = datetime.strptime(data.get('start_date', ''), '%Y-%m-%d')
                end_date = datetime.strptime(data.get('end_date', ''), '%Y-%m-%d')
            except:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Extract transactions from PDF
        all_transactions = extract_transactions_from_pdf(filepath)
        
        if not all_transactions:
            return jsonify({'error': 'No transactions found in the PDF'}), 400
        
        # Filter transactions by date range
        filtered_transactions = filter_transactions_by_date(all_transactions, start_date, end_date)
        
        if not filtered_transactions:
            return jsonify({'error': 'No transactions found in the specified date range'}), 400
        
        # Create CSV
        csv_data = create_csv_from_transactions(filtered_transactions)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        # Return CSV file
        output = io.BytesIO()
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'transactions_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_csv_from_transactions(transactions):
    """Create CSV content from transactions"""
    df = pd.DataFrame(transactions)
    
    # Select and order columns
    columns = ['date_string', 'description', 'amount']
    if all(col in df.columns for col in columns):
        df = df[columns]
    
    # Rename columns for clarity
    df.columns = ['Date', 'Description', 'Amount']
    
    # Sort by date
    df['DateParsed'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('DateParsed')
    df = df.drop('DateParsed', axis=1)
    
    return df.to_csv(index=False)

@app.route('/api/test-extraction', methods=['POST'])
def test_extraction():
    """Test endpoint to check PDF extraction without filtering"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract all transactions
        transactions = extract_transactions_from_pdf(filepath)
        
        # Clean up
        os.remove(filepath)
        
        # Return transaction count and sample
        return jsonify({
            'total_transactions': len(transactions),
            'sample': transactions[:5] if transactions else [],
            'date_range': {
                'earliest': min([t['date'].strftime('%Y-%m-%d') for t in transactions if 'date' in t], default=None),
                'latest': max([t['date'].strftime('%Y-%m-%d') for t in transactions if 'date' in t], default=None)
            } if transactions else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)