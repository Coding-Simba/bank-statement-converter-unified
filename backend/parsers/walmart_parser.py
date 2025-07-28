"""Walmart MoneyCard parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class WalmartParser(USBankParser):
    """Parser for Walmart MoneyCard statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Walmart MoneyCard"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Walmart MoneyCard statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_walmart_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_walmart_text(lines, year))
        
        return transactions
    
    def parse_walmart_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Walmart MoneyCard-specific table format"""
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
                    for pattern in ['^\\d{1,2}/\\d{1,2}$']:
                        if re.match(pattern, cell_str):
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
                    description = self.clean_description(description) if description else "Walmart MoneyCard Transaction"
                    
                    # Determine debit/credit
                    if self.is_walmart_debit(description, row_text):
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
    
    def parse_walmart_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Walmart MoneyCard-specific text format"""
        transactions = []
        
        # Walmart MoneyCard patterns
        patterns = [
            # Date Description Type Amount Balance (e.g., "02/01 Nancyhomes32@Gmail.com -$20.00 $1.68 DEBIT ACCOUNT")
            r'^(\d{1,2}/\d{1,2})\s+([^$]+?)\s+([+-]?\$[\d,]+\.?\d*)\s+\$?[\d,]+\.?\d*',
            # Date Amount Balance (e.g., "02/03 -$280.00 $21.68")
            r'^(\d{1,2}/\d{1,2})\s+([+-]?\$[\d,]+\.?\d*)\s+\$?[\d,]+\.?\d*',
            # Date and rest on same line (e.g., "02/11 1009918431 SANTT +$300.00 $301.68")
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([+-]?\$[\d,]+\.?\d*)\s*$'
        ]
        
        # Pattern to find transactions within lines (for multi-transaction lines)
        # Looking for pattern like "02/13 646-755-7665, NY -$140.00"
        multi_trans_pattern = r'(\d{1,2}/\d{1,2})\s+([^$\d]+?)\s+([+-]?\$[\d,]+\.?\d*)'
        
        # Additional processing for multi-line transactions
        skip_next = False
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            if skip_next:
                skip_next = False
                continue
            
            # First check if the line contains multiple transactions
            multi_matches = list(re.finditer(multi_trans_pattern, line))
            if len(multi_matches) > 1:
                # Handle multiple transactions on one line
                for match in multi_matches:
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3)
                    
                    # Parse date
                    date = self.parse_date(date_str, year)
                    if not date:
                        continue
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Clean description
                    description = self.clean_description(description)
                    
                    # Determine debit/credit
                    if self.is_walmart_debit(description, line):
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
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    if pattern_idx == 0:
                        # Date Description Amount Balance
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    elif pattern_idx == 1:
                        # Date Amount Balance - look for description on next line
                        amount_str = match.group(2)
                        description = ""
                        
                        # Look at next line for description
                        if i < len(lines) - 1:
                            next_line = lines[i+1].strip()
                            # If next line is not a date and not a header
                            if not re.match(r'^\d{1,2}/\d{1,2}', next_line) and not any(keyword in next_line for keyword in ['DEBIT ACCOUNT', 'SAVINGS ACCOUNT', 'Beginning Balance', 'Credits', 'Debits', 'Ending Balance']):
                                description = next_line
                                skip_next = True
                        
                        # Also check previous line for context
                        if not description and i > 0:
                            prev_line = lines[i-1].strip()
                            if not re.match(r'^\d{1,2}/\d{1,2}', prev_line) and any(keyword in prev_line for keyword in ['Paid to', 'Money Sent', 'VAULT TO ACCOUNT', 'CARD SERVICES', 'FLUZPAY']):
                                description = prev_line
                        
                        if not description:
                            description = "Walmart MoneyCard Transaction"
                    else:
                        # Date Description Amount
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    
                    # Parse date
                    date = self.parse_date(date_str, year)
                    if not date:
                        continue
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Clean description
                    description = self.clean_description(description)
                    
                    # Determine debit/credit
                    if self.is_walmart_debit(description, line):
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
                    break
        
        return transactions
    
    def is_walmart_debit(self, description: str, full_line: str) -> bool:
        """Determine if Walmart MoneyCard transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # Walmart MoneyCard credit indicators
        credit_keywords = ['deposit', 'load', 'credit', 'refund']
        
        # Walmart MoneyCard debit indicators
        debit_keywords = ['purchase', 'withdrawal', 'payment', 'fee']
        
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
