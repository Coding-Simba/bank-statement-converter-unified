"""ANZ Bank (Australia) parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from australian_bank_parser import AustralianBankParser

logger = logging.getLogger(__name__)

class ANZParser(AustralianBankParser):
    """Parser for ANZ Bank statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "ANZ Bank"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from ANZ statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_anz_tables(tables, year))
        
        # Also try text extraction for ANZ-specific format
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_anz_text(lines, year))
        
        return transactions
    
    def parse_anz_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse ANZ-specific table format"""
        transactions = []
        
        for table in tables:
            # ANZ often has a specific format with date in first column
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                # Skip header rows
                if any(header in str(row[0]).lower() for header in ['date', 'transaction', 'balance']):
                    continue
                
                # First column should be date
                date_str = str(row[0]).strip()
                
                # ANZ format: "1/15" or "15/1" or with year
                date_match = re.match(r'^(\d{1,2}/\d{1,2})', date_str)
                if not date_match:
                    continue
                
                date = self.parse_australian_date(date_match.group(1), year)
                if not date:
                    continue
                
                # Find description and amount
                description = ""
                amount = None
                
                # Description is usually in second column
                if len(row) > 1:
                    desc_candidate = str(row[1]).strip()
                    # Check if it's a valid description (not just a street address fragment)
                    if desc_candidate and not re.match(r'^/\d+\s+\w+\s+ST$', desc_candidate):
                        description = self.clean_description(desc_candidate)
                
                # Amount could be in various columns
                for i in range(2, len(row)):
                    amount_candidate = self.extract_australian_amount(str(row[i]))
                    if amount_candidate is not None:
                        amount = amount_candidate
                        break
                
                # If no amount found in separate column, check if it's in description
                if amount is None and description:
                    # Look for amount at end of description
                    amount_match = re.search(r'\$?([\d,]+\.?\d*)\s*(?:CR|DR)?$', description)
                    if amount_match:
                        amount = self.extract_australian_amount(amount_match.group(1))
                        # Remove amount from description
                        description = description[:amount_match.start()].strip()
                
                if date and description and amount is not None:
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_anz_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse ANZ-specific text format"""
        transactions = []
        
        # ANZ specific patterns
        patterns = [
            # Standard ANZ format: Date Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # With balance: Date Description Amount Balance
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s+\$?[\d,]+\.?\d*\s*$',
            # With reference: Date Ref Description Amount
            r'^(\d{1,2}/\d{1,2})\s+\S+\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$'
        ]
        
        in_transaction_section = False
        
        for line in lines:
            # Check for transaction section markers
            if 'transaction' in line.lower() and 'details' in line.lower():
                in_transaction_section = True
                continue
            
            if 'total' in line.lower() or 'balance' in line.lower():
                in_transaction_section = False
            
            if not in_transaction_section:
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
                    
                    # Clean description - remove address fragments
                    if not self.is_valid_anz_description(description):
                        continue
                    
                    # Parse amount
                    amount = self.extract_australian_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Determine debit/credit
                    if self.is_anz_debit(description):
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
    
    def is_valid_anz_description(self, desc: str) -> bool:
        """Check if description is valid (not a fragment)"""
        # Reject common fragments
        invalid_patterns = [
            r'^/\d+\s+\w+\s+ST$',  # Street address fragment like "/15 ETHEL ST"
            r'^\d+\s+\w+\s+ST$',   # Street address without slash
            r'^ST$',               # Just "ST"
            r'^\d+$'               # Just numbers
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, desc):
                return False
                
        return len(desc) > 2
    
    def is_anz_debit(self, description: str) -> bool:
        """Determine if ANZ transaction is a debit"""
        debit_keywords = [
            'payment', 'purchase', 'withdrawal', 'transfer debit',
            'direct debit', 'eftpos', 'atm', 'fee', 'charge'
        ]
        
        credit_keywords = [
            'deposit', 'credit', 'transfer credit', 'salary',
            'interest', 'refund'
        ]
        
        desc_lower = description.lower()
        
        for keyword in credit_keywords:
            if keyword in desc_lower:
                return False
                
        for keyword in debit_keywords:
            if keyword in desc_lower:
                return True
                
        return True  # Default to debit for ANZ