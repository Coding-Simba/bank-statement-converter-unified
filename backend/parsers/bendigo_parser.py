"""Bendigo Bank PDF parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import PyPDF2
import pdfplumber

def parse(pdf_path: str) -> List[Dict]:
    """Parse Bendigo Bank PDF statement"""
    transactions = []
    
    try:
        # Extract text using PyPDF2
        full_text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        
        # Process the text
        transactions = parse_bendigo_statement(full_text)
        
        # If PyPDF2 didn't work well, try pdfplumber
        if len(transactions) < 3:
            transactions_plumber = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        page_transactions = parse_bendigo_statement(text)
                        transactions_plumber.extend(page_transactions)
            
            if len(transactions_plumber) > len(transactions):
                transactions = transactions_plumber
                
    except Exception as e:
        print(f"Error parsing Bendigo PDF: {e}")
    
    return transactions

def parse_bendigo_statement(text: str) -> List[Dict]:
    """Parse Bendigo Bank statement text"""
    transactions = []
    lines = text.split('\n')
    
    # Date patterns for Bendigo (DD MMM YY format)
    date_pattern = re.compile(r'^(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2})\s+')
    
    # Amount pattern - Bendigo has separate columns for withdrawals and deposits
    withdrawal_pattern = re.compile(r'(\d+\.\d{2})\s+\d+\.\d{2}\s*$')  # withdrawal followed by balance
    deposit_pattern = re.compile(r'(\d+\.\d{2})\s+\d+\.\d{2}\s*$')  # deposit followed by balance
    
    # Track current year from statement period
    current_year = None
    year_match = re.search(r'statement period.*?(\d{4})', text, re.IGNORECASE)
    if year_match:
        current_year = int(year_match.group(1))
    else:
        current_year = datetime.now().year
    
    # Track if we're in transaction section
    in_transaction_section = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            continue
            
        # Detect transaction section start
        if 'Date' in line and 'Transaction' in line and 'Balance' in line:
            in_transaction_section = True
            continue
            
        # Skip non-transaction lines
        if not in_transaction_section:
            continue
            
        # Try to parse transaction
        date_match = date_pattern.match(line_stripped)
        if date_match:
            transaction = parse_bendigo_transaction_line(line_stripped, date_match, current_year)
            if transaction:
                transactions.append(transaction)
    
    return transactions

def parse_bendigo_transaction_line(line: str, date_match, year: int) -> Optional[Dict]:
    """Parse a single Bendigo transaction line"""
    try:
        date_str = date_match.group(1)
        rest_of_line = line[date_match.end():].strip()
        
        # Parse date (DD MMM YY format)
        date_obj = datetime.strptime(date_str, '%d %b %y')
        # Update year if needed
        if date_obj.year < 2000:
            date_obj = date_obj.replace(year=date_obj.year + 2000)
        
        # Split the rest of the line to find amounts
        # Bendigo format: description withdrawal_amount deposit_amount balance
        # Look for numeric patterns at the end
        parts = rest_of_line.split()
        
        # Find amount values from the end
        amount = None
        description = None
        amount_str = None
        
        # Check if last part is balance (always present)
        if parts and re.match(r'\d+\.\d{2}$', parts[-1]):
            balance = parts[-1]
            
            # Check second to last for withdrawal/deposit amount
            if len(parts) > 1 and re.match(r'\d+\.\d{2}$', parts[-2]):
                amount_str = parts[-2]
                amount = float(amount_str)
                
                # Description is everything before the amounts
                description = ' '.join(parts[:-2])
                
                # Determine if it's a withdrawal or deposit based on keywords
                if any(keyword in description.upper() for keyword in ['WITHDRAWAL', 'EFTPOS', 'TRANSFER OUT', 'FEE']):
                    amount = -abs(amount)
                elif any(keyword in description.upper() for keyword in ['DEPOSIT', 'TRANSFER IN', 'INTEREST']):
                    amount = abs(amount)
                else:
                    # Default to withdrawal if unclear
                    amount = -abs(amount)
            else:
                # No amount found, might be opening balance or interest with 0.00
                if 'INTEREST' in rest_of_line.upper() and '0.00' in rest_of_line:
                    amount = 0.00
                    amount_str = '0.00'
                    description = ' '.join(parts[:-1])
                else:
                    return None
        
        if amount is not None and description:
            return {
                'date': date_obj,
                'date_string': date_str,
                'description': description.strip(),
                'amount': amount,
                'amount_string': amount_str
            }
            
    except Exception as e:
        print(f"Error parsing Bendigo line: {line}, error: {e}")
        
    return None