"""Parser for RBC (Royal Bank of Canada) bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_rbc(date_str, year=None):
    """Parse RBC date format (D Mon or DD Mon)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to date string
        date_with_year = f"{date_str} {year}"
        return datetime.strptime(date_with_year, "%d %b %Y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_rbc(pdf_path):
    """Parse RBC bank statements"""
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
        period_match = re.search(r'From\s+\w+\s+\d+,\s+(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find header line
        header_found = False
        for i, line in enumerate(lines):
            if 'Date' in line and 'Description' in line and 'Withdrawals' in line and 'Deposits' in line:
                header_found = True
                break
        
        if not header_found:
            print("Could not find transaction table header")
            return transactions
        
        # Process transactions
        i = 0
        current_transaction = None
        
        while i < len(lines):
            line = lines[i]
            
            # Look for date at start of line (D Mon or DD Mon format)
            date_match = re.match(r'^(\d{1,2}\s+[A-Z][a-z]{2})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                current_transaction = {
                    'date': parse_date_rbc(date_str, year),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Look for amounts in the line
                # RBC format: description, then optional withdrawal amount, then optional deposit amount, then balance
                # Find all numbers at the end of the line
                numbers = re.findall(r'([\d,]+\.?\d*)', rest_of_line)
                
                if numbers:
                    # The last number is typically the balance
                    # The second-to-last could be the transaction amount
                    if len(numbers) >= 2:
                        # Extract description (everything before the first amount)
                        first_amount_pos = rest_of_line.find(numbers[-2])
                        description = rest_of_line[:first_amount_pos].strip()
                        current_transaction['description'] = description
                        
                        # Check if this is a withdrawal or deposit
                        # Look at the position of the amount in the line
                        amount_str = numbers[-2]
                        amount = extract_amount(amount_str)
                        
                        if amount:
                            # Check if description indicates deposit
                            if re.search(r'Payment|Transfer.*Autodeposit|Misc Payment|Deposit|Credit', description, re.I):
                                current_transaction['amount'] = abs(amount)
                            else:
                                current_transaction['amount'] = -abs(amount)
                            current_transaction['amount_string'] = amount_str
                    else:
                        # Only one number (balance), description is everything before it
                        current_transaction['description'] = rest_of_line.strip()
                else:
                    # No amounts on this line
                    current_transaction['description'] = rest_of_line.strip()
            
            # Handle continuation lines
            elif current_transaction and line.strip() and not re.match(r'^\s*\d{1,2}\s+[A-Z][a-z]{2}', line):
                # This is a continuation of the previous transaction
                stripped = line.strip()
                
                # Skip page headers/footers
                if 'Details of your account activity' in stripped or 'From' in stripped and 'to' in stripped:
                    i += 1
                    continue
                
                # Add to description
                current_transaction['description'] += ' ' + stripped
                
                # Look for amounts if we don't have one yet
                if current_transaction['amount'] is None:
                    # Look for amount pattern
                    amounts = re.findall(r'([\d,]+\.?\d*)', stripped)
                    
                    if amounts:
                        # Take the first significant amount
                        for amt_str in amounts:
                            amount = extract_amount(amt_str)
                            if amount and amount > 0:
                                # Determine if withdrawal or deposit based on description
                                if re.search(r'Payment|Transfer.*Autodeposit|Misc Payment|Deposit|Credit', 
                                           current_transaction['description'], re.I):
                                    current_transaction['amount'] = abs(amount)
                                else:
                                    current_transaction['amount'] = -abs(amount)
                                current_transaction['amount_string'] = amt_str
                                break
            
            i += 1
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing RBC statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions