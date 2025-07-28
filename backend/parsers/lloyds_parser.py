"""Lloyds Bank parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from uk_bank_parser import UKBankParser

logger = logging.getLogger(__name__)

class LloydsParser(UKBankParser):
    """Parser for Lloyds Bank statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Lloyds Bank"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Lloyds Bank statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_lloyds_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_lloyds_text(lines, year))
        
        return transactions
    
    def parse_lloyds_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Lloyds Bank-specific table format"""
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
                    # Try date patterns - Lloyds uses various formats
                    for pattern in ['^\\d{1,2}/\\d{1,2}$', '^\\d{1,2}-\\d{1,2}-\\d{2}$', '^\\d{1,2}-[A-Za-z]{3}-\\d{2}$']:
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
                    description = self.clean_description(description) if description else "Lloyds Bank Transaction"
                    
                    # Determine debit/credit
                    if self.is_lloyds_debit(description, row_text):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if 'UKBankParser' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_lloyds_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Lloyds Bank-specific text format"""
        transactions = []
        
        # Lloyds Bank patterns
        patterns = [
            # Date Type Description Amount Balance (e.g., "1-Nov-21 DEB DEBIT CARD PURCHASE AT BP#8988 15.00 190.00")
            r'^(\d{1,2}-[A-Za-z]{3}-\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)$',
            # Date Type Description Amount (no balance)
            r'^(\d{1,2}-[A-Za-z]{3}-\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.?\d*)$',
            # Date Description Amount (e.g., "12/05 DIRECT DEBIT TO ABC LTD 250.00")
            r'^(\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}-\d{2})\s+(.+?)\s+([\d,]+\.?\d*)\s*$',
            # Date Amount Description
            r'^(\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}-\d{2})\s+([\d,]+\.?\d*)\s+(.+?)$',
            # Date with spaces (e.g., "22 Oct Card Payment 45.30")
            r'^(\d{1,2}\s+[A-Za-z]{3})\s+(.+?)\s+([\d,]+\.?\d*)\s*$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    if pattern_idx == 0:
                        # Date Type Description Amount Balance
                        trans_type = match.group(2)
                        description = match.group(3).strip()
                        amount_str = match.group(4)
                    elif pattern_idx == 1:
                        # Date Type Description Amount
                        trans_type = match.group(2)
                        description = match.group(3).strip()
                        amount_str = match.group(4)
                    elif pattern_idx in [2, 4]:
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
                    if self.is_lloyds_debit(description, line):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if 'UKBankParser' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def is_lloyds_debit(self, description: str, full_line: str) -> bool:
        """Determine if Lloyds Bank transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # Lloyds Bank credit indicators
        credit_keywords = ['credit', 'deposit', 'transfer in', 'salary']
        
        # Lloyds Bank debit indicators
        debit_keywords = ['debit', 'dd', 'payment', 'withdrawal', 'purchase']
        
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
