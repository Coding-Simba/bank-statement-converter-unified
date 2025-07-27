"""Parser for Walmart Money Card bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_walmart(date_str):
    """Parse Walmart date format (MM/DD)"""
    try:
        # Add current year since the statement only shows MM/DD
        current_year = datetime.now().year
        return datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
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
        
        # Check if negative
        is_negative = cleaned.startswith('-') or cleaned.startswith('+')
        if is_negative:
            sign = cleaned[0]
            cleaned = cleaned[1:]
        else:
            sign = ''
        
        # Convert to float
        result = float(cleaned)
        
        # Apply sign
        if sign == '-':
            result = -result
            
        return result
    except:
        return None

def parse_walmart(pdf_path):
    """Parse Walmart Money Card bank statements"""
    transactions = []
    
    try:
        # Extract text with layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        text = result.stdout
        lines = text.split('\n')
        
        # State tracking
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Look for "DEBIT ACCOUNT TRANSACTIONS" header
            if 'DEBIT ACCOUNT TRANSACTIONS' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'SAVINGS ACCOUNT' in line and 'Beginning Balance:' in line:
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
            
            # Look for lines with amounts (main transaction indicator)
            # Format can be: -$20.00 or +$300.00 or just amounts in specific column positions
            amount_match = re.search(r'([+-]?\$?[\d,]+\.\d{2})\s+([+-]?\$?[\d,]+\.\d{2})', line)
            
            if amount_match:
                # Found a line with amounts - first is transaction amount, second is balance
                amount_str = amount_match.group(1)
                
                # Look for date at start of line or previous lines
                date_str = None
                description = ""
                
                # Check if date is on this line
                date_match = re.match(r'^(\d{2}/\d{2})', line)
                if date_match:
                    date_str = date_match.group(1)
                    # Extract description between date and amount
                    date_end = len(date_match.group(0))
                    amount_pos = line.find(amount_match.group(0))
                    if amount_pos > date_end:
                        desc_part = line[date_end:amount_pos].strip()
                        if desc_part:
                            description = desc_part
                
                # Look for description and date in previous lines
                j = i - 1
                while j >= 0 and j > i - 5:  # Look up to 4 lines back
                    prev_line = lines[j].strip()
                    
                    # Check for date
                    if not date_str:
                        prev_date_match = re.match(r'^(\d{2}/\d{2})', prev_line)
                        if prev_date_match:
                            date_str = prev_date_match.group(1)
                            # Get rest of line as potential description
                            rest = prev_line[len(prev_date_match.group(0)):].strip()
                            if rest and not re.search(r'[+-]?\$?[\d,]+\.\d{2}', rest):
                                description = rest + " " + description
                            break
                    
                    # Check for description lines
                    if prev_line and not re.match(r'^\d{2}/\d{2}', prev_line) and \
                       not re.search(r'[+-]?\$?[\d,]+\.\d{2}', prev_line) and \
                       'Date' not in prev_line and 'DEBIT ACCOUNT' not in prev_line:
                        # This is likely a description line
                        description = prev_line + " " + description
                    
                    j -= 1
                
                # Clean up description
                description = description.strip()
                
                if date_str:
                    trans_date = parse_date_walmart(date_str)
                    
                    if trans_date:
                        amount = extract_amount(amount_str)
                        
                        if amount is not None:
                            transaction = {
                                'date': trans_date,
                                'date_string': date_str,
                                'description': description or "Transaction",
                                'amount': amount,
                                'amount_string': amount_str
                            }
                            
                            transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Walmart Money Card statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions