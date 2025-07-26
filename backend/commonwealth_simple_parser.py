"""Simple parser for Commonwealth Bank with direct line parsing"""

import re
from datetime import datetime
import subprocess

def parse_date_commonwealth(date_str, year=None):
    """Parse Commonwealth Bank date format (01 Jul, 15 Aug, etc)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Try with provided year
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

def parse_commonwealth_simple(pdf_path):
    """Parse Commonwealth Bank statements with simple line-by-line approach"""
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
        period_match = re.search(r'Period\s+\d+\s+\w+\s+(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Process transactions
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for date at start of line
            date_match = re.match(r'^\s*(\d{2}\s+[A-Za-z]{3})\s+(.+)', line)
            
            if date_match:
                date_str = date_match.group(1).strip()
                rest_of_line = date_match.group(2)
                
                # Initialize transaction
                transaction = {
                    'date': parse_date_commonwealth(date_str, year),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Check if this line has amounts (look for pattern with balance at end)
                # Pattern: description, then optional amounts, then balance with CR/DR
                balance_pattern = re.search(r'(.*?)\s+(\d[\d,]*\.?\d*)\s+\$?([\d,]+\.?\d*\s+(?:CR|DR))\s*$', rest_of_line)
                
                if balance_pattern:
                    # This line has transaction amount and balance
                    transaction['description'] = balance_pattern.group(1).strip()
                    transaction['amount_string'] = balance_pattern.group(2)
                    amount = extract_amount(balance_pattern.group(2))
                    
                    # Determine if debit or credit
                    # Look for keywords or check if there's another amount before this one
                    full_line_amounts = re.findall(r'(\d[\d,]*\.?\d*)', rest_of_line)
                    
                    if len(full_line_amounts) >= 3:
                        # Three amounts: likely debit, credit, balance
                        # The transaction amount is in position based on whether it's debit or credit
                        debit_amount = extract_amount(full_line_amounts[0])
                        credit_amount = extract_amount(full_line_amounts[1]) if len(full_line_amounts) > 1 else None
                        
                        # If first amount matches our extracted amount, it's a debit
                        if debit_amount and abs(debit_amount - amount) < 0.01:
                            transaction['amount'] = -abs(amount)
                        else:
                            transaction['amount'] = abs(amount)
                    else:
                        # Check description for credit indicators
                        if re.search(r'CASH DEPOSIT|Transfer from|Credit|Direct Credit|Deposit|Refund', transaction['description'], re.I):
                            transaction['amount'] = abs(amount)
                        else:
                            transaction['amount'] = -abs(amount)
                else:
                    # No amounts on this line, just description
                    transaction['description'] = rest_of_line.strip()
                    
                    # Look for amount in next lines
                    j = i + 1
                    while j < len(lines) and j < i + 4:
                        next_line = lines[j]
                        
                        # Stop if we hit another date
                        if re.match(r'^\s*\d{2}\s+[A-Za-z]{3}\s+', next_line):
                            break
                        
                        # Add to description if it's additional info
                        if next_line.strip() and not re.search(r'\s+\d[\d,]*\.?\d*\s+\$?[\d,]+\.?\d*\s+(?:CR|DR)\s*$', next_line):
                            transaction['description'] += ' ' + next_line.strip()
                        
                        # Look for amount line (has balance at end)
                        amount_match = re.search(r'(\d[\d,]*\.?\d*)\s+\$?([\d,]+\.?\d*\s+(?:CR|DR))\s*$', next_line)
                        if amount_match:
                            # Found amount line
                            # Check if there are multiple amounts (debit and credit columns)
                            all_amounts = re.findall(r'(\d[\d,]*\.?\d*)', next_line)
                            
                            if len(all_amounts) >= 2:
                                # At least transaction amount and balance
                                transaction['amount_string'] = all_amounts[-2]  # Second to last is transaction
                                amount = extract_amount(all_amounts[-2])
                                
                                if amount:
                                    # Check position or keywords to determine debit/credit
                                    if re.search(r'CASH DEPOSIT|Transfer from|Credit|Direct Credit|Deposit|Refund', transaction['description'], re.I):
                                        transaction['amount'] = abs(amount)
                                    else:
                                        transaction['amount'] = -abs(amount)
                                    break
                        
                        j += 1
                    
                    i = j - 1
                
                # Add transaction if valid
                if transaction['amount'] is not None:
                    transactions.append(transaction)
            
            i += 1
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Commonwealth Bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions