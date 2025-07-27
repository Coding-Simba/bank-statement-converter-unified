"""Parser for Discover credit card statements"""

import re
from datetime import datetime
import subprocess

def parse_date_discover(date_str, year=None):
    """Parse Discover date format (Mon D or Mon DD)"""
    if not year:
        year = datetime.now().year
    
    try:
        # Add year to the date
        date_with_year = f"{date_str.strip()} {year}"
        return datetime.strptime(date_with_year, "%b %d %Y")
    except:
        try:
            # Try with single digit day
            return datetime.strptime(date_with_year, "%b %d %Y")
        except:
            return None

def extract_amount(amount_str):
    """Extract numeric amount from string, handling negative values"""
    if not amount_str or not amount_str.strip():
        return None
    
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Check for negative sign (credits/payments)
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

def parse_discover(pdf_path):
    """Parse Discover credit card statements"""
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
        # Look for "Open Date: Sep 15, 2022 - Close Date: Oct 26, 2022"
        period_match = re.search(r'(?:Open|Close)\s+Date:.*?(\d{4})', text)
        if period_match:
            year = int(period_match.group(1))
        else:
            year = datetime.now().year
        
        lines = text.split('\n')
        
        # Find transactions section
        in_transactions_section = False
        current_category = None
        
        for i, line in enumerate(lines):
            # Look for "Transactions" header
            if 'Transactions' in line and not 'section' in line:
                in_transactions_section = True
                continue
            
            # End sections on certain markers
            if 'Interest Charge Calculation' in line or 'NOTICE:' in line:
                in_transactions_section = False
                continue
            
            # Skip if not in transaction section
            if not in_transactions_section:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for category with first transaction on same line
            # e.g., "Payments and Credits      Oct 2          Oct 2       INTERNET PAYMENT - THANK YOU                                  $            -180.00"
            category_trans_match = re.match(r'^([A-Za-z\s&]+?)\s+([A-Z][a-z]{2}\s+\d{1,2})\s+([A-Z][a-z]{2}\s+\d{1,2})\s+(.+?)\s+([-]?\$?\s*[\d,]+\.?\d*)\s*$', line)
            if category_trans_match:
                current_category = category_trans_match.group(1).strip()
                trans_date_str = category_trans_match.group(2)
                post_date_str = category_trans_match.group(3)
                description = category_trans_match.group(4).strip()
                amount_str = category_trans_match.group(5)
                
                # Process this transaction
                trans_date = parse_date_discover(trans_date_str, year)
                
                if trans_date:
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # Payments and Credits should be positive
                        if 'payments' in current_category.lower() and 'credits' in current_category.lower():
                            if amount < 0:
                                amount = -amount  # Make positive
                        else:
                            # Purchases are negative (debits)
                            if amount > 0:
                                amount = -amount
                        
                        transaction = {
                            'date': trans_date,
                            'date_string': trans_date_str,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str,
                            'category': current_category
                        }
                        
                        transactions.append(transaction)
                continue
            
            # Check for standalone category headers
            if re.match(r'^[A-Za-z\s&]+$', line) and not re.match(r'^\s*$', line):
                potential_category = line.strip()
                # Only update category if it looks like a valid category name
                if len(potential_category) > 3 and len(potential_category) < 30:
                    current_category = potential_category
            
            # Look for regular transaction lines with format: Mon D   Mon D   Description   $amount
            # Pattern to match lines with two dates followed by description and amount
            # Allow for variable spacing at the beginning
            trans_match = re.match(r'^\s*([A-Z][a-z]{2}\s+\d{1,2})\s+([A-Z][a-z]{2}\s+\d{1,2})\s+(.+?)\s+([-]?\$?\s*[\d,]+\.?\d*)\s*$', line)
            if not trans_match:
                # Try without requiring both dates (some lines might be formatted differently)
                trans_match = re.match(r'^\s+([A-Z][a-z]{2}\s+\d{1,2})\s+([A-Z][a-z]{2}\s+\d{1,2})\s+(.+?)\s+([-]?[\d,]+\.?\d*)\s*$', line)
            
            if trans_match:
                trans_date_str = trans_match.group(1)
                post_date_str = trans_match.group(2)
                description = trans_match.group(3).strip()
                amount_str = trans_match.group(4)
                
                # Parse transaction date
                trans_date = parse_date_discover(trans_date_str, year)
                
                if trans_date:
                    amount = extract_amount(amount_str)
                    
                    if amount is not None:
                        # Determine if it's a credit or debit based on category and sign
                        if current_category and 'payments' in current_category.lower() and 'credits' in current_category.lower():
                            # Payments and Credits should be positive
                            if amount < 0:
                                amount = -amount  # Make positive
                        else:
                            # Purchases are negative (debits)
                            if amount > 0:
                                amount = -amount  # Make purchases negative as they reduce balance
                        
                        transaction = {
                            'date': trans_date,
                            'date_string': trans_date_str,
                            'description': description,
                            'amount': amount,
                            'amount_string': amount_str,
                            'category': current_category
                        }
                        
                        transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x.get('date') or datetime.min)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing Discover statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions