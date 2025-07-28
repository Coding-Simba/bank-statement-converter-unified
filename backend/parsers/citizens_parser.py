"""Citizens Bank parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class CitizensParser(USBankParser):
    """Parser for Citizens Bank statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Citizens Bank"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Citizens Bank statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_citizens_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_citizens_text(lines, year))
        
        return transactions
    
    def parse_citizens_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Citizens Bank-specific table format"""
        transactions = []
        
        for table in tables:
            # Citizens Bank often has complex table structures
            # Look for rows with date patterns
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                # Try to find date in first few columns
                date = None
                date_col = -1
                
                for i in range(min(3, len(row))):
                    cell = str(row[i]).strip()
                    # Citizens uses various date formats
                    if re.match(r'^\d{1,2}/\d{1,2}$', cell):
                        date = self.parse_date(cell, year)
                        if date:
                            date_col = i
                            break
                
                if not date:
                    continue
                
                # Extract description and amount
                description = ""
                amount = None
                
                # Description is usually after date
                if date_col + 1 < len(row):
                    desc_candidate = str(row[date_col + 1]).strip()
                    # Citizens sometimes has check numbers or reference numbers
                    if not re.match(r'^\d{3,6}$', desc_candidate):
                        description = self.clean_citizens_description(desc_candidate)
                    elif date_col + 2 < len(row):
                        # Skip check number, get next column
                        description = self.clean_citizens_description(str(row[date_col + 2]).strip())
                
                # Find amount in remaining columns
                for i in range(date_col + 1, len(row)):
                    amount_candidate = self.extract_amount(str(row[i]))
                    if amount_candidate is not None:
                        amount = amount_candidate
                        
                        # Check if this column or nearby indicates debit/credit
                        if i + 1 < len(row):
                            next_col = str(row[i + 1]).strip().lower()
                            if 'purchase' in next_col or 'withdrawal' in next_col:
                                amount = -abs(amount)
                        break
                
                if date and description and amount is not None:
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_citizens_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Citizens Bank-specific text format"""
        transactions = []
        
        # Citizens patterns - they sometimes have check numbers
        patterns = [
            # Date Check# Description Amount
            r'^(\d{1,2}/\d{1,2})\s+(\d{3,6})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Date Description Amount  
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Date Amount Purchase/Credit - Description
            r'^(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.?\d*)\s+(Purchase|Credit)\s*-\s*(.+)$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    check_num = None
                    
                    if pattern == patterns[0]:
                        # Has check number
                        date_str = match.group(1)
                        check_num = match.group(2)
                        description = f"Check #{check_num} - {match.group(3).strip()}"
                        amount_str = match.group(4)
                        transaction_type = 'debit'
                    elif pattern == patterns[1]:
                        # Standard format
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        transaction_type = self.determine_citizens_type(description)
                    else:
                        # Amount first format
                        date_str = match.group(1)
                        amount_str = match.group(2)
                        transaction_type = match.group(3).lower()
                        description = match.group(4).strip()
                    
                    # Parse date
                    date = self.parse_date(date_str, year)
                    if not date:
                        continue
                    
                    # Clean description
                    description = self.clean_citizens_description(description)
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Apply sign based on type
                    if transaction_type in ['debit', 'purchase', 'withdrawal'] or check_num:
                        amount = -abs(amount)
                    elif transaction_type in ['credit', 'deposit']:
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
    
    def clean_citizens_description(self, desc: str) -> str:
        """Clean Citizens Bank-specific description format"""
        # Remove transaction codes if present
        desc = re.sub(r'^\d{6,}\s+', '', desc)
        
        # Remove trailing reference numbers
        desc = re.sub(r'\s+\d{10,}$', '', desc)
        
        # Citizens specific replacements
        desc = desc.replace('Purchase -', '').strip()
        desc = desc.replace('Credit -', '').strip()
        
        return self.clean_description(desc)
    
    def determine_citizens_type(self, description: str) -> str:
        """Determine transaction type for Citizens Bank"""
        desc_lower = description.lower()
        
        credit_indicators = [
            'deposit', 'credit', 'transfer in', 'refund',
            'interest', 'reversal'
        ]
        
        for indicator in credit_indicators:
            if indicator in desc_lower:
                return 'credit'
        
        return 'debit'