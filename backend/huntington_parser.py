"""Huntington Bank statement parser"""

import re
from datetime import datetime
import pdfplumber

def parse_huntington(pdf_path):
    """Parse Huntington Bank statements"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text from page
                text = page.extract_text()
                if not text:
                    continue
                
                # Split into lines
                lines = text.split('\n')
                
                # Look for transaction patterns
                # Huntington format: MM/DD Description Amount or -Amount
                # Example: 03/15 DEPOSIT 1,200.00
                # Example: 03/16 WALMART SUPERCENTER -45.32
                
                for line in lines:
                    # Skip empty lines and headers
                    if not line.strip():
                        continue
                    
                    # Skip common headers
                    if any(header in line.upper() for header in [
                        'HUNTINGTON', 'STATEMENT', 'ACCOUNT', 'PAGE', 
                        'BALANCE', 'TRANSACTION', 'DATE', 'DESCRIPTION',
                        'DEPOSITS', 'WITHDRAWALS', 'FEES', 'SUMMARY'
                    ]):
                        continue
                    
                    # Try to match transaction pattern
                    # Pattern 1: MM/DD at start of line
                    match = re.match(r'^(\d{1,2}/\d{1,2})\s+(.+?)[\s\-]*([\d,]+\.\d{2})$', line.strip())
                    if match:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = match.group(3).replace(',', '')
                        
                        # Determine if it's a debit (check for minus or certain keywords)
                        is_debit = '-' in line or any(keyword in description.upper() for keyword in [
                            'WITHDRAWAL', 'PURCHASE', 'PAYMENT', 'FEE', 'CHARGE'
                        ])
                        
                        try:
                            # Parse date (add current year)
                            current_year = datetime.now().year
                            date_obj = datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y")
                            
                            # Parse amount
                            amount = float(amount_str)
                            if is_debit and amount > 0:
                                amount = -amount
                            
                            transactions.append({
                                'date': date_obj,
                                'description': description,
                                'amount': amount,
                                'date_string': date_str,
                                'amount_string': amount_str
                            })
                        except ValueError:
                            continue
                    
                    # Pattern 2: Date in MM/DD/YY format
                    match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2})\s+(.+?)[\s\-]*([\d,]+\.\d{2})$', line.strip())
                    if match:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = match.group(3).replace(',', '')
                        
                        # Determine if it's a debit
                        is_debit = '-' in line or any(keyword in description.upper() for keyword in [
                            'WITHDRAWAL', 'PURCHASE', 'PAYMENT', 'FEE', 'CHARGE'
                        ])
                        
                        try:
                            # Parse date
                            date_obj = datetime.strptime(date_str, "%m/%d/%y")
                            
                            # Parse amount
                            amount = float(amount_str)
                            if is_debit and amount > 0:
                                amount = -amount
                            
                            transactions.append({
                                'date': date_obj,
                                'description': description,
                                'amount': amount,
                                'date_string': date_str,
                                'amount_string': amount_str
                            })
                        except ValueError:
                            continue
                    
                    # Pattern 3: Check for multi-line transactions (date on one line, description and amount on next)
                    if re.match(r'^\d{1,2}/\d{1,2}(/\d{2,4})?$', line.strip()):
                        # This line contains only a date, check next line
                        date_str = line.strip()
                        # Store for processing with next line
                        continue
                
    except Exception as e:
        print(f"Error parsing Huntington PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return transactions