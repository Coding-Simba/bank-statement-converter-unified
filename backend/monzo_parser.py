"""Parser for Monzo Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_monzo(date_str):
    """Parse Monzo date format (DD/MM/YYYY)"""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y")
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

def parse_monzo(pdf_path):
    """Parse Monzo Bank statements"""
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
        
        # Find the transaction table header
        header_found = False
        for i, line in enumerate(lines):
            if 'Date' in line and 'Description' in line and 'Amount' in line and 'Balance' in line:
                header_found = True
                break
        
        if not header_found:
            print("Could not find transaction table header")
            return transactions
        
        # Process transaction lines
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for transaction pattern: DD/MM/YYYY at start
            date_match = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+)', line)
            
            if date_match:
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                # Parse the rest of the line
                # Pattern: Description (can have spaces) Amount Balance
                # Amount can be negative with - prefix
                
                # Find amounts at the end (look for patterns like -15.00 or 40.00)
                amount_pattern = re.findall(r'(-?\d+\.?\d*)', rest_of_line)
                
                if amount_pattern and len(amount_pattern) >= 2:
                    # Last is balance, second-to-last is transaction amount
                    trans_amount_str = amount_pattern[-2]
                    trans_amount = extract_amount(trans_amount_str)
                    
                    if trans_amount is not None:
                        # Extract description (everything before the amounts)
                        # Find where the transaction amount appears
                        amount_pos = rest_of_line.rfind(trans_amount_str)
                        description = rest_of_line[:amount_pos].strip()
                        
                        # If description ends with currency symbol, remove it
                        description = re.sub(r'\s*\(GBP\)\s*$', '', description)
                        
                        transaction = {
                            'date': parse_date_monzo(date_str),
                            'date_string': date_str,
                            'description': description,
                            'amount': trans_amount,
                            'amount_string': trans_amount_str
                        }
                        
                        transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Monzo statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions