"""Parser for Netspend Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_netspend(date_str, year=None):
    """Parse Netspend date format (Mon D or Mon DD)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to the date
        date_with_year = f"{date_str.strip()} {year}"
        return datetime.strptime(date_with_year, "%b %d %Y")
    except:
        try:
            # Try with single digit day
            return datetime.strptime(date_with_year, "%b %d %Y")
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

def parse_netspend(pdf_path):
    """Parse Netspend Bank statements"""
    transactions = []
    
    try:
        # Extract text with layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        text = result.stdout
        
        # Extract year from statement date
        year = None
        # Look for "Account Summary Month DD, YYYY"
        date_match = re.search(r'Account Summary\s+\w+\s+\d+,\s+(\d{4})', text)
        if date_match:
            year = int(date_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find transaction table
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Look for "Your Transaction Details" header
            if 'Your Transaction Details' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'Closing Balance' in line and '$' in line:
                in_transaction_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header line
            if 'Date' in line and 'Details' in line and 'Withdrawals' in line:
                continue
            
            # Skip Opening Balance line
            if 'Opening Balance' in line:
                continue
            
            # Look for transaction lines starting with date pattern
            date_match = re.match(r'^([A-Z][a-z]{2}\s+\d{1,2})\s+', line)
            
            if date_match:
                date_str = date_match.group(1)
                
                # Parse the rest of the line by column positions
                # Approximate column positions based on the header:
                # Date (0-15), Details (16-47), Withdrawals (48-71), Deposits (72-95), Balance (96+)
                
                if len(line) > 48:
                    description = line[16:48].strip()
                    withdrawal_part = line[48:72].strip() if len(line) > 48 else ""
                    deposit_part = line[72:96].strip() if len(line) > 72 else ""
                    balance_part = line[96:].strip() if len(line) > 96 else ""
                    
                    # Parse date
                    trans_date = parse_date_netspend(date_str, year)
                    
                    if trans_date:
                        # Determine amount and type
                        amount = None
                        amount_str = None
                        
                        # Check for withdrawal amount
                        if withdrawal_part:
                            withdrawal_amount = extract_amount(withdrawal_part)
                            if withdrawal_amount:
                                amount = -withdrawal_amount  # Withdrawals are negative
                                amount_str = withdrawal_part
                        
                        # Check for deposit amount
                        if not amount and deposit_part:
                            deposit_amount = extract_amount(deposit_part)
                            if deposit_amount:
                                amount = deposit_amount  # Deposits are positive
                                amount_str = deposit_part
                        
                        if amount is not None:
                            transaction = {
                                'date': trans_date,
                                'date_string': date_str,
                                'description': description,
                                'amount': amount,
                                'amount_string': amount_str,
                                'balance': extract_amount(balance_part)
                            }
                            
                            transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Netspend statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions