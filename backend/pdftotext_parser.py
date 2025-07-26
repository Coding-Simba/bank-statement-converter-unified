"""Parser that uses pdftotext output to extract transactions"""

import subprocess
import re
from datetime import datetime

def parse_date(date_string):
    """Try multiple date formats to parse dates from statements"""
    # Handle mm/dd/yyyy placeholder
    if date_string == "mm/dd/yyyy":
        return None
        
    date_formats = [
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
            return datetime.strptime(date_string.strip(), fmt)
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
        if ',' in cleaned:
            # Check if comma is decimal separator
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely thousand separator
                cleaned = cleaned.replace(',', '')
        
        # Convert to float
        return float(cleaned)
        
    except Exception:
        return None

def parse_pdftotext_output(pdf_path):
    """Parse PDF using pdftotext command line tool"""
    transactions = []
    
    # print(f"[DEBUG] Starting pdftotext parsing for {pdf_path}")
    
    try:
        # Run pdftotext with layout preservation
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        lines = result.stdout.split('\n')
        
        # print(f"[DEBUG] Found {len(lines)} lines in pdftotext output")
        
        # Parse bank account transactions (page 1 style)
        # Look for lines with date pattern at the beginning
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Look for transaction patterns
            # Pattern 1: Date at beginning (mm/dd/yyyy Fast Payment...)
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{4}|mm/dd/yyyy)\s+(.+)', line)
            if date_match:
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                # Skip header lines
                if 'Date' in line and 'Payment Type' in line:
                    continue
                
                # Skip template date but parse the rest if it looks like a transaction
                if date_str == "mm/dd/yyyy":
                    # Look for real transaction patterns in rest of line
                    # Pattern for bank transactions: "Fast Payment       Amazon                                        132.30     8,181.00"
                    # Pattern for credit card: "Petron - C5 Station                                    223.26"
                    
                    amounts = re.findall(r'[\d,]+\.\d{2}', rest_of_line)
                    if amounts and not any(keyword in rest_of_line for keyword in ['to mm/dd/yyyy', 'Date']):
                        # For bank transactions, extract payment type and description
                        bank_match = re.match(r'^(\w+\s*\w*)\s+(.+?)\s+([\d,]+\.\d{2})(?:\s+([\d,]+\.\d{2}))?', rest_of_line)
                        if bank_match and len(amounts) >= 2:
                            # Bank transaction with payment type
                            payment_type = bank_match.group(1).strip()
                            description = f"{payment_type} {bank_match.group(2).strip()}"
                            amount_str = bank_match.group(3)  # Transaction amount
                            
                            transaction = {
                                'description': description,
                                'amount': extract_amount(amount_str),
                                'amount_string': amount_str
                            }
                            transactions.append(transaction)
                            # print(f"[DEBUG] Found bank transaction: {description} - {amount_str}")
                        elif len(amounts) == 1:
                            # Credit card transaction with single amount
                            desc_match = re.match(r'^(.+?)\s+([\d,]+\.\d{2})\s*$', rest_of_line)
                            if desc_match:
                                description = desc_match.group(1).strip()
                                amount_str = desc_match.group(2)
                                
                                transaction = {
                                    'description': description,
                                    'amount': extract_amount(amount_str),
                                    'amount_string': amount_str
                                }
                                transactions.append(transaction)
                                # print(f"[DEBUG] Found credit card transaction: {description} - {amount_str}")
                else:
                    # Parse real date
                    date = parse_date(date_str)
                    if date:
                        # Extract transaction details
                        # Find amounts in the line
                        amounts = re.findall(r'[\d,]+\.\d{2}', rest_of_line)
                        
                        if amounts:
                            # Extract description (everything before the amounts)
                            desc_end = rest_of_line.find(amounts[0])
                            if desc_end > 0:
                                description = rest_of_line[:desc_end].strip()
                            else:
                                # Try to extract description differently
                                parts = rest_of_line.split()
                                description = ' '.join(parts[:-len(amounts)])
                            
                            # Determine transaction amount
                            # Usually the second-to-last amount is the transaction, last is balance
                            if len(amounts) >= 2:
                                amount = extract_amount(amounts[-2])
                            else:
                                amount = extract_amount(amounts[0])
                            
                            if amount:
                                transaction = {
                                    'date': date,
                                    'date_string': date_str,
                                    'description': description,
                                    'amount': amount,
                                    'amount_string': amounts[-2] if len(amounts) >= 2 else amounts[0]
                                }
                                transactions.append(transaction)
        
        # Second pass: look for simple transaction patterns without dates that we might have missed
        # This is a backup for any missed transactions
        processed_lines = set()
        for i, line in enumerate(lines):
            if not line.strip() or i in processed_lines:
                continue
                
            # Check if this line was already processed as a date line
            if re.match(r'^(\d{1,2}/\d{1,2}/\d{4}|mm/dd/yyyy)\s+', line):
                processed_lines.add(i)
                continue
                
            # Look for lines with amounts at the end that aren't headers
            # Example: "Petron - C5 Station                                       223.26"
            amount_at_end = re.search(r'^(.+?)\s+([\d,]+\.\d{2})\s*$', line)
            if amount_at_end:
                desc = amount_at_end.group(1).strip()
                amt = amount_at_end.group(2)
                
                # Filter out headers and non-transaction lines
                if (desc and 
                    not any(skip in desc.lower() for skip in ['date', 'description', 'amount', 'transaction', 
                                                              'summary', 'reminder', 'balance', 'note:',
                                                              'statement', 'customer', 'branch', 'credit limit',
                                                              'visa gold', 'total amount due', 'payment due']) and
                    len(desc) > 3 and
                    any(c.isalpha() for c in desc) and
                    'mm/dd/yyyy' not in desc):
                    
                    # Check if we already have this transaction
                    already_exists = any(t['description'] == desc and t['amount_string'] == amt for t in transactions)
                    if not already_exists:
                        transaction = {
                            'description': desc,
                            'amount': extract_amount(amt),
                            'amount_string': amt
                        }
                        transactions.append(transaction)
                        # print(f"[DEBUG] Found additional transaction: {desc} - {amt}")
        
        # print(f"[DEBUG] Total transactions found: {len(transactions)}")
        return transactions
        
    except FileNotFoundError:
        print("pdftotext command not found. Please install poppler-utils.")
        return transactions
    except Exception as e:
        print(f"Error parsing with pdftotext: {e}")
        return transactions