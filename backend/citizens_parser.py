"""Parser for Citizens Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_citizens(date_str, year=None):
    """Parse Citizens date format (M/D)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to the date
        date_with_year = f"{date_str.strip()}/{year}"
        return datetime.strptime(date_with_year, "%m/%d/%Y")
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

def parse_citizens(pdf_path):
    """Parse Citizens Bank statements"""
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
        # Look for patterns like "Beginning January 17, 2021"
        period_match = re.search(r'Beginning\s+\w+\s+\d+,\s+(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find transaction sections
        in_withdrawals_section = False
        in_deposits_section = False
        current_transaction = None
        
        for i, line in enumerate(lines):
            # Look for section headers
            if 'Withdrawals & Debits' in line:
                in_withdrawals_section = True
                in_deposits_section = False
                continue
            
            if 'Deposits & Credits' in line:
                in_withdrawals_section = False
                in_deposits_section = True
                continue
            
            # End sections on certain markers
            if 'Current Balance' in line or 'Ending Balance' in line or 'SUMMARY' in line:
                # Save last transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                    current_transaction = None
                in_withdrawals_section = False
                in_deposits_section = False
                continue
            
            # Skip if not in a transaction section
            if not in_withdrawals_section and not in_deposits_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header lines
            if 'Date' in line and 'Amount' in line and 'Description' in line:
                continue
            
            # Look for transaction lines starting with date (M/D or MM/DD)
            date_match = re.match(r'^(\d{1,2}/\d{1,2})\s+(\d+\.\d{2})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(1)
                amount_str = date_match.group(2)
                description = date_match.group(3).strip()
                
                current_transaction = {
                    'date': parse_date_citizens(date_str, year),
                    'date_string': date_str,
                    'description': description,
                    'amount': None,
                    'amount_string': amount_str
                }
                
                amount = extract_amount(amount_str)
                
                if amount is not None:
                    # Apply sign based on section
                    if in_withdrawals_section:
                        amount = -abs(amount)  # Withdrawals are negative
                    elif in_deposits_section:
                        amount = abs(amount)  # Deposits are positive
                    
                    current_transaction['amount'] = amount
            
            # Handle continuation lines (descriptions that span multiple lines)
            elif current_transaction and line.strip() and not re.match(r'^\d{1,2}/\d{1,2}', line):
                # This is a continuation of the previous transaction description
                # Skip certain patterns like page numbers
                if not re.match(r'^\s*\d+\s*$', line) and 'Page' not in line:
                    current_transaction['description'] += ' ' + line.strip()
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Citizens Bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions