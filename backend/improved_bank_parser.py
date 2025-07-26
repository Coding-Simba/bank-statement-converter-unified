"""Improved bank statement parser that correctly handles money in/out columns"""

import re
from datetime import datetime

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    date_formats = [
        '%d %B',  # "1 February" format
        '%d %b',  # "1 Feb" format
        '%m/%d/%Y',
        '%m-%d-%Y', 
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%b %d, %Y',
        '%B %d, %Y',
        '%m/%d/%y',
        '%d-%b-%Y',
        '%d/%m/%y',
        '%m/%d',
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

def parse_bank_statement_with_columns(text):
    """Parse bank statements that have Money out / Money in / Balance columns"""
    transactions = []
    lines = text.split('\n')
    
    # Detect if this is a columnar format by looking for header patterns
    has_money_columns = False
    for i in range(min(50, len(lines) - 1)):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        
        # Check for "Money" on one line and "out" "in" on the next
        if 'money' in line.lower() and ('out' in next_line.lower() or 'in' in next_line.lower()):
            has_money_columns = True
            print(f"[DEBUG] Found money columns header at lines {i}-{i+1}")
            break
        # Also check single line patterns
        if 'money out' in line.lower() or 'money in' in line.lower():
            has_money_columns = True
            print(f"[DEBUG] Found money columns header at line {i}")
            break
    
    if not has_money_columns:
        return transactions
    
    print("[DEBUG] Detected columnar format with Money out/in columns")
    
    # Process transaction lines
    for line in lines:
        if not line.strip():
            continue
            
        # Look for lines with multiple amounts (at least 2)
        amounts = re.findall(r'[\d,]+\.\d{2}', line)
        if len(amounts) < 2:
            continue
            
        # Skip summary/header lines
        if any(skip in line.lower() for skip in ['total', 'balance at', 'summary', 'money out', 'money in']):
            continue
        
        # Try to parse the line structure
        # Pattern 1: With date at beginning
        date_match = re.match(r'^(\d{1,2}\s+\w+|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4})\s+(.+)', line)
        
        if date_match:
            date_str = date_match.group(1)
            rest_of_line = date_match.group(2)
        else:
            # Pattern 2: Continuation line (no date, just description)
            date_str = None
            rest_of_line = line
        
        # Extract description and amounts
        # The last amount is always the balance
        # The second-to-last (or third-to-last if there are 3) is the transaction amount
        
        balance = extract_amount(amounts[-1])
        
        # Find where the amounts start in the line
        first_amount_pos = rest_of_line.find(amounts[0])
        if first_amount_pos > 0:
            description = rest_of_line[:first_amount_pos].strip()
        else:
            # Fallback: use everything before the numbers
            description = re.sub(r'[\d,]+\.\d{2}.*', '', rest_of_line).strip()
        
        # Determine transaction amount and type
        transaction_amount = None
        
        if len(amounts) == 2:
            # Format: transaction amount + balance
            # The first amount is the transaction, second is balance
            transaction_amount = extract_amount(amounts[0])
            
            # Determine if it's a withdrawal based on the position in the line
            # Look for spacing patterns - if there's significant space before the amount,
            # it might be in the "Money In" column
            amount_pos = rest_of_line.find(amounts[0])
            if amount_pos > 60:  # Arbitrary threshold for "Money In" column position
                # This is likely a deposit (Money In column)
                transaction_amount = abs(transaction_amount) if transaction_amount else None
            else:
                # This is likely a withdrawal (Money Out column) or we need to check description
                if any(word in description.lower() for word in ['withdrawal', 'payment', 'debit']):
                    transaction_amount = -abs(transaction_amount) if transaction_amount else None
                elif any(word in description.lower() for word in ['deposit', 'credit', 'salary', 'payment']):
                    transaction_amount = abs(transaction_amount) if transaction_amount else None
                else:
                    # Default to negative for amounts in the first position
                    transaction_amount = -abs(transaction_amount) if transaction_amount else None
        
        if transaction_amount is not None and description:
            transaction = {
                'description': description,
                'amount': transaction_amount,
                'amount_string': str(abs(transaction_amount)),
                'balance': balance
            }
            
            # Add date if available
            if date_str:
                date = parse_date(date_str)
                if date:
                    transaction['date'] = date
                    transaction['date_string'] = date_str
            
            transactions.append(transaction)
            print(f"[DEBUG] Found transaction: {description} | Amount: {transaction_amount} | Balance: {balance}")
    
    return transactions

def parse_improved_bank_pdf(pdf_path):
    """Enhanced parser for bank PDFs with better column detection"""
    import subprocess
    
    transactions = []
    
    try:
        # Get text with layout preserved
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            transactions = parse_bank_statement_with_columns(result.stdout)
            
    except Exception as e:
        print(f"Error in improved parser: {e}")
    
    return transactions