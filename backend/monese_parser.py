"""Parser for Monese Bank statements"""

import re
from datetime import datetime
import subprocess

def parse_date_monese(date_str):
    """Parse Monese date format (DD/MM/YYYY)"""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y")
    except:
        return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling + and - prefixes"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check for + or - prefix
        is_negative = cleaned.startswith('-')
        is_positive = cleaned.startswith('+')
        
        if is_negative or is_positive:
            cleaned = cleaned[1:]
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[€$£¥₹,]', '', cleaned)
        cleaned = cleaned.replace(' ', '')
        
        # Convert to float
        result = float(cleaned)
        
        # Apply sign
        if is_negative:
            result = -result
            
        return result
    except:
        return None

def parse_monese(pdf_path):
    """Parse Monese Bank statements with multi-line format"""
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
        
        # Find the Transactions section
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Look for "Transactions" header
            if line.strip() == 'Transactions':
                in_transaction_section = True
                continue
            
            if not in_transaction_section:
                continue
            
            # Skip headers
            if 'Processed date' in line or 'Payment made' in line:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for transaction lines - they start with a date
            # Pattern: DD/MM/YYYY at the beginning of the line (with possible leading spaces)
            date_match = re.match(r'^\s*(\d{2}/\d{2}/\d{4})\s+', line)
            
            if date_match:
                processed_date = date_match.group(1)
                rest_of_line = line[len(date_match.group(0)):]
                
                # Look for payment date and other info
                # Pattern: DD/MM/YYYY Description +/-Amount Balance
                payment_match = re.match(r'(\d{2}/\d{2}/\d{4})\s+(.+?)([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)\s*$', rest_of_line)
                
                if payment_match:
                    # Complete transaction on one line
                    payment_date = payment_match.group(1)
                    description = payment_match.group(2).strip()
                    amount_str = payment_match.group(3)
                    
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        transaction = {
                            'date': parse_date_monese(payment_date),
                            'date_string': payment_date,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str
                        }
                        transactions.append(transaction)
                else:
                    # Transaction might be split across lines
                    # Check if next lines have the rest of the info
                    combined_lines = [rest_of_line]
                    j = i + 1
                    
                    # Collect next few lines that might be part of this transaction
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        
                        # Stop if we hit another date or empty line
                        if not next_line or re.match(r'^\d{2}/\d{2}/\d{4}', next_line):
                            break
                        
                        combined_lines.append(next_line)
                        j += 1
                    
                    # Try to extract transaction from combined lines
                    combined_text = ' '.join(combined_lines)
                    
                    # Look for pattern: payment_date description amount balance
                    full_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)', combined_text)
                    
                    if full_match:
                        payment_date = full_match.group(1)
                        description = full_match.group(2).strip()
                        amount_str = full_match.group(3)
                        
                        amount = extract_amount(amount_str)
                        
                        if amount is not None:
                            transaction = {
                                'date': parse_date_monese(payment_date),
                                'date_string': payment_date,
                                'description': description,
                                'amount': amount,
                                'amount_string': amount_str
                            }
                            transactions.append(transaction)
            
            # Also handle lines that don't start with processed date but have payment date
            # These are continuation lines from multi-line transactions
            elif line.strip() and not re.match(r'^\s*\d{2}/\d{2}/\d{4}', line):
                # Check if this line contains amount and balance (might be continuation)
                amount_match = re.search(r'([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)\s*$', line)
                if amount_match and i > 0:
                    # Look back to find the payment date
                    for k in range(max(0, i-3), i):
                        if re.search(r'\d{2}/\d{2}/\d{4}', lines[k]):
                            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', lines[k])
                            if date_match:
                                payment_date = date_match.group(1)
                                
                                # Extract description from current and previous lines
                                description_lines = []
                                for m in range(k, i+1):
                                    desc_line = lines[m].strip()
                                    # Remove date and amount parts
                                    desc_line = re.sub(r'^\s*\d{2}/\d{2}/\d{4}\s*', '', desc_line)
                                    desc_line = re.sub(r'([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)\s*$', '', desc_line)
                                    if desc_line:
                                        description_lines.append(desc_line)
                                
                                description = ' '.join(description_lines).strip()
                                amount_str = amount_match.group(1)
                                amount = extract_amount(amount_str)
                                
                                if amount is not None and description:
                                    transaction = {
                                        'date': parse_date_monese(payment_date),
                                        'date_string': payment_date,
                                        'description': description,
                                        'amount': amount,
                                        'amount_string': amount_str
                                    }
                                    transactions.append(transaction)
                                break
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Monese statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions