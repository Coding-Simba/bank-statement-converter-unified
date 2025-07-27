"""Parser for SunTrust bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_suntrust(date_str):
    """Parse SunTrust date format (MM/DD/YYYY)"""
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
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
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_suntrust(pdf_path):
    """Parse SunTrust bank statements"""
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
            # Look for "TRANSACTION" header
            if 'TRANSACTION' in line:
                in_transaction_section = True
                continue
            
            # End sections on certain markers
            if 'TOTAL' in line and in_transaction_section:
                # Don't include the TOTAL line
                in_transaction_section = False
                continue
            
            if 'REMINDER' in line:
                in_transaction_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transaction_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip header line
            if 'Date' in line and 'Description' in line and 'Amount' in line:
                continue
            
            # Look for transaction lines with format: MM/DD/YYYY   Description   Amount
            trans_match = re.match(r'^\s*(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s*$', line)
            
            if trans_match:
                date_str = trans_match.group(1)
                description = trans_match.group(2).strip()
                amount_str = trans_match.group(3)
                
                # Parse date
                trans_date = parse_date_suntrust(date_str)
                
                if trans_date:
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # All transactions in this statement appear to be charges (negative)
                        # In a credit card statement, charges reduce available credit
                        amount = -amount
                        
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
        print(f"Error parsing SunTrust statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions