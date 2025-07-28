"""US Bank parser base class for MM/DD date formats"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from base_parser import BaseBankParser

logger = logging.getLogger(__name__)

class USBankParser(BaseBankParser):
    """Base parser for US banks with MM/DD date formats"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "US Bank"
        
        # Common US date formats
        self.supported_date_formats = [
            '%m/%d/%Y',      # 01/15/2023
            '%m/%d/%y',      # 01/15/23
            '%m-%d-%Y',      # 01-15-2023
            '%m-%d-%y',      # 01-15-23
            '%m/%d',         # 01/15 (no year)
            '%m-%d',         # 01-15 (no year)
            '%b %d, %Y',     # Jan 15, 2023
            '%B %d, %Y',     # January 15, 2023
            '%b %d %Y',      # Jan 15 2023
            '%B %d %Y',      # January 15 2023
            '%b %d',         # Jan 15 (no year)
            '%b %-d',        # Jan 5 (single digit day, no year)
            '%b-%d',         # Jan-15 (Scotiabank format)
            '%b-%-d',        # Jan-5 (single digit day)
        ]
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from US bank statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_from_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_from_text(lines, year))
        
        return transactions
    
    def parse_from_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse transactions from table data"""
        transactions = []
        
        for table in tables:
            # Find header row
            header_idx = self.find_header_row(table)
            if header_idx is None:
                continue
                
            headers = [str(h).lower() for h in table[header_idx]]
            
            # Find column indices
            date_col = self.find_column(headers, ['date', 'trans date', 'transaction date', 'posted'])
            desc_col = self.find_column(headers, ['description', 'transaction', 'details', 'merchant'])
            amount_col = self.find_column(headers, ['amount', 'total'])
            debit_col = self.find_column(headers, ['debit', 'withdrawal', 'charges'])
            credit_col = self.find_column(headers, ['credit', 'deposit', 'payments'])
            
            # Process data rows
            for row_idx in range(header_idx + 1, len(table)):
                row = table[row_idx]
                
                # Extract date
                date = None
                if date_col is not None and date_col < len(row):
                    date_str = str(row[date_col]).strip()
                    if self.is_valid_date(date_str):
                        date = self.parse_date(date_str, year)
                
                if not date:
                    continue
                
                # Extract description
                description = ""
                if desc_col is not None and desc_col < len(row):
                    description = self.clean_description(str(row[desc_col]))
                
                # Extract amount
                amount = None
                
                # Try single amount column first
                if amount_col is not None and amount_col < len(row):
                    amount = self.extract_amount(str(row[amount_col]))
                
                # Try separate debit/credit columns
                if amount is None:
                    if debit_col is not None and debit_col < len(row):
                        debit_amt = self.extract_amount(str(row[debit_col]))
                        if debit_amt:
                            amount = -abs(debit_amt)
                    
                    if credit_col is not None and credit_col < len(row):
                        credit_amt = self.extract_amount(str(row[credit_col]))
                        if credit_amt:
                            amount = abs(credit_amt)
                
                if amount is not None and description:
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_from_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse transactions from text lines"""
        transactions = []
        
        # Common patterns for US bank transactions
        patterns = [
            # Date at start: MM/DD Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Date at start: MM-DD Description Amount
            r'^(\d{1,2}-\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Full date: MM/DD/YYYY Description Amount
            r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # With transaction type: MM/DD TYPE Description Amount
            r'^(\d{1,2}/\d{1,2})\s+\w+\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
                
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
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
                    
                    # Determine if debit/credit based on context
                    if self.is_debit_transaction(description, line):
                        amount = -abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': self.clean_description(description),
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def find_header_row(self, table: List[List[str]]) -> Optional[int]:
        """Find the header row in a table"""
        for i, row in enumerate(table):
            if not row:
                continue
                
            row_text = ' '.join(str(cell).lower() for cell in row if cell)
            
            # Check for common header keywords
            if any(keyword in row_text for keyword in ['date', 'description', 'amount', 'debit', 'credit']):
                return i
                
        return None
    
    def find_column(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by keywords"""
        for keyword in keywords:
            for i, header in enumerate(headers):
                if keyword in header:
                    return i
        return None
    
    def is_debit_transaction(self, description: str, full_line: str) -> bool:
        """Determine if transaction is a debit based on description"""
        debit_keywords = [
            'withdrawal', 'purchase', 'payment', 'fee', 'charge',
            'debit', 'pos', 'atm', 'check', 'ach debit', 'bill pay',
            'transfer out', 'wire out'
        ]
        
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        for keyword in debit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return True
                
        return False