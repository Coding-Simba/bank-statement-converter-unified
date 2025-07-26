"""Improved fixed column parser for complex bank statement layouts"""

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
        
        # Handle commas
        cleaned = cleaned.replace(',', '')
        
        # Convert to float
        return float(cleaned)
        
    except Exception:
        return None

def parse_bank_statement_with_columns(pdf_path):
    """Parse bank statements with Money out/Money in/Balance columns"""
    transactions = []
    
    try:
        # Run pdftotext with layout preservation
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        lines = result.stdout.split('\n')
        
        # Process each line
        for i, line in enumerate(lines):
            # Skip empty lines or short lines
            if not line.strip() or len(line) < 20:
                continue
            
            # Look for lines starting with a date pattern
            # Patterns: "1 February", "16 February", etc.
            date_match = re.match(r'^(\s*)(\d{1,2}\s+\w+)\s+(.+)', line)
            
            if date_match:
                indent = date_match.group(1)
                date_str = date_match.group(2).strip()
                rest_of_line = date_match.group(3)
                
                # Parse the date
                date = parse_date(date_str)
                if not date:
                    continue
                
                # Extract all numeric values from the line
                # Pattern to find amounts: digits with optional commas and decimal point
                amounts = list(re.finditer(r'([\d,]+\.?\d*)', rest_of_line))
                
                if amounts:
                    # Analyze positions of amounts
                    # Typically, amounts appear in these approximate positions:
                    # - Money out: around column 60-70
                    # - Money in: around column 70-80
                    # - Balance: around column 80-90
                    
                    transaction_amount = None
                    is_withdrawal = False
                    
                    # Get description (text before first amount)
                    first_amount_pos = amounts[0].start()
                    description = rest_of_line[:first_amount_pos].strip()
                    
                    # Analyze each amount by its position in the line
                    for amt_match in amounts:
                        amt_str = amt_match.group()
                        amt_pos = amt_match.start() + len(indent) + len(date_str) + 2  # Adjust for date position
                        
                        # Skip if it looks like a time (e.g., "17:30")
                        if ':' in amt_str:
                            continue
                            
                        # Skip if it's just a year or other non-monetary number
                        if len(amt_str) == 4 and amt_str.isdigit():
                            continue
                        
                        amount_val = extract_amount(amt_str)
                        if amount_val is None:
                            continue
                        
                        # Determine if this is the transaction amount or balance
                        # If there are multiple amounts, the first one is usually the transaction
                        # and the last one is the balance
                        if len(amounts) >= 2:
                            if amt_match == amounts[-1]:
                                # This is likely the balance, skip it
                                continue
                            elif amt_match == amounts[0]:
                                # This is likely the transaction amount
                                transaction_amount = amount_val
                                
                                # Determine if it's a withdrawal based on position
                                # Amounts in the "Money out" column (around pos 60-70)
                                if 55 <= amt_pos <= 75:
                                    is_withdrawal = True
                                    transaction_amount = -abs(transaction_amount)
                                # Amounts in the "Money in" column (around pos 70-85)
                                elif 70 <= amt_pos <= 85 and not is_withdrawal:
                                    is_withdrawal = False
                                break
                        else:
                            # Single amount - need to determine by context
                            transaction_amount = amount_val
                            # Check description for withdrawal keywords
                            withdrawal_keywords = ['payment', 'withdrawal', 'debit', 'deli', 'jewelers']
                            if any(keyword in description.lower() for keyword in withdrawal_keywords):
                                is_withdrawal = True
                                transaction_amount = -abs(transaction_amount)
                    
                    # Create transaction if we found a valid amount
                    if transaction_amount is not None:
                        transaction = {
                            'date': date,
                            'date_string': date_str,
                            'description': description,
                            'amount': transaction_amount,
                            'amount_string': f"{abs(transaction_amount):.2f}"
                        }
                        transactions.append(transaction)
            
            # Also check for transactions that continue on next line
            # (description on next line after a date line)
            elif i > 0 and line.strip() and not line[0].isdigit():
                # Check if previous line had a date
                prev_line = lines[i-1] if i > 0 else ""
                if re.match(r'^\s*\d{1,2}\s+\w+', prev_line):
                    # This might be a continuation - check for amounts
                    amounts = list(re.finditer(r'([\d,]+\.?\d*)', line))
                    if amounts:
                        # Extract description and amount
                        description = line[:amounts[0].start()].strip()
                        if description and len(description) > 5:
                            # Add this as a transaction with the previous date
                            # (Would need to track previous date for this)
                            pass
        
        return transactions
        
    except FileNotFoundError:
        print("pdftotext command not found. Please install poppler-utils.")
        return transactions
    except Exception as e:
        print(f"Error parsing bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions