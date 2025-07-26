"""Improved parser for Commonwealth Bank of Australia statements"""

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

def parse_commonwealth_bank_v2(pdf_path):
    """Parse Commonwealth Bank of Australia statements - improved version"""
    transactions = []
    
    try:
        # Extract text with layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        text = result.stdout
        
        # Extract year from statement period if available
        year = None
        period_match = re.search(r'Period\s+\d+\s+\w+\s+(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Process each line looking for transactions
        current_transaction = None
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for date at start of line (with possible indentation)
            # Pattern: whitespace, DD Mon, then transaction description
            date_match = re.match(r'^(\s*)(\d{2}\s+[A-Za-z]{3})\s+(.+)', line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction and current_transaction.get('amount') is not None:
                    transactions.append(current_transaction)
                
                # Start new transaction
                indent = date_match.group(1)
                date_str = date_match.group(2).strip()
                rest_of_line = date_match.group(3)
                
                current_transaction = {
                    'date': parse_date_commonwealth(date_str, year),
                    'date_string': date_str,
                    'description': '',
                    'amount': None,
                    'amount_string': ''
                }
                
                # Check if amount is on the same line
                # Look for amount patterns at the end of the line
                # Format: amount spaces CR/DR or just amount
                amount_match = re.search(r'([\d,]+\.?\d*)\s+(?:[\d,]+\.?\d*\s+)?(?:CR|DR)?\s*$', rest_of_line)
                
                if amount_match:
                    # Extract description (everything before the amount)
                    desc_end = amount_match.start()
                    current_transaction['description'] = rest_of_line[:desc_end].strip()
                    
                    # Extract amount
                    amount_str = amount_match.group(1)
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # Check if this is a debit by looking at the position or context
                        # If there's only one amount and no CR indicator, it's likely a debit
                        if ' CR' not in line and not re.search(r'Credit|Direct Credit|Deposit|Refund', rest_of_line, re.I):
                            amount = -abs(amount)
                        
                        current_transaction['amount'] = amount
                        current_transaction['amount_string'] = amount_str
                else:
                    # No amount on this line, just description
                    current_transaction['description'] = rest_of_line.strip()
            
            # Handle continuation lines
            elif current_transaction and line.strip():
                # Check if this line contains additional info for current transaction
                stripped = line.strip()
                
                # Look for card number, value date, or other transaction details
                if 'Card xx' in stripped or 'Value Date:' in stripped or 'Ref ' in stripped:
                    # Add to description
                    current_transaction['description'] += ' ' + stripped
                    
                    # Check if amount is on this line
                    if current_transaction['amount'] is None:
                        amount_match = re.search(r'([\d,]+\.?\d*)\s+(?:[\d,]+\.?\d*\s+)?(?:CR|DR)?\s*$', stripped)
                        if amount_match:
                            amount_str = amount_match.group(1)
                            amount = extract_amount(amount_str)
                            
                            if amount is not None:
                                # Determine if debit or credit
                                if ' CR' not in line and not re.search(r'Credit|Deposit|Refund', current_transaction['description'], re.I):
                                    amount = -abs(amount)
                                
                                current_transaction['amount'] = amount
                                current_transaction['amount_string'] = amount_str
                
                # Check for standalone amount (on a line by itself or with minimal text)
                elif re.match(r'^\s*([\d,]+\.?\d*)\s+(?:[\d,]+\.?\d*\s+)?(?:CR|DR)?\s*$', stripped):
                    if current_transaction['amount'] is None:
                        amount_match = re.match(r'^\s*([\d,]+\.?\d*)', stripped)
                        if amount_match:
                            amount_str = amount_match.group(1)
                            amount = extract_amount(amount_str)
                            
                            if amount is not None:
                                # Determine if debit or credit based on description
                                if not re.search(r'Credit|Deposit|Refund|Transfer from', current_transaction['description'], re.I):
                                    amount = -abs(amount)
                                
                                current_transaction['amount'] = amount
                                current_transaction['amount_string'] = amount_str
        
        # Don't forget the last transaction
        if current_transaction and current_transaction.get('amount') is not None:
            transactions.append(current_transaction)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Commonwealth Bank statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions