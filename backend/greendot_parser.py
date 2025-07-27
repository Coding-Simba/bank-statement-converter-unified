"""Parser for Green Dot Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_greendot(date_str, year=None):
    """Parse Green Dot date format (MM/DD)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to the date
        date_with_year = f"{date_str.strip()}/{year}"
        return datetime.strptime(date_with_year, "%m/%d/%Y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling +/- signs"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check sign
        is_negative = cleaned.startswith('-')
        is_positive = cleaned.startswith('+')
        
        if is_negative or is_positive:
            cleaned = cleaned[1:]
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        result = float(cleaned)
        
        # Apply sign
        if is_negative:
            result = -result
            
        return result
    except:
        return None

def parse_greendot(pdf_path):
    """Parse Green Dot Bank statements"""
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
        # Look for "Statement Period MM/DD/YYYY-MM/DD/YYYY"
        period_match = re.search(r'Statement Period\s+\d{2}/\d{2}/(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find transaction sections
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Look for "DEBIT ACCOUNT TRANSACTIONS" header
            if 'DEBIT ACCOUNT TRANSACTIONS' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'No transactions during this period' in line or 'HIGH YIELD SAVINGS' in line:
                in_transaction_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header line
            if 'Date' in line and 'Description' in line and 'Type' in line:
                continue
            
            # Look for transaction lines with format: MM/DD   Description   Type   +/-$amount   $balance
            trans_match = re.match(r'^(\d{2}/\d{2})\s+(.+?)\s+(Deposit|Fee|Withdrawal|Transfer|Purchase)\s+([-+]?\$[\d,]+\.\d{2})\s+\$[\d,]+\.\d{2}\s*$', line)
            
            if trans_match:
                date_str = trans_match.group(1)
                description = trans_match.group(2).strip()
                trans_type = trans_match.group(3)
                amount_str = trans_match.group(4)
                
                # Parse date
                trans_date = parse_date_greendot(date_str, year)
                
                if trans_date:
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        transaction = {
                            'date': trans_date,
                            'date_string': date_str,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str,
                            'type': trans_type
                        }
                        
                        transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Green Dot statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions