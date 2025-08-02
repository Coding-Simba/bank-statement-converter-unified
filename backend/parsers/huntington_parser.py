"""Huntington Bank PDF parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import PyPDF2
import pdfplumber

def parse(pdf_path: str) -> List[Dict]:
    """Parse Huntington Bank PDF statement"""
    transactions = []
    
    try:
        # Extract text using PyPDF2
        full_text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        
        # Process the text
        transactions = parse_huntington_statement(full_text)
        
        # If PyPDF2 didn't work well, try pdfplumber
        if len(transactions) < 5:
            transactions_plumber = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        page_transactions = parse_huntington_statement(text)
                        transactions_plumber.extend(page_transactions)
            
            if len(transactions_plumber) > len(transactions):
                transactions = transactions_plumber
                
    except Exception as e:
        print(f"Error parsing Huntington PDF: {e}")
    
    return transactions

def parse_huntington_statement(text: str) -> List[Dict]:
    """Parse Huntington Bank statement text"""
    transactions = []
    lines = text.split('\n')
    
    # Date patterns for Huntington (MM/DD format)
    date_pattern = re.compile(r'^(\d{2}/\d{2})\s+')
    
    # Amount pattern
    amount_pattern = re.compile(r'([\d,]+\.?\d{0,2})$')
    
    # Track current section and year
    current_section = None
    current_year = None
    
    # Extract year from statement period
    year_match = re.search(r'Period from \d{2}/\d{2}/(\d{2})', text)
    if year_match:
        year_suffix = year_match.group(1)
        current_year = 2000 + int(year_suffix)
    else:
        # Default to current year if not found
        current_year = datetime.now().year
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Detect sections
        if 'Deposit / Credit Activity' in line:
            current_section = 'deposit'
            continue
        elif 'Check Activity' in line:
            current_section = 'check'
            continue
        elif 'Debit Activity' in line or 'Withdrawal Activity' in line:
            current_section = 'debit'
            continue
        elif 'Purchase Activity' in line:
            current_section = 'purchase'
            continue
        elif 'Fee Activity' in line:
            current_section = 'fee'
            continue
            
        # Skip headers and non-transaction lines
        if any(keyword in line for keyword in ['Date', 'Description', 'Amount', 'Check #', 'Beginning Balance', 
                                                'Ending Balance', 'Account:', 'Page', 'Statement']):
            continue
            
        # Try to parse transaction
        date_match = date_pattern.match(line)
        if date_match and current_section:
            transaction = parse_huntington_transaction_line(line, current_section, current_year, date_pattern, amount_pattern)
            if transaction:
                transactions.append(transaction)
        
        # Handle check transactions (different format)
        elif current_section == 'check' and re.match(r'^\d{6}', line):
            # Check format: check_number amount date
            parts = line.split()
            if len(parts) >= 3:
                try:
                    check_num = parts[0]
                    amount_str = parts[1]
                    date_str = parts[2]
                    
                    # Parse amount
                    amount = float(amount_str.replace(',', ''))
                    
                    # Parse date
                    date_parts = date_str.split('/')
                    if len(date_parts) == 2:
                        month = int(date_parts[0])
                        day = int(date_parts[1])
                        date = datetime(current_year, month, day)
                        
                        transactions.append({
                            'date': date,
                            'date_string': date_str,
                            'description': f'Check #{check_num}',
                            'amount': -abs(amount),  # Checks are always negative
                            'amount_string': amount_str
                        })
                except:
                    pass
    
    return transactions

def parse_huntington_transaction_line(line: str, section: str, year: int, date_pattern, amount_pattern) -> Optional[Dict]:
    """Parse a single Huntington transaction line"""
    date_match = date_pattern.match(line)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    rest_of_line = line[date_match.end():].strip()
    
    # Find amount at end of line
    amount_match = amount_pattern.search(rest_of_line)
    if not amount_match:
        return None
    
    amount_str = amount_match.group(1)
    description = rest_of_line[:amount_match.start()].strip()
    
    # Clean up description
    description = ' '.join(description.split())
    
    try:
        # Parse date (MM/DD format)
        date_parts = date_str.split('/')
        month = int(date_parts[0])
        day = int(date_parts[1])
        date = datetime(year, month, day)
        
        # Parse amount
        amount = float(amount_str.replace(',', ''))
        
        # Determine sign based on section
        if section in ['debit', 'check', 'purchase', 'fee']:
            amount = -abs(amount)
        else:  # deposit, credit
            amount = abs(amount)
        
        return {
            'date': date,
            'date_string': date_str,
            'description': description,
            'amount': amount,
            'amount_string': amount_str
        }
    except Exception as e:
        print(f"Error parsing line: {line}, error: {e}")
        return None