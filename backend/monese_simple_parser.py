"""Simple parser for Monese Bank statements"""

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

def parse_monese_simple(pdf_path):
    """Parse Monese Bank statements with simple line-by-line approach"""
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
        
        # Find all lines that contain transaction amounts
        # Pattern: line contains amount (+/-£XXX.XX) and balance (£XXX.XX)
        for i, line in enumerate(lines):
            # Look for lines with amount and balance pattern
            trans_match = re.search(r'([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)\s*$', line)
            
            if trans_match:
                amount_str = trans_match.group(1)
                amount = extract_amount(amount_str)
                
                if amount is not None:
                    # Look for date and description
                    # Date could be on this line or previous lines
                    payment_date = None
                    date_string = None
                    description_parts = []
                    
                    # Check current line for date
                    date_in_line = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                    if date_in_line:
                        date_string = date_in_line.group(1)
                        payment_date = parse_date_monese(date_string)
                        
                        # Extract description from current line
                        desc = line[:line.find(amount_str)].strip()
                        desc = re.sub(r'\d{2}/\d{2}/\d{4}\s*', '', desc, count=1)  # Remove first date
                        if desc:
                            description_parts.append(desc)
                    
                    # If no date found, look in previous lines
                    if not payment_date:
                        for j in range(max(0, i-4), i):
                            prev_line = lines[j]
                            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', prev_line)
                            if date_match:
                                # Found a date, check if it's the payment date (second date on line)
                                all_dates = re.findall(r'(\d{2}/\d{2}/\d{4})', prev_line)
                                if len(all_dates) >= 2:
                                    date_string = all_dates[1]  # Payment date is second
                                else:
                                    date_string = all_dates[0]
                                payment_date = parse_date_monese(date_string)
                                break
                    
                    # Collect description from surrounding lines
                    for j in range(max(0, i-2), min(len(lines), i+2)):
                        desc_line = lines[j].strip()
                        if j == i:
                            # Current line - remove amount and balance
                            desc_line = re.sub(r'([+-]£[\d,]+\.?\d*)\s+(£[\d,]+\.?\d*)\s*$', '', desc_line).strip()
                        
                        # Remove dates and clean up
                        desc_line = re.sub(r'\d{2}/\d{2}/\d{4}\s*', '', desc_line)
                        desc_line = desc_line.strip()
                        
                        if desc_line and desc_line not in ['Transactions', 'Processed date', 'Payment made', 'Description', 'Amount', 'Balance']:
                            if desc_line not in description_parts:
                                description_parts.append(desc_line)
                    
                    # Combine description parts
                    description = ' '.join(description_parts).strip()
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description)  # Multiple spaces to single
                    description = re.sub(r'\|\s*', '| ', description)  # Clean pipe separators
                    
                    if payment_date and description:
                        transaction = {
                            'date': payment_date,
                            'date_string': date_string,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str
                        }
                        transactions.append(transaction)
        
        # Remove duplicates based on date, amount, and description
        seen = set()
        unique_transactions = []
        for trans in transactions:
            key = (trans['date_string'], trans['amount'], trans['description'][:30])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(trans)
        
        # Sort by date
        unique_transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return unique_transactions
        
    except Exception as e:
        print(f"Error parsing Monese statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions