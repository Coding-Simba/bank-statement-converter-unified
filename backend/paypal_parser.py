"""Parser for PayPal account statements"""

import re
from datetime import datetime
import subprocess

def parse_date_paypal(date_str):
    """Parse PayPal date format (MM/DD/YY)"""
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling negative values"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check for negative sign
        is_negative = cleaned.startswith('-')
        if is_negative:
            cleaned = cleaned[1:]
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        result = float(cleaned)
        
        # Apply negative sign if needed
        if is_negative:
            result = -result
            
        return result
    except:
        return None

def parse_paypal(pdf_path):
    """Parse PayPal account statements"""
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
            # Look for "ACCOUNT ACTIVITY" header
            if 'ACCOUNT ACTIVITY' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'Total Amount' in line or '*For each transaction' in line:
                in_transaction_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header line
            if 'DATE' in line and 'DESCRIPTION' in line and 'CURRENCY' in line:
                continue
            
            # Look for transaction lines starting with date (MM/DD/YY)
            # PayPal format: Date Description Currency Amount Fees Total
            trans_match = re.match(r'^\s*(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(USD|EUR|GBP)\s+([-]?[\d,]+\.?\d*)\s+([-]?[\d,]+\.?\d*)\s+([-]?[\d,]+\.?\d*)\s*$', line)
            
            if trans_match:
                date_str = trans_match.group(1)
                description = trans_match.group(2).strip()
                currency = trans_match.group(3)
                amount_str = trans_match.group(4)
                fees_str = trans_match.group(5)
                total_str = trans_match.group(6)
                
                # Parse date
                trans_date = parse_date_paypal(date_str)
                
                if trans_date:
                    # Use the total amount (includes fees)
                    total_amount = extract_amount(total_str)
                    
                    if total_amount is not None:
                        transaction = {
                            'date': trans_date,
                            'date_string': date_str,
                            'description': description,
                            'amount': total_amount,
                            'amount_string': total_str,
                            'currency': currency,
                            'fees': extract_amount(fees_str),
                            'gross_amount': extract_amount(amount_str)
                        }
                        
                        transactions.append(transaction)
            
            # Handle wrapped transactions (where total is on next line)
            elif re.match(r'^\s*(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(USD|EUR|GBP)\s+([-]?[\d,]+\.?\d*)\s+([-]?[\d,]+\.?\d*)\s*$', line):
                # This line has date but no total, check next line
                match = re.match(r'^\s*(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(USD|EUR|GBP)\s+([-]?[\d,]+\.?\d*)\s+([-]?[\d,]+\.?\d*)\s*$', line)
                if match and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # Check if next line has the total
                    total_match = re.match(r'^\s*([-]?[\d,]+\.?\d*)\s*$', next_line)
                    if total_match:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        currency = match.group(3)
                        amount_str = match.group(4)
                        fees_str = match.group(5)
                        total_str = total_match.group(1)
                        
                        # Parse date
                        trans_date = parse_date_paypal(date_str)
                        
                        if trans_date:
                            total_amount = extract_amount(total_str)
                            
                            if total_amount is not None:
                                transaction = {
                                    'date': trans_date,
                                    'date_string': date_str,
                                    'description': description,
                                    'amount': total_amount,
                                    'amount_string': total_str,
                                    'currency': currency,
                                    'fees': extract_amount(fees_str),
                                    'gross_amount': extract_amount(amount_str)
                                }
                                
                                transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing PayPal statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions