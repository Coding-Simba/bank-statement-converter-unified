"""SunTrust parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class SuntrustParser(USBankParser):
    """Parser for SunTrust statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "SunTrust"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from SunTrust statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_suntrust_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_suntrust_text(lines, year))
        
        return transactions
    
    def parse_suntrust_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse SunTrust-specific table format"""
        transactions = []
        
        for table in tables:
            # Process each row
            for row in table:
                if not row:
                    continue
                
                # Skip headers
                row_text = ' '.join(str(cell).lower() if cell else '' for cell in row)
                if any(header in row_text for header in ['date', 'description', 'amount', 'balance', 'previous', 'card type']):
                    continue
                
                # Check if the transaction is in a single cell (common for SunTrust)
                if len(row) == 1 or (len(row) > 1 and all(cell is None for cell in row[1:])):
                    # Transaction in single cell
                    cell_text = str(row[0]).strip()
                    # Pattern: MM/DD/YYYY Description Amount
                    match = re.match(r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([\d,]+\.?\d*)$', cell_text)
                    if match:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        
                        date = self.parse_date(date_str, year)
                        amount = self.extract_amount(amount_str)
                        
                        if date and amount is not None:
                            transactions.append({
                                'date': date,
                                'date_string': date.strftime('%m/%d/%Y'),
                                'description': self.clean_description(description),
                                'amount': amount,  # All SunTrust transactions appear to be debits in this format
                                'amount_string': f"{abs(amount):.2f}"
                            })
                    continue
                
                # Standard multi-column format
                date = None
                description = ""
                amount = None
                
                # Look for date in first few columns
                for i, cell in enumerate(row[:3]):
                    if cell is None:
                        continue
                    cell_str = str(cell).strip()
                    if self.is_valid_date(cell_str):
                        date = self.parse_date(cell_str, year)
                        if date:
                            break
                
                if not date:
                    continue
                
                # Extract description and amount
                desc_parts = []
                for i, cell in enumerate(row):
                    if cell is None:
                        continue
                    cell_str = str(cell).strip()
                    
                    # Try to extract amount
                    if not amount:
                        test_amount = self.extract_amount(cell_str)
                        if test_amount is not None:
                            amount = test_amount
                            continue
                    
                    # Otherwise it's part of description
                    if cell_str and not re.match(r'^\d{1,2}[/-]\d{1,2}', cell_str):
                        desc_parts.append(cell_str)
                
                description = ' '.join(desc_parts)
                
                if date and amount is not None:
                    description = self.clean_description(description) if description else "SunTrust Transaction"
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,  # SunTrust statements show all amounts as positive debits
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_suntrust_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse SunTrust-specific text format"""
        transactions = []
        
        # SunTrust patterns
        patterns = [
            # Date Description Amount
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s*$',
            # Date Amount Description
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(.+?)$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    if pattern_idx == 0:
                        # Date Description Amount
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    else:
                        # Date Amount Description
                        amount_str = match.group(2)
                        description = match.group(3).strip()
                    
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
                    if self.is_suntrust_debit(description, line):
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
    
    def is_suntrust_debit(self, description: str, full_line: str) -> bool:
        """Determine if SunTrust transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # SunTrust credit indicators
        credit_keywords = ['deposit', 'credit', 'transfer credit']
        
        # SunTrust debit indicators
        debit_keywords = ['debit', 'purchase', 'payment', 'withdrawal']
        
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
