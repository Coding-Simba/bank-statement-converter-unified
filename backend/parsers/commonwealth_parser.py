"""Commonwealth Bank (Australia) parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from australian_bank_parser import AustralianBankParser

logger = logging.getLogger(__name__)

class CommonwealthParser(AustralianBankParser):
    """Parser for Commonwealth Bank statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Commonwealth Bank"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Commonwealth Bank statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_commonwealth_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_commonwealth_text(lines, year))
        
        return transactions
    
    def parse_commonwealth_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Commonwealth Bank-specific table format"""
        transactions = []
        
        for table in tables:
            # Commonwealth has dates that are being extracted but not parsed correctly
            # Sample: "27/06/2021 | /06/2021 59.99 $4,935.74 CR | $27.00"
            for row in table:
                if not row:
                    continue
                
                # Join row to reconstruct the line
                line = ' '.join(str(cell) for cell in row if cell)
                
                # Look for Commonwealth date pattern DD/MM/YYYY
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if not date_match:
                    continue
                
                date_str = date_match.group(1)
                date = self.parse_australian_date(date_str, year)
                if not date:
                    continue
                
                # Extract the rest of the line after the date
                remaining = line[date_match.end():].strip()
                
                # Parse Commonwealth format
                # Often has "Value Date: DD/MM/YYYY" which we should skip
                remaining = re.sub(r'Value Date:\s*\d{1,2}/\d{1,2}/\d{4}', '', remaining).strip()
                
                # Extract amount and balance
                # Look for patterns like "59.99 $4,935.74 CR"
                amount = None
                description = ""
                
                # Find all money amounts in the line
                money_pattern = r'\$?([\d,]+\.?\d*)\s*(?:CR|DR)?'
                amounts = re.findall(money_pattern, remaining)
                
                if amounts:
                    # First amount is usually the transaction amount
                    amount = self.extract_amount(amounts[0])
                    
                    # Check for CR/DR indicator
                    if 'DR' in remaining:
                        amount = -abs(amount) if amount else None
                    elif 'CR' in remaining:
                        amount = abs(amount) if amount else None
                    
                    # Description is what's left after removing amounts
                    desc_text = remaining
                    for amt in amounts:
                        desc_text = desc_text.replace(amt, '').replace('$', '')
                    desc_text = re.sub(r'\s*(CR|DR)\s*', '', desc_text)
                    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                    
                    if desc_text:
                        description = desc_text
                
                # If no description found, try to extract from original line
                if not description and date and amount is not None:
                    # Try to find description between date and amount
                    desc_match = re.search(rf'{re.escape(date_str)}\s+(.+?)\s+\$?{re.escape(amounts[0])}', line)
                    if desc_match:
                        description = self.clean_description(desc_match.group(1))
                
                if date and amount is not None:
                    # Generate description if still empty
                    if not description:
                        description = "Transaction"
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_commonwealth_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Commonwealth Bank-specific text format"""
        transactions = []
        
        # Commonwealth patterns
        patterns = [
            # DD MMM format with description and balance (e.g., "04 Jul WORLDREMIT LTD LONDON W14 8U GB GBR")
            r'^(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(.+?)\s+([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)\s*(CR|DR)$',
            # DD MMM with just description and amount
            r'^(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(.+?)\s+([\d,]+\.?\d*)\s*(CR|DR)?$',
            # Full date with description and amounts
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)\s*(CR|DR)$',
            # Date, amount, balance with CR/DR
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)\s*(CR|DR)$',
            # Simple format
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*(CR|DR)?$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
            
            # Skip headers and non-transaction lines
            if any(skip in line.lower() for skip in ['balance', 'brought forward', 'carried forward', 'page']):
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    # Parse based on pattern
                    if pattern_idx == 0:
                        # DD MMM with description, amount and balance
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        cr_dr = match.group(5) if match.lastindex >= 5 else None
                    elif pattern_idx == 1:
                        # DD MMM with description and amount
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        cr_dr = match.group(4) if match.lastindex >= 4 else None
                    elif len(match.groups()) >= 5:
                        # Full format
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        cr_dr = match.group(5)
                    elif len(match.groups()) == 4 and not re.match(r'[\d,]+\.?\d*', match.group(2)):
                        # Has description
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        cr_dr = match.group(4) if match.lastindex >= 4 else None
                    else:
                        # No description
                        description = "Transaction"
                        amount_str = match.group(2)
                        cr_dr = match.group(4) if match.lastindex >= 4 else match.group(3)
                    
                    # Parse date
                    date = self.parse_australian_date(date_str, year)
                    if not date:
                        continue
                    
                    # Clean description
                    description = self.clean_commonwealth_description(description)
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Apply CR/DR
                    if cr_dr == 'DR':
                        amount = -abs(amount)
                    elif cr_dr == 'CR':
                        amount = abs(amount)
                    else:
                        # Guess based on description
                        if self.is_commonwealth_debit(description):
                            amount = -abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def clean_commonwealth_description(self, desc: str) -> str:
        """Clean Commonwealth Bank-specific description format"""
        # Remove date fragments
        desc = re.sub(r'/\d{2}/\d{4}', '', desc)
        desc = re.sub(r'Value Date:.*', '', desc)
        
        # Remove transaction codes
        desc = re.sub(r'^\d{6,}\s+', '', desc)
        
        # Clean up
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        return self.clean_description(desc)
    
    def is_commonwealth_debit(self, description: str) -> bool:
        """Determine if Commonwealth transaction is a debit"""
        desc_lower = description.lower()
        
        credit_keywords = [
            'deposit', 'credit', 'transfer credit', 'salary',
            'wages', 'interest', 'dividend', 'refund'
        ]
        
        debit_keywords = [
            'payment', 'purchase', 'withdrawal', 'eftpos',
            'transfer debit', 'direct debit', 'fee', 'charge',
            'atm', 'bill payment'
        ]
        
        # Check credits first
        for keyword in credit_keywords:
            if keyword in desc_lower:
                return False
        
        # Then debits
        for keyword in debit_keywords:
            if keyword in desc_lower:
                return True
        
        return True  # Default to debit