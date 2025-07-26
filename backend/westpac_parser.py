"""Parser for Westpac Bank statements with In/Out column format"""

import re
from datetime import datetime
import subprocess

def parse_date_westpac(date_str):
    """Parse Westpac date format (M/D/YYYY)"""
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except:
        try:
            # Try D/M/YYYY format
            return datetime.strptime(date_str.strip(), "%d/%m/%Y")
        except:
            return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        # Remove negative sign temporarily to clean the number
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

def parse_westpac(pdf_path):
    """Parse Westpac Bank statements with In/Out column format"""
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
        
        # Find the header line to understand column positions
        in_col = None
        out_col = None
        header_found = False
        
        for i, line in enumerate(lines):
            # Look for header line with "In" and "Out"
            if 'Date' in line and 'In' in line and 'Out' in line:
                header_found = True
                # Find column positions
                in_col = line.find('In')
                out_col = line.find('Out')
                print(f"Found header at line {i}, In pos: {in_col}, Out pos: {out_col}")
                break
        
        if not header_found:
            print("Could not find transaction table header")
            return transactions
        
        # Process transaction lines
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for date at start of line (M/D/YYYY or D/M/YYYY format)
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{4})\s+', line)
            
            if date_match:
                date_str = date_match.group(1)
                date_obj = parse_date_westpac(date_str)
                
                if date_obj:
                    # Extract amounts from the line
                    # Look for amount patterns after the date
                    # Format: Date Amount Currency In Out Description
                    
                    # Extract the part after date
                    rest_of_line = line[len(date_match.group(0)):]
                    
                    # Look for pattern: amount currency and then look for In/Out values by position
                    amount_match = re.match(r'([\d,]+\.?\d*)\s+(\w+)\s+(.+)', rest_of_line)
                    
                    if amount_match:
                        currency = amount_match.group(2)
                        remaining = amount_match.group(3)
                        
                        # Split remaining text to find In and Out values
                        # Look for numeric patterns (with possible negative sign)
                        values = re.findall(r'(-?[\d,]+\.?\d*)', remaining)
                        
                        # Determine transaction amount
                        amount = None
                        amount_string = ''
                        
                        if values:
                            # First value is typically the In amount (if present)
                            # Second value is typically the Out amount (if present)
                            
                            # Check if first value is negative (it's an Out amount)
                            if values[0].startswith('-'):
                                # This is an Out transaction
                                out_val = extract_amount(values[0])
                                if out_val is not None:
                                    amount = out_val  # Already negative from extract_amount
                                    amount_string = values[0]
                            else:
                                # Check if there's a second value that's negative
                                if len(values) > 1 and values[1].startswith('-'):
                                    # First is In amount, second is Out amount
                                    # Use the Out amount (withdrawal)
                                    out_val = extract_amount(values[1])
                                    if out_val is not None:
                                        amount = out_val  # Already negative
                                        amount_string = values[1]
                                else:
                                    # Only In amount present (deposit)
                                    in_val = extract_amount(values[0])
                                    if in_val is not None:
                                        amount = abs(in_val)  # Ensure positive
                                        amount_string = values[0]
                        
                        if amount is not None:
                            # Extract description from the next line
                            description = ''
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                # Check if next line is not a date or balance line
                                if not re.match(r'^\d{1,2}/\d{1,2}/\d{4}', next_line) and not 'Balance' in next_line:
                                    description = next_line
                                    i += 1  # Skip the description line
                            
                            transaction = {
                                'date': date_obj,
                                'date_string': date_str,
                                'description': description or 'Transaction',
                                'amount': amount,
                                'amount_string': amount_string
                            }
                            
                            transactions.append(transaction)
            
            i += 1
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Westpac statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions