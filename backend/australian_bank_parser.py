"""Australian Bank parser base class for D/MM/YYYY date formats"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from base_parser import BaseBankParser

logger = logging.getLogger(__name__)

class AustralianBankParser(BaseBankParser):
    """Base parser for Australian banks with D/MM/YYYY date formats"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Australian Bank"
        
        # Common Australian date formats
        self.supported_date_formats = [
            '%d/%m/%Y',      # 5/01/2023 or 15/01/2023
            '%d/%m/%y',      # 5/01/23 or 15/01/23
            '%-d/%m/%Y',     # 5/01/2023 (no leading zero)
            '%-d/%m/%y',     # 5/01/23 (no leading zero)
            '%d-%m-%Y',      # 5-01-2023
            '%d-%m-%y',      # 5-01-23
            '%-d-%m-%Y',     # 5-01-2023 (no leading zero)
            '%-d-%m-%y',     # 5-01-23 (no leading zero)
            '%d %b %Y',      # 5 Jan 2023
            '%d %B %Y',      # 5 January 2023
            '%-d %b %Y',     # 5 Jan 2023 (no leading zero)
            '%-d %B %Y',     # 5 January 2023 (no leading zero)
            '%d %b',         # 5 Jan (no year)
            '%-d %b',        # 5 Jan (no year, no leading zero)
            '%d/%m',         # 5/01 (no year)
            '%-d/%m'         # 5/01 (no year, no leading zero)
        ]
        
        # Australian currency
        self.currency_symbols = ['$', 'AUD', 'AU$'] + self.currency_symbols
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Australian bank statement"""
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
            
            # Find column indices (Australian-specific headers)
            date_col = self.find_column(headers, ['date', 'trans date', 'transaction date', 'value date', 'posted date'])
            desc_col = self.find_column(headers, ['description', 'transaction', 'details', 'narrative', 'particulars'])
            amount_col = self.find_column(headers, ['amount', 'value', 'transaction amount'])
            debit_col = self.find_column(headers, ['debit', 'withdrawal', 'money out', 'dr'])
            credit_col = self.find_column(headers, ['credit', 'deposit', 'money in', 'cr'])
            balance_col = self.find_column(headers, ['balance', 'running balance', 'closing balance'])
            
            # Process data rows
            for row_idx in range(header_idx + 1, len(table)):
                row = table[row_idx]
                
                # Extract date
                date = None
                if date_col is not None and date_col < len(row):
                    date_str = str(row[date_col]).strip()
                    if self.is_valid_australian_date(date_str):
                        date = self.parse_australian_date(date_str, year)
                
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
                    amount = self.extract_australian_amount(str(row[amount_col]))
                
                # Try separate debit/credit columns
                if amount is None:
                    if debit_col is not None and debit_col < len(row):
                        debit_amt = self.extract_australian_amount(str(row[debit_col]))
                        if debit_amt:
                            amount = -abs(debit_amt)
                    
                    if credit_col is not None and credit_col < len(row):
                        credit_amt = self.extract_australian_amount(str(row[credit_col]))
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
        
        # Common patterns for Australian bank transactions
        patterns = [
            # Date at start: D/MM or DD/MM Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*(?:CR|DR)?$',
            # Full date: D/MM/YYYY or DD/MM/YYYY Description Amount
            r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*(?:CR|DR)?$',
            # Date with spaces: DD MM YYYY Description Amount
            r'^(\d{1,2}\s+\d{1,2}\s+\d{2,4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*(?:CR|DR)?$',
            # With reference: DD/MM REF Description Amount Balance
            r'^(\d{1,2}/\d{1,2})\s+\S+\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*(?:CR|DR)?\s+\$?[\d,]+\.?\d*\s*(?:CR|DR)?$'
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
                    date = self.parse_australian_date(date_str, year)
                    if not date:
                        continue
                    
                    # Parse amount
                    amount = self.extract_australian_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Check for CR/DR indicators
                    if 'DR' in line.upper() or self.is_debit_transaction(description, line):
                        amount = -abs(amount)
                    elif 'CR' in line.upper():
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': self.clean_description(description),
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def parse_australian_date(self, date_str: str, year: Optional[int] = None) -> Optional[datetime]:
        """Parse Australian-specific date formats"""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # Handle Australian date with spaces (DD MM YYYY)
        date_str = re.sub(r'(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})', r'\1/\2/\3', date_str)
        
        # Try parsing with base method
        return self.parse_date(date_str, year)
    
    def is_valid_australian_date(self, date_str: str) -> bool:
        """Check if string could be a valid Australian date"""
        if not self.is_valid_date(date_str):
            return False
            
        # Additional Australian date validation
        # Check for D/M or DD/MM format
        if re.match(r'^\d{1,2}/\d{1,2}', date_str):
            parts = date_str.split('/')
            if len(parts) >= 2:
                try:
                    day = int(parts[0])
                    month = int(parts[1])
                    # Australian format has day first
                    if 1 <= day <= 31 and 1 <= month <= 12:
                        return True
                except:
                    pass
                    
        return True
    
    def extract_australian_amount(self, amount_str: str) -> Optional[float]:
        """Extract amount with Australian formatting"""
        if not amount_str:
            return None
            
        # Handle CR/DR suffixes
        amount_str = re.sub(r'\s*(CR|DR)\s*$', '', amount_str, flags=re.IGNORECASE)
        
        # Use base extraction
        return self.extract_amount(amount_str)
    
    def find_header_row(self, table: List[List[str]]) -> Optional[int]:
        """Find the header row in a table"""
        for i, row in enumerate(table):
            if not row:
                continue
                
            row_text = ' '.join(str(cell).lower() for cell in row if cell)
            
            # Check for Australian-specific header keywords
            au_keywords = ['date', 'description', 'narrative', 'debit', 'credit', 
                          'dr', 'cr', 'balance', 'particulars', 'value date']
            
            if any(keyword in row_text for keyword in au_keywords):
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
            'eftpos', 'withdrawal', 'payment', 'transfer', 'direct debit',
            'fee', 'charge', 'atm', 'pos', 'purchase', 'bpay'
        ]
        
        credit_keywords = [
            'deposit', 'credit', 'salary', 'wages', 'transfer credit',
            'interest', 'dividend', 'refund'
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