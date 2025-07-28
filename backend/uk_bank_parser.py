"""UK Bank parser base class for DD/MM date formats"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from base_parser import BaseBankParser

logger = logging.getLogger(__name__)

class UKBankParser(BaseBankParser):
    """Base parser for UK banks with DD/MM date formats"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "UK Bank"
        
        # Common UK date formats
        self.supported_date_formats = [
            '%d/%m/%Y',      # 15/01/2023
            '%d/%m/%y',      # 15/01/23
            '%d-%m-%Y',      # 15-01-2023
            '%d-%m-%y',      # 15-01-23
            '%d.%m.%Y',      # 15.01.2023 (Metro format)
            '%d.%m.%y',      # 15.01.23
            '%d/%m',         # 15/01 (no year)
            '%d-%m',         # 15-01 (no year)
            '%d %b %Y',      # 15 Jan 2023
            '%d %B %Y',      # 15 January 2023
            '%d %b %y',      # 15 Jan 23
            '%d %B %y',      # 15 January 23
            '%d %b',         # 15 Jan (no year)
            '%d %B',         # 15 January (no year)
            '%d-%b-%y',      # 15-Jan-23 (Lloyds format)
            '%-d-%b-%y'      # 1-Jan-23 (no leading zero)
        ]
        
        # UK-specific currency
        self.currency_symbols = ['£', 'GBP', '€', 'EUR'] + self.currency_symbols
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from UK bank statement"""
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
            
            # Find column indices (UK-specific headers)
            date_col = self.find_column(headers, ['date', 'trans date', 'transaction date', 'value date'])
            desc_col = self.find_column(headers, ['description', 'transaction', 'details', 'narrative', 'reference'])
            amount_col = self.find_column(headers, ['amount', 'value'])
            debit_col = self.find_column(headers, ['debit', 'money out', 'payments out', 'debits'])
            credit_col = self.find_column(headers, ['credit', 'money in', 'payments in', 'credits'])
            balance_col = self.find_column(headers, ['balance', 'running balance'])
            
            # Process data rows
            for row_idx in range(header_idx + 1, len(table)):
                row = table[row_idx]
                
                # Extract date
                date = None
                if date_col is not None and date_col < len(row):
                    date_str = str(row[date_col]).strip()
                    if self.is_valid_date(date_str):
                        date = self.parse_uk_date(date_str, year)
                
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
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_from_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse transactions from text lines"""
        transactions = []
        
        # Common patterns for UK bank transactions
        patterns = [
            # Date at start: DD/MM Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+£?([\d,]+\.?\d*)\s*$',
            # Date at start: DD-MM Description Amount
            r'^(\d{1,2}-\d{1,2})\s+(.+?)\s+£?([\d,]+\.?\d*)\s*$',
            # Full date: DD/MM/YYYY Description Amount
            r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+£?([\d,]+\.?\d*)\s*$',
            # Date with month name: DD MMM Description Amount
            r'^(\d{1,2}\s+\w{3})\s+(.+?)\s+£?([\d,]+\.?\d*)\s*$',
            # With reference: DD/MM REF Description Amount
            r'^(\d{1,2}/\d{1,2})\s+\S+\s+(.+?)\s+£?([\d,]+\.?\d*)\s*$'
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
                    date = self.parse_uk_date(date_str, year)
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
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': self.clean_description(description),
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def parse_uk_date(self, date_str: str, year: Optional[int] = None) -> Optional[datetime]:
        """Parse UK-specific date formats"""
        if not date_str:
            return None
            
        # Handle special UK formats
        date_str = date_str.strip()
        
        # Convert UK month abbreviations if needed
        uk_months = {
            'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
            'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug',
            'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dec': 'Dec'
        }
        
        for abbr, proper in uk_months.items():
            if abbr in date_str.lower():
                date_str = date_str.lower().replace(abbr, proper)
                break
        
        # Try parsing with base method
        return self.parse_date(date_str, year)
    
    def find_header_row(self, table: List[List[str]]) -> Optional[int]:
        """Find the header row in a table"""
        for i, row in enumerate(table):
            if not row:
                continue
                
            row_text = ' '.join(str(cell).lower() for cell in row if cell)
            
            # Check for UK-specific header keywords
            uk_keywords = ['date', 'description', 'narrative', 'money in', 'money out', 
                          'debit', 'credit', 'balance', 'reference']
            
            if any(keyword in row_text for keyword in uk_keywords):
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
            'card payment', 'direct debit', 'standing order', 'withdrawal',
            'purchase', 'payment', 'fee', 'charge', 'dd', 'so', 'atm',
            'faster payment', 'bacs', 'chaps', 'transfer out'
        ]
        
        credit_keywords = [
            'deposit', 'credit', 'salary', 'wages', 'transfer in',
            'refund', 'interest', 'dividend'
        ]
        
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # Check for credit indicators first
        for keyword in credit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return False
        
        # Then check for debit indicators
        for keyword in debit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return True
                
        return False