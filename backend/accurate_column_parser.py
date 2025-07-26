"""Accurate fixed column parser based on exact column positions"""

import re
from datetime import datetime
import subprocess

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    date_formats = [
        '%d %B',      # '1 February'
        '%d %b',      # '1 Feb' 
        '%B %d',      # 'February 1'
        '%b %d',      # 'Feb 1'
        '%m/%d/%Y',
        '%m-%d-%Y', 
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%b %d, %Y',
        '%B %d, %Y',
        '%m/%d/%y',
        '%d-%b-%Y',
        '%m/%d'       # '10/03' for dummy statements
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_string.strip(), fmt)
            # If year is missing, use current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    try:
        if not amount_str:
            return None
            
        # Clean the string
        cleaned = amount_str.strip()
        
        # Remove currency symbols
        cleaned = re.sub(r'[€$£¥₹]', '', cleaned)
        
        # Remove spaces
        cleaned = cleaned.replace(' ', '')
        
        # Handle parentheses for negative amounts
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + re.sub(r'[()]', '', cleaned)
        
        # Handle commas
        cleaned = cleaned.replace(',', '')
        
        # Convert to float
        return float(cleaned)
        
    except Exception:
        return None

def parse_accurate_columns(pdf_path):
    """Parse bank statements using accurate column position detection"""
    transactions = []
    
    try:
        # Run pdftotext with layout preservation
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        lines = result.stdout.split('\n')
        
        # First, try to detect column headers to determine format
        paid_in_pos = None
        paid_out_pos = None
        money_in_pos = None 
        money_out_pos = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'paid in' in line_lower and 'paid out' in line_lower:
                # This is a "Paid In/Paid Out" format
                paid_in_match = re.search(r'paid\s+in', line_lower)
                paid_out_match = re.search(r'paid\s+out', line_lower)
                if paid_in_match:
                    paid_in_pos = paid_in_match.start()
                if paid_out_match:
                    paid_out_pos = paid_out_match.start()
                print(f"Found Paid In/Out format - Paid In: {paid_in_pos}, Paid Out: {paid_out_pos}")
                break
            elif 'money' in line_lower and ('in' in line_lower or 'out' in line_lower):
                # This is a "Money in/Money out" format
                if i+1 < len(lines):
                    next_line = lines[i+1]
                    if 'out' in next_line.lower():
                        money_out_pos = next_line.lower().find('out')
                    if 'in' in next_line.lower():
                        money_in_pos = next_line.lower().find('in')
                print(f"Found Money In/Out format - Money out: {money_out_pos}, Money in: {money_in_pos}")
                break
        
        # Set appropriate ranges based on detected format
        if paid_in_pos is not None and paid_out_pos is not None:
            # Paid In/Out format
            money_in_range = (paid_in_pos - 5, paid_in_pos + 10)
            money_out_range = (paid_out_pos - 5, paid_out_pos + 10)
            balance_range = (paid_out_pos + 15, paid_out_pos + 30)
        else:
            # Default Money in/out format positions
            money_out_range = (58, 68)
            money_in_range = (70, 80)
            balance_range = (82, 95)
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for lines starting with dates or date placeholders
            # Pattern 1: "1 February" style
            date_match = re.match(r'^(\s*)(\d{1,2}\s+\w+)\s+(.+)', line)
            # Pattern 2: "10/03" style (for dummy statements)
            if not date_match:
                date_match = re.match(r'^(\s*)(\d{1,2}/\d{1,2})\s+(.+)', line)
            # Pattern 3: "mm/dd/yyyy" placeholder style
            if not date_match:
                date_match = re.match(r'^(\s*)(mm/dd/yyyy)\s+(.+)', line)
            
            if date_match:
                indent = date_match.group(1)
                date_str = date_match.group(2).strip()
                rest_of_line = line[len(indent) + len(date_str):]
                
                # Parse the date
                date = parse_date(date_str)
                # For placeholder dates, use None but continue processing
                if not date and date_str != "mm/dd/yyyy":
                    continue
                
                # Find all amounts in the line
                amounts = list(re.finditer(r'([\d,]+\.?\d*)', rest_of_line))
                
                transaction_amount = None
                description = None
                
                for amt_match in amounts:
                    amt_str = amt_match.group()
                    # Calculate absolute position in the original line
                    amt_pos = len(indent) + len(date_str) + amt_match.start()
                    
                    # Skip non-monetary values (times, years, etc.)
                    if ':' in amt_str or (len(amt_str) == 4 and amt_str.isdigit()):
                        continue
                    
                    # Skip reference numbers (long digit strings)
                    if len(amt_str) > 10 and '.' not in amt_str:
                        continue
                    
                    amount_val = extract_amount(amt_str)
                    if amount_val is None or amount_val == 0:
                        continue
                    
                    # Determine which column this amount is in
                    if money_out_range[0] <= amt_pos <= money_out_range[1]:
                        # This is a withdrawal (money out)
                        transaction_amount = -abs(amount_val)
                        # Description is everything before this amount
                        desc_end = amt_match.start()
                        description = rest_of_line[:desc_end].strip()
                        break
                    elif money_in_range[0] <= amt_pos <= money_in_range[1]:
                        # This is a deposit (money in)
                        transaction_amount = abs(amount_val)
                        # Description is everything before this amount
                        desc_end = amt_match.start()
                        description = rest_of_line[:desc_end].strip()
                        break
                    elif balance_range[0] <= amt_pos <= balance_range[1]:
                        # This is the balance - skip it
                        continue
                
                # Create transaction if we found a valid amount
                if transaction_amount is not None and description:
                    transaction = {
                        'date': date,
                        'date_string': date_str,
                        'description': description.strip(),
                        'amount': transaction_amount,
                        'amount_string': f"{abs(transaction_amount):.2f}"
                    }
                    transactions.append(transaction)
            
            # Handle continuation lines (like "Direct Deposit" without date)
            elif i > 0 and line.strip() and not re.match(r'^\s*\d', line):
                # Check for amounts in continuation lines
                amounts = list(re.finditer(r'([\d,]+\.?\d*)', line))
                
                for amt_match in amounts:
                    amt_str = amt_match.group()
                    amt_pos = amt_match.start()
                    
                    # Skip non-monetary values
                    if ':' in amt_str or (len(amt_str) == 4 and amt_str.isdigit()):
                        continue
                    
                    amount_val = extract_amount(amt_str)
                    if amount_val and amount_val > 0:
                        # Check position for both deposits and withdrawals
                        transaction_amount = None
                        description = None
                        
                        if money_out_range[0] <= amt_pos <= money_out_range[1]:
                            # This is a withdrawal continuation
                            transaction_amount = -abs(amount_val)
                            description = line[:amt_match.start()].strip()
                        elif money_in_range[0] <= amt_pos <= money_in_range[1]:
                            # This is a deposit continuation
                            transaction_amount = abs(amount_val)
                            description = line[:amt_match.start()].strip()
                        
                        if transaction_amount and description and len(description) > 3:
                            # Use previous transaction's date if available
                            if transactions:
                                # Find the most recent date from a proper date line
                                prev_date = None
                                prev_date_string = None
                                for j in range(len(transactions)-1, -1, -1):
                                    if transactions[j].get('date'):
                                        prev_date = transactions[j]['date']
                                        prev_date_string = transactions[j]['date_string']
                                        break
                                
                                if prev_date:
                                    transaction = {
                                        'date': prev_date,
                                        'date_string': prev_date_string,
                                        'description': description,
                                        'amount': transaction_amount,
                                        'amount_string': f"{abs(transaction_amount):.2f}"
                                    }
                                    transactions.append(transaction)
        
        return transactions
        
    except FileNotFoundError:
        print("pdftotext command not found. Please install poppler-utils.")
        return transactions
    except Exception as e:
        print(f"Error parsing with accurate column parser: {e}")
        import traceback
        traceback.print_exc()
        return transactions