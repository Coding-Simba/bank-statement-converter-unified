"""Parser for Bank of America bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_boa(date_str):
    """Parse Bank of America date format (MM/DD/YY)"""
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling negative values"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check for negative sign
        is_negative = cleaned.startswith('-')
        if is_negative:
            cleaned = cleaned[1:]
        
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

def parse_boa(pdf_path):
    """Parse Bank of America bank statements"""
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
        
        # Find transaction sections
        in_deposits_section = False
        in_withdrawals_section = False
        current_transaction = None
        
        for i, line in enumerate(lines):
            # Look for section headers
            if 'Deposits and other credits' in line and 'Date' in lines[i+1] if i+1 < len(lines) else False:
                in_deposits_section = True
                in_withdrawals_section = False
                continue
            
            if 'Withdrawals and other debits' in line and 'Date' in lines[i+1] if i+1 < len(lines) else False:
                in_deposits_section = False
                in_withdrawals_section = True
                continue
            
            if 'Total deposits' in line or 'Total withdrawals' in line:
                # Save last transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                    current_transaction = None
                in_deposits_section = False
                in_withdrawals_section = False
                continue
            
            # Skip if not in a transaction section
            if not in_deposits_section and not in_withdrawals_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for transaction lines starting with date
            date_match = re.match(r'^(\d{2}/\d{2}/\d{2})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                current_transaction = {
                    'date': parse_date_boa(date_str),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Check if amount is on this line
                # Amount is typically at the end, right-aligned
                amount_match = re.search(r'([-]?[\d,]+\.?\d*)\s*$', rest_of_line)
                
                if amount_match:
                    # Extract description (everything before the amount)
                    amount_pos = rest_of_line.rfind(amount_match.group(1))
                    description = rest_of_line[:amount_pos].strip()
                    
                    amount_str = amount_match.group(1)
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # Apply sign based on section
                        if in_deposits_section:
                            amount = abs(amount)  # Deposits are positive
                        elif in_withdrawals_section:
                            amount = -abs(amount)  # Withdrawals are negative
                        
                        current_transaction['amount'] = amount
                        current_transaction['amount_string'] = amount_str
                        current_transaction['description'] = description
                else:
                    # No amount on this line, just description
                    current_transaction['description'] = rest_of_line.strip()
            
            # Handle continuation lines
            elif current_transaction and line.strip() and not re.match(r'^\d{2}/\d{2}/\d{2}', line):
                # This is a continuation of the previous transaction
                stripped = line.strip()
                
                # Add to description
                current_transaction['description'] += ' ' + stripped
                
                # Check if this line has the amount
                if current_transaction['amount'] is None:
                    amount_match = re.search(r'([-]?[\d,]+\.?\d*)\s*$', stripped)
                    
                    if amount_match:
                        # Extract the amount
                        amount_str = amount_match.group(1)
                        amount = extract_amount(amount_str)
                        
                        if amount is not None:
                            # Apply sign based on section
                            if in_deposits_section:
                                amount = abs(amount)
                            elif in_withdrawals_section:
                                amount = -abs(amount)
                            
                            current_transaction['amount'] = amount
                            current_transaction['amount_string'] = amount_str
                            
                            # Remove amount from description
                            desc_without_amount = stripped[:stripped.rfind(amount_str)].strip()
                            if desc_without_amount:
                                # Replace the last addition with the cleaned version
                                current_transaction['description'] = current_transaction['description'].rsplit(' ' + stripped, 1)[0]
                                if desc_without_amount:
                                    current_transaction['description'] += ' ' + desc_without_amount
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Bank of America statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions