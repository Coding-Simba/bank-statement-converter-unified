"""Parser for Woodforest National Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_woodforest(date_str):
    """Parse Woodforest date format (MM-DD)"""
    try:
        # Add current year since the statement only shows MM-DD
        current_year = datetime.now().year
        return datetime.strptime(f"{date_str}-{current_year}", "%m-%d-%Y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Handle parentheses for negative amounts
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + re.sub(r'[()]', '', cleaned)
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_woodforest(pdf_path):
    """Parse Woodforest National Bank statements"""
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
        
        # Find transaction section
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Look for "Transactions" header with columns
            if 'Transactions' in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if 'Date' in next_line and 'Credits' in next_line and 'Debits' in next_line:
                    in_transaction_section = True
                    continue
            
            # Also check for "Transactions (continued)"
            if 'Transactions (continued)' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'Total for' in line or 'Account Summary' in line:
                in_transaction_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header lines
            if 'Date' in line and 'Credits' in line and 'Debits' in line:
                continue
            
            # Look for transaction lines
            # Format: MM-DD    Credits    Debits    Balance    Description
            # First try to match date
            date_match = re.match(r'^\s*(\d{2}-\d{2})', line)
            
            if date_match:
                date_str = date_match.group(1)
                
                # Parse by column positions
                # Based on the output, columns appear to be:
                # Date (0-13), Credits (13-36), Debits (36-58), Balance (58-66), Description (66+)
                
                credit_part = line[13:36].strip() if len(line) > 13 else ""
                debit_part = line[36:58].strip() if len(line) > 36 else ""
                balance_part = line[58:66].strip() if len(line) > 58 else ""
                description = line[66:].strip() if len(line) > 66 else ""
                
                # Parse date
                trans_date = parse_date_woodforest(date_str)
                
                if trans_date:
                    # Determine amount based on credit/debit
                    amount = None
                    amount_str = ""
                    
                    # Extract credit amount
                    credit_match = re.search(r'(\d+\.\d{2})', credit_part)
                    # Extract debit amount
                    debit_match = re.search(r'(\d+\.\d{2})', debit_part)
                    
                    if credit_match:
                        # Credit (deposit)
                        amount = extract_amount(credit_match.group(1))
                        amount_str = credit_match.group(1)
                    elif debit_match:
                        # Debit (withdrawal)
                        debit_amount = extract_amount(debit_match.group(1))
                        if debit_amount is not None:
                            amount = -debit_amount
                            amount_str = debit_match.group(1)
                    
                    if amount is not None:
                        transaction = {
                            'date': trans_date,
                            'date_string': date_str,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str
                        }
                        
                        transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Woodforest statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions