"""BECU (Boeing Employees' Credit Union) parser - Fixed version"""

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
        
        # Try text extraction with specific BECU parsing
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_becu_lines(lines, year))
        
        # Also try table extraction
        tables = self.extract_table_data(pdf_path)
        if tables and len(transactions) < 10:  # If text parsing didn't get enough
            transactions.extend(self.parse_becu_tables(tables, year))
        
        return transactions
    
    def parse_becu_lines(self, lines: List[str], year: int) -> List[Dict]:
        """Parse BECU-specific text format line by line"""
        transactions = []
        
        # BECU pattern: MM/DD amount description or MM/DD (amount) description
        pattern = r'^(\d{1,2}/\d{1,2})\s+(\(?([\d,]+\.?\d*)\)?)\s+(.+)$'
        
        for line in lines:
            if not line.strip():
                continue
            
            match = re.match(pattern, line)
            if match:
                date_str = match.group(1)
                amount_str = match.group(2)
                amount_num = match.group(3)
                description = match.group(4).strip()
                
                # Parse date
                date = self.parse_date(date_str, year)
                if not date:
                    continue
                
                # Parse amount - check if it has parentheses (debit)
                try:
                    amount = float(amount_num.replace(',', ''))
                    if '(' in amount_str:
                        amount = -amount
                except:
                    continue
                
                # Clean description
                description = self.clean_becu_description(description)
                
                transactions.append({
                    'date': date,
                    'date_string': date.strftime('%m/%d/%Y'),
                    'description': description,
                    'amount': amount,
                    'amount_string': f"{abs(amount):.2f}"
                })
        
        return transactions
    
    def parse_becu_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse BECU-specific table format"""
        transactions = []
        
        for table in tables:
            # Skip small tables
            if len(table) < 3:
                continue
            
            # Process each row
            for row in table:
                if not row or len(row) < 3:
                    continue
                
                # Join the row to parse it as a line
                line = ' '.join(str(cell) for cell in row if cell)
                
                # Try to extract transaction data using regex
                # Pattern for BECU transactions
                patterns = [
                    # Date Amount Description
                    r'(\d{1,2}/\d{1,2})\s+([\d,]+\.?\d*)\s+(.+)',
                    # Date (Amount) Description
                    r'(\d{1,2}/\d{1,2})\s+\(([\d,]+\.?\d*)\)\s+(.+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        date_str = match.group(1)
                        amount_str = match.group(2)
                        description = match.group(3).strip()
                        
                        # Parse date
                        date = self.parse_date(date_str, year)
                        if not date:
                            continue
                        
                        # Parse amount
                        try:
                            amount = float(amount_str.replace(',', ''))
                            # Second pattern is for debits
                            if pattern == patterns[1]:
                                amount = -amount
                        except:
                            continue
                        
                        # Clean description
                        description = self.clean_becu_description(description)
                        
                        # Determine if it's a debit based on description
                        if pattern == patterns[0] and self.is_becu_debit(description, line):
                            amount = -abs(amount)
                        
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
            'External Payment ',
            'POS Withdrawal ',
            'POS Deposit ',
            'Withdrawal ',
            'Deposit '
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
            'dir dep', 'direct deposit', 'payroll', 'refund'
        ]
        
        # BECU debit indicators  
        debit_keywords = [
            'withdrawal', 'payment', 'purchase', 'transfer out',
            'fee', 'charge', 'debit card', 'check', 'bill pay',
            'pos withdrawal', 'external withdrawal', 'transfer to'
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