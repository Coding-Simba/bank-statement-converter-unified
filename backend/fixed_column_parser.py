"""Fixed column position parser for bank statements with clear columnar layouts"""

import re
from datetime import datetime
import subprocess

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    date_formats = [
        '%d %B',  # '1 February'
        '%d %b',  # '1 Feb' 
        '%B %d',  # 'February 1'
        '%b %d',  # 'Feb 1'
        '%m/%d/%Y',
        '%m-%d-%Y', 
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%b %d, %Y',
        '%B %d, %Y',
        '%m/%d/%y',
        '%d-%b-%Y'
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

def parse_fixed_column_layout(pdf_path):
    """Parse PDFs with fixed column positions for Money out/Money in/Balance"""
    transactions = []
    
    try:
        # Run pdftotext with layout preservation
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        lines = result.stdout.split('\n')
        
        # Detect column positions by finding header line
        money_out_pos = None
        money_in_pos = None
        balance_pos = None
        
        for i, line in enumerate(lines):
            # Look for column headers - handle multi-line headers
            if 'money' in line.lower():
                # This might be a header line, check next line too
                next_line = lines[i+1] if i+1 < len(lines) else ""
                combined = line + " " + next_line
                
                # Find column positions
                money_out_match = re.search(r'money\s*out', combined, re.IGNORECASE)
                money_in_match = re.search(r'money\s*in', combined, re.IGNORECASE)
                balance_match = re.search(r'balance', combined, re.IGNORECASE)
                
                if money_out_match or money_in_match:
                    # Try to find positions in the original lines
                    if 'out' in next_line.lower():
                        money_out_pos = next_line.lower().find('out')
                    if 'in' in next_line.lower():
                        money_in_pos = next_line.lower().find('in')
                    if 'balance' in line.lower():
                        balance_pos = line.lower().find('balance')
                    elif 'balance' in next_line.lower():
                        balance_pos = next_line.lower().find('balance')
                        
                    print(f"Column positions - Money out: {money_out_pos}, Money in: {money_in_pos}, Balance: {balance_pos}")
                    break
        
        # If we didn't find explicit column headers, try to detect from patterns
        if money_out_pos is None:
            # Analyze a few transaction lines to find common positions
            amount_positions = []
            for line in lines:
                # Look for lines with dates and multiple amounts
                if re.match(r'^\d{1,2}\s+\w+', line):
                    amounts = list(re.finditer(r'[\d,]+\.\d{2}', line))
                    if len(amounts) >= 2:
                        for amt in amounts:
                            amount_positions.append(amt.start())
            
            if amount_positions:
                # Cluster positions to find columns
                amount_positions.sort()
                # Typically: money out ~62, money in ~75, balance ~86-87
                if len(amount_positions) >= 3:
                    money_out_pos = 62
                    money_in_pos = 75
                    balance_pos = 86
        
        # Parse transactions
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Look for transaction lines starting with dates
            date_match = re.match(r'^(\d{1,2}\s+\w+)', line)
            if date_match:
                date_str = date_match.group(1)
                date = parse_date(date_str)
                
                if date:
                    # Extract description (after date, before amounts)
                    # Find first amount position
                    first_amount = re.search(r'[\d,]+\.\d{2}', line)
                    if first_amount:
                        desc_end = first_amount.start()
                        description = line[len(date_str):desc_end].strip()
                    else:
                        # No amount on this line, description is rest of line
                        description = line[len(date_str):].strip()
                    
                    # Extract amounts based on column positions
                    transaction_amount = None
                    is_withdrawal = False
                    
                    # Find all amounts in the line
                    amounts = list(re.finditer(r'[\d,]+\.\d{2}', line))
                    
                    for amt_match in amounts:
                        amt_pos = amt_match.start()
                        amt_str = amt_match.group()
                        
                        # Determine which column this amount belongs to
                        if money_out_pos and abs(amt_pos - money_out_pos) < 10:
                            # This is a withdrawal (money out)
                            transaction_amount = extract_amount(amt_str)
                            if transaction_amount:
                                transaction_amount = -abs(transaction_amount)
                                is_withdrawal = True
                                break
                        elif money_in_pos and abs(amt_pos - money_in_pos) < 10:
                            # This is a deposit (money in)
                            transaction_amount = extract_amount(amt_str)
                            break
                        elif balance_pos and abs(amt_pos - balance_pos) < 15:
                            # This is the balance, skip it
                            continue
                        elif len(amounts) == 2 and amt_match == amounts[0]:
                            # If only 2 amounts and this is the first, it's likely the transaction
                            transaction_amount = extract_amount(amt_str)
                            # Check if it should be negative based on description
                            if any(word in description.lower() for word in ['withdrawal', 'payment', 'debit']):
                                transaction_amount = -abs(transaction_amount)
                                is_withdrawal = True
                    
                    # Create transaction if we found an amount
                    if transaction_amount is not None:
                        transaction = {
                            'date': date,
                            'date_string': date_str,
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
        print(f"Error parsing with fixed column layout: {e}")
        import traceback
        traceback.print_exc()
        return transactions