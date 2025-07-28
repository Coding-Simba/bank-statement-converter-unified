"""BECU (Boeing Employees' Credit Union) parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class BECUParser(USBankParser):
    """Parser for BECU statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "BECU"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from BECU statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_becu_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_becu_text(lines, year))
        
        return transactions
    
    def parse_becu_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse BECU-specific table format"""
        transactions = []
        
        for table in tables:
            # Find header row
            header_idx = None
            for i, row in enumerate(table):
                if not row:
                    continue
                row_text = ' '.join(str(cell).lower() for cell in row if cell)
                # BECU uses specific headers
                if 'date' in row_text and ('amount' in row_text or 'debit' in row_text or 'credit' in row_text):
                    header_idx = i
                    break
            
            if header_idx is None:
                continue
            
            headers = [str(h).lower() for h in table[header_idx]]
            
            # Find column indices
            date_col = self.find_column(headers, ['date', 'trans date', 'post date'])
            desc_col = self.find_column(headers, ['description', 'transaction description', 'details'])
            amount_col = self.find_column(headers, ['amount'])
            debit_col = self.find_column(headers, ['debit', 'debits', 'withdrawals'])
            credit_col = self.find_column(headers, ['credit', 'credits', 'deposits'])
            
            # Process data rows
            for row_idx in range(header_idx + 1, len(table)):
                row = table[row_idx]
                if not row or len(row) < 2:
                    continue
                
                # Extract date
                date = None
                if date_col is not None and date_col < len(row):
                    date_str = str(row[date_col]).strip()
                    # BECU format: MM/DD
                    if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
                        date = self.parse_date(date_str, year)
                
                if not date:
                    continue
                
                # Extract description
                description = ""
                if desc_col is not None and desc_col < len(row):
                    description = str(row[desc_col]).strip()
                    # BECU often includes transaction type in description
                    description = self.clean_becu_description(description)
                
                # Extract amount
                amount = None
                
                # Try single amount column
                if amount_col is not None and amount_col < len(row):
                    amount = self.extract_amount(str(row[amount_col]))
                
                # Try separate debit/credit columns
                if amount is None:
                    if credit_col is not None and credit_col < len(row):
                        credit_amt = self.extract_amount(str(row[credit_col]))
                        if credit_amt:
                            amount = abs(credit_amt)
                    
                    if debit_col is not None and debit_col < len(row):
                        debit_amt = self.extract_amount(str(row[debit_col]))
                        if debit_amt:
                            amount = -abs(debit_amt)
                
                if amount is not None and description:
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_becu_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse BECU-specific text format"""
        transactions = []
        
        # BECU patterns
        patterns = [
            # Standard: MM/DD Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # With type: MM/DD TYPE Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(?:External\s+)?(?:Deposit|Withdrawal|Transfer|Payment)\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Special case for dividend/interest
            r'^(\d{1,2}/\d{1,2})\s+(Dividend/Interest)\s+\$?([\d,]+\.?\d*)\s*$'
        ]
        
        in_transaction_section = False
        
        for line in lines:
            # Check for transaction section
            if 'transaction' in line.lower() and 'history' in line.lower():
                in_transaction_section = True
                continue
            
            if 'ending balance' in line.lower() or 'totals' in line.lower():
                in_transaction_section = False
            
            if not in_transaction_section and not re.match(r'^\d{1,2}/\d{1,2}', line):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    # Handle different group counts
                    if match.lastindex == 3:
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    else:
                        description = match.group(2).strip() if match.lastindex >= 2 else ""
                        amount_str = match.group(match.lastindex)
                    
                    # Parse date
                    date = self.parse_date(date_str, year)
                    if not date:
                        continue
                    
                    # Clean description
                    description = self.clean_becu_description(description)
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Determine debit/credit
                    if self.is_becu_debit(description, line):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def clean_becu_description(self, desc: str) -> str:
        """Clean BECU-specific description format"""
        # Remove common prefixes
        prefixes_to_remove = [
            'External Deposit ',
            'External Withdrawal ',
            'External Transfer ',
            'External Payment '
        ]
        
        for prefix in prefixes_to_remove:
            if desc.startswith(prefix):
                desc = desc[len(prefix):]
        
        # BECU specific cleaning
        desc = re.sub(r'\s*-\s*DIR DEP$', ' - Direct Deposit', desc)
        desc = re.sub(r'\s+', ' ', desc)
        
        return self.clean_description(desc)
    
    def is_becu_debit(self, description: str, full_line: str) -> bool:
        """Determine if BECU transaction is a debit"""
        # BECU credit indicators
        credit_keywords = [
            'deposit', 'dividend', 'interest', 'credit',
            'dir dep', 'direct deposit', 'payroll'
        ]
        
        # BECU debit indicators  
        debit_keywords = [
            'withdrawal', 'payment', 'purchase', 'transfer out',
            'fee', 'charge', 'debit card', 'check', 'bill pay'
        ]
        
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # Check credits first
        for keyword in credit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return False
        
        # Then debits
        for keyword in debit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return True
        
        # Default to debit if unclear
        return True