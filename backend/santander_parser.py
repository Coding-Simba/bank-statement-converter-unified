"""Parser for Santander UK bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_santander(date_str, year=None):
    """Parse Santander date format (12th Feb, 1st Mar, etc)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Remove ordinal suffixes (st, nd, rd, th)
        cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str.strip())
        # Add year
        date_with_year = f"{cleaned} {year}"
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
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_santander(pdf_path):
    """Parse Santander UK bank statements with multi-line transaction format"""
    transactions = []
    
    try:
        # Extract text with layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        text = result.stdout
        
        # Extract year from statement period
        year = None
        period_match = re.search(r'(\w+)\s+(\d{4})\s+to\s+\d+\w+\s+(\w+)\s+(\d{4})', text)
        if period_match:
            # Use the end year
            year = int(period_match.group(4))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find the transaction table
        in_transaction_section = False
        current_transaction = None
        
        for i, line in enumerate(lines):
            # Look for transaction header
            if 'Date' in line and 'Description' in line and 'Money in' in line and 'Money out' in line:
                in_transaction_section = True
                continue
            
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check if this is a date line (starts with date)
            date_match = re.match(r'^(\d{1,2}(?:st|nd|rd|th)\s+\w{3})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                current_transaction = {
                    'date': parse_date_santander(date_str, year),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Check if this line has amounts
                # Look for pattern with proper spacing between amounts
                # Santander format has significant spacing between columns
                
                # Try to find amounts with spacing pattern
                # Money in/out will have spacing before balance
                money_match = re.search(r'(.+?)\s{2,}([\d,]+\.?\d*)\s{2,}([\d,]+\.?\d*\s*\d*)\s*$', rest_of_line)
                
                if money_match:
                    description = money_match.group(1).strip()
                    trans_amount_str = money_match.group(2)
                    balance_str = money_match.group(3)
                    
                    trans_amount = extract_amount(trans_amount_str)
                    
                    if trans_amount:
                        # Check if description suggests deposit
                        if re.search(r'BANK GIRO CREDIT|FASTER PAYMENT FROM|DEPOSIT|CREDIT', description, re.I):
                            # This is money in
                            current_transaction['amount'] = trans_amount
                        else:
                            # This is money out
                            current_transaction['amount'] = -trans_amount
                        
                        current_transaction['amount_string'] = trans_amount_str
                        current_transaction['description'] = description
                else:
                    # No clear amount pattern, just get description
                    current_transaction['description'] = rest_of_line.strip()
            
            # Handle continuation lines
            elif current_transaction and line.strip():
                # Check if this is a continuation of the description
                # Look for patterns that indicate continuation (reference numbers, etc)
                if re.match(r'^\s+\d{4}$', line) or 'MANDATE NO' in line:
                    # This is a continuation
                    current_transaction['description'] += ' ' + line.strip()
                    
                    # Check if the next line has amounts
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        amounts = re.findall(r'([\d,]+\.?\d*)', next_line)
                        
                        # Skip if the next line is a date
                        if not re.match(r'^\d{1,2}(?:st|nd|rd|th)\s+\w{3}', next_line) and amounts and len(amounts) >= 2:
                            # This line has the amounts for the current transaction
                            # Extract the transaction amount (second to last)
                            trans_amount = extract_amount(amounts[-2])
                            
                            if trans_amount and current_transaction['amount'] is None:
                                # Determine if deposit or withdrawal
                                if re.search(r'BANK GIRO CREDIT|FASTER PAYMENT FROM|DEPOSIT|CREDIT', 
                                           current_transaction['description'], re.I):
                                    current_transaction['amount'] = trans_amount
                                else:
                                    current_transaction['amount'] = -trans_amount
                                
                                current_transaction['amount_string'] = amounts[-2]
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Santander statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions