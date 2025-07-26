"""Final parser for Commonwealth Bank of Australia statements with correct debit/credit detection"""

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

def parse_commonwealth_final(pdf_path):
    """Parse Commonwealth Bank statements with proper debit/credit identification"""
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
        
        # Find the header line to understand column positions
        debit_col = None
        credit_col = None
        balance_col = None
        
        for i, line in enumerate(lines):
            if 'Date' in line and 'Transaction' in line and 'Debit' in line and 'Credit' in line:
                # This is the header line
                debit_col = line.find('Debit')
                credit_col = line.find('Credit')
                balance_col = line.find('Balance')
                print(f"Found columns - Debit: {debit_col}, Credit: {credit_col}, Balance: {balance_col}")
                break
        
        # Process transactions
        current_transaction = None
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Look for date at start of line
            date_match = re.match(r'^(\s*)(\d{2}\s+[A-Za-z]{3})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(2).strip()
                description = date_match.group(3).strip()
                
                current_transaction = {
                    'date': parse_date_commonwealth(date_str, year),
                    'date_string': date_str,
                    'description': description,
                    'amount': None,
                    'amount_string': ''
                }
                
                # Look for amounts in the next few lines (Commonwealth often splits transactions)
                j = i + 1
                while j < len(lines) and j < i + 5:  # Check next 5 lines max
                    next_line = lines[j]
                    
                    # Stop if we hit another date
                    if re.match(r'^\s*\d{2}\s+[A-Za-z]{3}\s+', next_line):
                        break
                    
                    # Add card info or other details to description
                    if 'Card xx' in next_line or 'Ref ' in next_line:
                        current_transaction['description'] += ' ' + next_line.strip()
                    
                    # Look for amount line (contains Value Date and amounts)
                    if 'Value Date:' in next_line or re.search(r'\s+[\d,]+\.?\d*\s+(?:[\d,]+\.?\d*\s+)?(?:CR|DR)?\s*$', next_line):
                        # This line likely contains the amount
                        # Try to extract amounts based on column positions
                        
                        if debit_col and credit_col and balance_col:
                            # For Commonwealth Bank, amounts can appear anywhere between description and balance
                            # Look for all amounts in the line, excluding the balance at the end
                            
                            # Find all numeric values in the line
                            all_amounts = re.findall(r'([\d,]+\.?\d+)', next_line)
                            
                            if all_amounts:
                                # The last amount is typically the balance (has CR/DR suffix)
                                # The second-to-last is typically the transaction amount
                                if len(all_amounts) >= 2:
                                    # Check if this line has a balance indicator (CR/DR at end)
                                    has_balance = re.search(r'[\d,]+\.?\d+\s+(?:CR|DR)\s*$', next_line)
                                    
                                    if has_balance:
                                        # Second-to-last amount is the transaction
                                        transaction_amount_str = all_amounts[-2]
                                        amount = extract_amount(transaction_amount_str)
                                        
                                        if amount:
                                            # Determine if it's debit or credit by position
                                            amount_pos = next_line.rfind(transaction_amount_str)
                                            
                                            # If amount appears closer to credit column position, it's a credit
                                            # Otherwise it's a debit
                                            if amount_pos > debit_col + 20:  # Likely in credit area
                                                current_transaction['amount'] = abs(amount)  # Credits are positive
                                            else:
                                                current_transaction['amount'] = -abs(amount)  # Debits are negative
                                            
                                            current_transaction['amount_string'] = transaction_amount_str
                                            break
                                elif len(all_amounts) == 1:
                                    # Only one amount, likely a transaction amount
                                    amount = extract_amount(all_amounts[0])
                                    if amount:
                                        # Check position to determine debit/credit
                                        amount_pos = next_line.find(all_amounts[0])
                                        if amount_pos > debit_col + 20:
                                            current_transaction['amount'] = abs(amount)
                                        else:
                                            current_transaction['amount'] = -abs(amount)
                                        current_transaction['amount_string'] = all_amounts[0]
                                        break
                        else:
                            # Fallback: look for pattern with two amounts (transaction amount and balance)
                            # Pattern: some text, amount1, amount2 CR/DR
                            amounts_match = re.search(r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*\s+(?:CR|DR))', next_line)
                            if amounts_match:
                                # First amount is the transaction amount
                                amount = extract_amount(amounts_match.group(1))
                                if amount:
                                    # Check if it's a credit transaction
                                    if re.search(r'Credit|Deposit|Transfer from|Refund|Cash Dep', current_transaction['description'], re.I):
                                        current_transaction['amount'] = abs(amount)
                                    else:
                                        current_transaction['amount'] = -abs(amount)
                                    current_transaction['amount_string'] = amounts_match.group(1)
                                    break
                    
                    j += 1
                
                # Skip the lines we just processed
                i = j - 1
            
            i += 1
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        # Some transactions might not have been captured, try a simpler approach for those
        if len(transactions) < 50 and 'OPENING BALANCE' in text:  # Likely missing transactions
            print(f"Only found {len(transactions)} transactions, trying alternative parsing...")
            
            # Simple pattern matching for common transaction formats
            simple_pattern = re.compile(r'(\d{2}\s+[A-Za-z]{3})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*\s+CR)')
            
            for match in simple_pattern.finditer(text):
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                
                # Skip if we already have this transaction
                exists = any(t['date_string'] == date_str and amount_str in t.get('amount_string', '') for t in transactions)
                if exists:
                    continue
                
                transaction = {
                    'date': parse_date_commonwealth(date_str, year),
                    'date_string': date_str,
                    'description': description,
                    'amount': -extract_amount(amount_str),  # These are typically debits
                    'amount_string': amount_str
                }
                
                if transaction['amount'] is not None:
                    transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Commonwealth Bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions