"""PayPal parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class PaypalParser(USBankParser):
    """Parser for PayPal statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "PayPal"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from PayPal statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # PayPal PDFs work better with text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_paypal_text(lines, year))
        
        # If text extraction didn't work well, try tables
        if len(transactions) < 5:
            tables = self.extract_table_data(pdf_path)
            if tables:
                table_trans = self.parse_paypal_tables(tables, year)
                # Add only new transactions
                existing_keys = {(t['date'], t['amount']) for t in transactions}
                for t in table_trans:
                    if (t['date'], t['amount']) not in existing_keys:
                        transactions.append(t)
        
        return transactions
    
    def parse_paypal_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse PayPal-specific table format"""
        transactions = []
        
        for table in tables:
            # Process each row
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                # Skip headers
                row_text = ' '.join(str(cell).lower() for cell in row if cell)
                if any(header in row_text for header in ['date', 'description', 'amount', 'balance']):
                    continue
                
                # Extract transaction data
                date = None
                description = ""
                amount = None
                
                # Look for date in first few columns
                for i, cell in enumerate(row[:3]):
                    cell_str = str(cell).strip()
                    # Try date patterns
                    if self.is_valid_date(cell_str):
                        date = self.parse_date(cell_str, year)
                        if date:
                            break
                    if date:
                        break
                
                if not date:
                    continue
                
                # Extract description (usually middle columns)
                desc_parts = []
                for i, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    # Skip date and amount cells
                    if cell_str and not re.match(r'^[\d,\.\$\-]+$', cell_str) and not re.match(r'^\d{1,2}[/-]\d{1,2}', cell_str):
                        desc_parts.append(cell_str)
                
                description = ' '.join(desc_parts)
                
                # Extract amount (usually last columns)
                for i in range(len(row)-1, -1, -1):
                    amount = self.extract_amount(str(row[i]))
                    if amount is not None:
                        break
                
                if date and amount is not None:
                    description = self.clean_description(description) if description else "PayPal Transaction"
                    
                    # Determine debit/credit
                    if self.is_paypal_debit(description, row_text):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if 'USBankParser' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_paypal_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse PayPal-specific text format"""
        transactions = []
        
        # PayPal specific pattern: DATE DESCRIPTION CURRENCY AMOUNT FEES TOTAL
        # Example: 04/01/22 Deposit in Paypal ID(839439283) USD 432.65 2.65 435.30
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Skip headers and non-transaction lines
            if 'DATE' in line and 'DESCRIPTION' in line:
                i += 1
                continue
            if 'Total Amount' in line:
                i += 1
                continue
            
            # Check if line starts with a date
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2})', line)
            if not date_match:
                i += 1
                continue
            
            date_str = date_match.group(1)
            date = self.parse_date(date_str, year)
            if not date:
                continue
            
            # Remove date from line
            remainder = line[len(date_str):].strip()
            
            # Look for currency indicator to split description and amounts
            currency_match = re.search(r'\s+(USD|EUR|GBP)\s+', remainder)
            if currency_match:
                # Everything before currency is description
                description = remainder[:currency_match.start()].strip()
                
                # Everything after currency contains amounts
                amounts_part = remainder[currency_match.end():].strip()
                
                # Extract the TOTAL amount (last number in the line)
                # Format could be: amount fees total OR just amount
                amount_matches = re.findall(r'[-]?[\d,]+\.?\d*', amounts_part)
                
                if amount_matches:
                    # Check if this transaction continues on the next line
                    # This happens when there are multiple fee entries
                    next_line_amount = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line is just a number (total on next line)
                        if re.match(r'^[-]?[\d,]+\.?\d*$', next_line):
                            next_line_amount = self.extract_amount(next_line)
                    
                    if next_line_amount is not None:
                        # Use the amount from the next line as the total
                        amount = next_line_amount
                        i += 1  # Skip the next line
                    else:
                        # The last amount is usually the total
                        total_str = amount_matches[-1]
                        amount = self.extract_amount(total_str)
                    
                    if amount is not None:
                        # Check if amount should be negative
                        if '-' in amounts_part and amount > 0:
                            # Line contains negative amount but total isn't marked as negative
                            # Check if this is a debit transaction
                            if self.is_paypal_debit(description, line):
                                amount = -abs(amount)
                        elif amount < 0:
                            # Already negative
                            pass
                        
                        transactions.append({
                            'date': date,
                            'date_string': date.strftime('%m/%d/%Y'),
                            'description': self.clean_description(description),
                            'amount': amount,
                            'amount_string': f"{abs(amount):.2f}"
                        })
            else:
                # Try simpler pattern without currency
                # Split by spaces and look for amounts
                parts = remainder.split()
                if len(parts) >= 2:
                    # Find the last numeric value
                    for i in range(len(parts)-1, -1, -1):
                        amount = self.extract_amount(parts[i])
                        if amount is not None:
                            # Description is everything before this amount
                            description = ' '.join(parts[:i])
                            
                            if description:
                                # Determine debit/credit
                                if self.is_paypal_debit(description, line):
                                    amount = -abs(amount)
                                
                                transactions.append({
                                    'date': date,
                                    'date_string': date.strftime('%m/%d/%Y'),
                                    'description': self.clean_description(description),
                                    'amount': amount,
                                    'amount_string': f"{abs(amount):.2f}"
                                })
                                break
            
            i += 1  # Move to next line
        
        return transactions
    
    def is_paypal_debit(self, description: str, full_line: str) -> bool:
        """Determine if PayPal transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # PayPal credit indicators
        credit_keywords = ['deposit', 'payment received', 'refund', 'transfer from']
        
        # PayPal debit indicators
        debit_keywords = ['payment sent', 'purchase', 'withdrawal', 'transfer to', 'fee']
        
        # Check credits first
        for keyword in credit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return False
        
        # Then debits
        for keyword in debit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return True
        
        # Default to debit
        return True
