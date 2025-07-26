"""Improved parser for RBC (Royal Bank of Canada) bank statements"""

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

def parse_rbc_v2(pdf_path):
    """Parse RBC bank statements with improved multi-line transaction handling"""
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
        
        # Find the transaction section
        in_transaction_section = False
        current_date = None
        current_date_str = None
        
        for i, line in enumerate(lines):
            # Look for transaction header
            if 'Date' in line and 'Description' in line and 'Withdrawals' in line and 'Deposits' in line:
                in_transaction_section = True
                continue
            
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip headers and footers
            if any(x in line for x in ['Details of your account activity', 'From', 'Please retain', 'TM Trademarks']):
                continue
            
            # Check for date at start of line (with large indentation)
            date_match = re.match(r'^[^\d]*(\d{1,2})\s+([A-Z][a-z]{2})\s+(.+)', line)
            
            if date_match and int(date_match.group(1)) <= 31:  # Valid day
                # New date found
                current_date_str = f"{date_match.group(1)} {date_match.group(2)}"
                current_date = parse_date_rbc(current_date_str, year)
                rest_of_line = date_match.group(3).strip()
                
                # Process the transaction on this line
                if rest_of_line:
                    # Look for amounts
                    # Pattern: description followed by amounts
                    # Find all numeric values
                    amounts = re.findall(r'([\d,]+\.?\d*)', rest_of_line)
                    
                    if amounts:
                        # Last amount is balance, second-to-last is transaction amount
                        if len(amounts) >= 2:
                            trans_amount = extract_amount(amounts[-2])
                            if trans_amount:
                                # Find description (everything before the amounts)
                                desc_end = rest_of_line.find(amounts[-2])
                                description = rest_of_line[:desc_end].strip()
                                
                                # Determine if withdrawal or deposit
                                # Check column position or keywords
                                if re.search(r'Transfer.*Autodeposit|Payment.*Lyft|Payment.*Uber|Deposit|Credit', rest_of_line, re.I):
                                    amount = abs(trans_amount)
                                else:
                                    amount = -abs(trans_amount)
                                
                                transaction = {
                                    'date': current_date,
                                    'date_string': current_date_str,
                                    'description': description,
                                    'amount': amount,
                                    'amount_string': amounts[-2]
                                }
                                transactions.append(transaction)
            else:
                # This might be a transaction under the current date
                if current_date and line.strip():
                    # Remove large indentation
                    stripped = line.strip()
                    
                    # Skip if it's just a page number or header
                    if re.match(r'^\d+$', stripped) or len(stripped) < 5:
                        continue
                    
                    # Look for transaction pattern
                    # Could be just description, or description with amounts
                    amounts = re.findall(r'([\d,]+\.?\d*)', stripped)
                    
                    if amounts and len(amounts) >= 1:
                        # This line has amounts
                        # Check if it's a complete transaction line
                        description = stripped
                        trans_amount = None
                        amount_str = ''
                        
                        # If there are multiple amounts, last is balance, previous is transaction
                        if len(amounts) >= 2:
                            trans_amount = extract_amount(amounts[-2])
                            amount_str = amounts[-2]
                            # Extract description
                            desc_end = stripped.find(amounts[-2])
                            if desc_end > 0:
                                description = stripped[:desc_end].strip()
                        elif len(amounts) == 1:
                            # Single amount might be transaction amount
                            # Check if next line has more amounts (continuation)
                            if i + 1 < len(lines) and lines[i + 1].strip():
                                next_amounts = re.findall(r'([\d,]+\.?\d*)', lines[i + 1])
                                if not next_amounts:
                                    # No amounts on next line, this is the transaction amount
                                    trans_amount = extract_amount(amounts[0])
                                    amount_str = amounts[0]
                                    desc_end = stripped.find(amounts[0])
                                    if desc_end > 0:
                                        description = stripped[:desc_end].strip()
                        
                        if trans_amount:
                            # Determine if withdrawal or deposit
                            if re.search(r'Transfer.*Autodeposit|Payment.*Lyft|Payment.*Uber|Deposit|Credit|Misc Payment', description, re.I):
                                amount = abs(trans_amount)
                            else:
                                amount = -abs(trans_amount)
                            
                            transaction = {
                                'date': current_date,
                                'date_string': current_date_str,
                                'description': description,
                                'amount': amount,
                                'amount_string': amount_str
                            }
                            transactions.append(transaction)
                    else:
                        # No amounts, might be a description line
                        # Check if next line has the amount
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            next_amounts = re.findall(r'([\d,]+\.?\d*)', next_line)
                            
                            if next_amounts and not re.match(r'^\d{1,2}\s+[A-Z][a-z]{2}', next_line):
                                # Next line has amounts for this description
                                trans_amount = None
                                amount_str = ''
                                
                                if len(next_amounts) >= 2:
                                    trans_amount = extract_amount(next_amounts[0])
                                    amount_str = next_amounts[0]
                                elif len(next_amounts) == 1:
                                    trans_amount = extract_amount(next_amounts[0])
                                    amount_str = next_amounts[0]
                                
                                if trans_amount:
                                    # Combine description from both lines
                                    full_description = stripped
                                    if not re.match(r'^\d', next_line):
                                        desc_part = next_line[:next_line.find(amount_str)].strip()
                                        if desc_part:
                                            full_description += ' ' + desc_part
                                    
                                    # Determine if withdrawal or deposit
                                    if re.search(r'Transfer.*Autodeposit|Payment.*Lyft|Payment.*Uber|Deposit|Credit|Misc Payment', full_description, re.I):
                                        amount = abs(trans_amount)
                                    else:
                                        amount = -abs(trans_amount)
                                    
                                    transaction = {
                                        'date': current_date,
                                        'date_string': current_date_str,
                                        'description': full_description,
                                        'amount': amount,
                                        'amount_string': amount_str
                                    }
                                    transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing RBC statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions