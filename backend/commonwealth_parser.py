"""Parser for Commonwealth Bank of Australia statements"""

import re
from datetime import datetime
import subprocess

def parse_date_commonwealth(date_str):
    """Parse Commonwealth Bank date format (01 Jul, 15 Aug, etc)"""
    # Add current year since it's not in the date
    current_year = datetime.now().year
    
    try:
        # Try with current year first
        date_with_year = f"{date_str} {current_year}"
        return datetime.strptime(date_with_year, "%d %b %Y")
    except:
        try:
            # Try with previous year if that fails
            date_with_year = f"{date_str} {current_year - 1}"
            return datetime.strptime(date_with_year, "%d %b %Y")
        except:
            return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_commonwealth_bank(pdf_path):
    """Parse Commonwealth Bank of Australia statements"""
    transactions = []
    
    try:
        # Extract text with layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        lines = result.stdout.split('\n')
        
        # Find the transaction table header
        header_found = False
        debit_pos = None
        credit_pos = None
        balance_pos = None
        
        for i, line in enumerate(lines):
            # Look for header line
            if 'Date' in line and 'Transaction' in line and 'Debit' in line and 'Credit' in line:
                header_found = True
                # Find column positions
                debit_pos = line.find('Debit')
                credit_pos = line.find('Credit')
                balance_pos = line.find('Balance')
                print(f"Found header at line {i}, Debit pos: {debit_pos}, Credit pos: {credit_pos}")
                break
        
        if not header_found:
            print("Could not find transaction table header")
            return transactions
        
        # Process transaction lines
        current_date = None
        header_line_index = None
        
        # Find the actual header line index
        for i, line in enumerate(lines):
            if header_found and 'Date' in line and 'Transaction' in line:
                header_line_index = i
                break
        
        if header_line_index is None:
            return transactions
        
        for i, line in enumerate(lines):
            # Skip lines before header
            if i <= header_line_index:
                continue
            
            if not line.strip():
                continue
            
            # Check if line starts with a date (DD Mon format)
            # Account for various indentations
            date_match = re.match(r'^\s*(\d{2}\s+[A-Za-z]{3})\s+', line)
            
            if date_match:
                # This is a new transaction
                date_str = date_match.group(1).strip()
                current_date = parse_date_commonwealth(date_str)
                
                if current_date:
                    # Extract the rest of the line after date
                    rest_of_line = line[len(date_match.group(0)):]
                    
                    # Find amounts in debit/credit columns
                    debit_amount = None
                    credit_amount = None
                    
                    # Extract potential amounts based on position
                    if debit_pos and credit_pos:
                        # Get text in debit column area (roughly)
                        debit_area = rest_of_line[max(0, debit_pos-15):credit_pos-5].strip()
                        credit_area = rest_of_line[credit_pos-5:balance_pos-5].strip() if balance_pos else rest_of_line[credit_pos-5:].strip()
                        
                        # Look for amounts
                        debit_match = re.search(r'([\d,]+\.?\d*)\s*$', debit_area)
                        credit_match = re.search(r'([\d,]+\.?\d*)\s*$', credit_area)
                        
                        if debit_match:
                            debit_amount = extract_amount(debit_match.group(1))
                        if credit_match:
                            credit_amount = extract_amount(credit_match.group(1))
                    
                    # Extract description (everything before the amounts)
                    desc_end = len(rest_of_line)
                    if debit_amount or credit_amount:
                        # Find where the amount starts
                        amount_match = re.search(r'[\d,]+\.?\d*\s*[\d,]+\.?\d*\s*[A-Z]{2}\s*$', rest_of_line)
                        if amount_match:
                            desc_end = amount_match.start()
                        else:
                            # Just look for first amount
                            first_amount = re.search(r'\s+([\d,]+\.?\d*)\s*$', rest_of_line)
                            if first_amount:
                                desc_end = first_amount.start()
                    
                    description = rest_of_line[:desc_end].strip()
                    
                    # Determine transaction amount and type
                    if debit_amount:
                        amount = -abs(debit_amount)  # Debits are negative
                    elif credit_amount:
                        amount = abs(credit_amount)   # Credits are positive
                    else:
                        continue  # Skip if no amount found
                    
                    transaction = {
                        'date': current_date,
                        'date_string': date_str,
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    }
                    
                    transactions.append(transaction)
            
            elif current_date and line.strip() and not line.strip().startswith('Date'):
                # This might be a continuation line (additional description)
                # Check if it contains transaction info
                if 'Card xx' in line or 'Value Date:' in line:
                    # Add to previous transaction's description if exists
                    if transactions and transactions[-1]['date'] == current_date:
                        transactions[-1]['description'] += ' ' + line.strip()
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Commonwealth Bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions