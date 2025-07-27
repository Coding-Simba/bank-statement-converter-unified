"""Parser for BECU (Boeing Employees' Credit Union) bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_becu(date_str, year=None):
    """Parse BECU date format (MM/DD)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to the date
        date_with_year = f"{date_str.strip()}/{year}"
        return datetime.strptime(date_with_year, "%m/%d/%Y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling parentheses for negative"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check if it's negative (in parentheses)
        is_negative = cleaned.startswith('(') and cleaned.endswith(')')
        if is_negative:
            cleaned = cleaned[1:-1]  # Remove parentheses
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        result = float(cleaned)
        
        # Apply negative sign if needed
        if is_negative:
            result = -result
            
        return result
    except:
        return None

def parse_becu(pdf_path):
    """Parse BECU bank statements"""
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
        period_match = re.search(r'Statement Period:.*?(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find deposit and withdrawal sections for each account
        in_deposits_section = False
        in_withdrawals_section = False
        current_transaction = None
        
        for i, line in enumerate(lines):
            # Look for section headers
            if line.strip() == 'Deposits':
                # Check if next line has Date header
                if i + 1 < len(lines) and 'Date' in lines[i + 1]:
                    in_deposits_section = True
                    in_withdrawals_section = False
                    continue
            
            if line.strip() == 'Withdrawals':
                # Check if next line has Date header
                if i + 1 < len(lines) and 'Date' in lines[i + 1]:
                    in_deposits_section = False
                    in_withdrawals_section = True
                    continue
            
            # End sections on certain markers
            if 'Member Advantage' in line or 'Deposit Account Activity' in line or 'Page' in line:
                # Save last transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                    current_transaction = None
                in_deposits_section = False
                in_withdrawals_section = False
                continue
            
            # Skip if not in a transaction section - but still try to parse if it looks like a transaction
            if not in_deposits_section and not in_withdrawals_section:
                # Check if this line looks like a transaction anyway
                if not re.match(r'^\s*(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])\s+', line):
                    continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for transaction lines starting with date (MM/DD)
            date_match = re.match(r'^\s*(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = f"{date_match.group(1)}/{date_match.group(2)}"
                rest_of_line = date_match.group(3)
                
                current_transaction = {
                    'date': parse_date_becu(date_str, year),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Check if amount is on this line
                # BECU format has amount before description with lots of spaces
                # Look for amount patterns like 150.00 or (150.00)
                amount_match = re.match(r'^\s*(\(?[\d,]+\.?\d*\)?)\s+(.+)', rest_of_line)
                
                if amount_match:
                    amount_str = amount_match.group(1)
                    description = amount_match.group(2).strip()
                    
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # Apply sign based on section or amount format
                        if in_deposits_section and amount < 0:
                            amount = -amount  # Make positive
                        elif in_withdrawals_section and amount > 0:
                            amount = -amount  # Make negative
                        elif not in_deposits_section and not in_withdrawals_section:
                            # If not in any section, use the natural sign from parentheses
                            # Amounts in parentheses are already negative from extract_amount
                            pass
                        
                        current_transaction['amount'] = amount
                        current_transaction['amount_string'] = amount_str
                        current_transaction['description'] = description
                else:
                    # No clear amount pattern
                    current_transaction['description'] = rest_of_line.strip()
            
            # Handle continuation lines (for multi-line descriptions)
            elif current_transaction and line.strip() and not re.match(r'^\s*(0?[1-9]|1[0-2])/', line):
                # This is a continuation of the previous transaction
                stripped = line.strip()
                
                # Skip certain patterns
                if 'Machine#' in stripped or 'Trace#' in stripped:
                    current_transaction['description'] += ' ' + stripped
                else:
                    # Add to description
                    current_transaction['description'] += ' ' + stripped
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing BECU statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions