"""Westpac parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from australian_bank_parser import AustralianBankParser

logger = logging.getLogger(__name__)

class WestpacParser(AustralianBankParser):
    """Parser for Westpac statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Westpac"
        
        # Add specific format for Westpac's D/MM/YYYY without leading zeros
        self.supported_date_formats = [
            '%-d/%-m/%Y',    # 2/11/2022 or 14/2/2022 (no leading zeros)
            '%d/%m/%Y',      # 02/11/2022 or 14/02/2022
            '%-d/%m/%Y',     # 2/11/2022 (no leading zero on day)
            '%d/%-m/%Y',     # 02/11/2022 (no leading zero on month)
        ] + self.supported_date_formats
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Westpac statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_westpac_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_westpac_text(lines, year))
        
        return transactions
    
    def parse_westpac_date(self, date_str: str, year: int) -> Optional[datetime]:
        """Custom date parser for Westpac's mixed date formats"""
        import re
        
        # Match D/M/YYYY or DD/MM/YYYY
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str.strip())
        if match:
            num1 = int(match.group(1))
            num2 = int(match.group(2))
            year_parsed = int(match.group(3))
            
            # For Westpac, transaction dates appear to use M/DD/YYYY format
            # Try M/DD/YYYY first (US format)
            try:
                return datetime(year_parsed, num1, num2)  # month, day
            except ValueError:
                # If that fails, try DD/MM/YYYY (Australian format)
                try:
                    return datetime(year_parsed, num2, num1)  # day, month
                except ValueError:
                    return None
                
        # Try parent parser for other formats
        return self.parse_date(date_str, year)
    
    def parse_westpac_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Westpac-specific table format"""
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
                    # Try date patterns - Westpac uses DD/MM/YYYY or DD/MM
                    for pattern in ['^\\d{1,2}/\\d{1,2}/\\d{4}$', '^\\d{1,2}/\\d{1,2}$']:
                        if re.match(pattern, cell_str):
                            date = self.parse_westpac_date(cell_str, year)
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
                    description = self.clean_description(description) if description else "Westpac Transaction"
                    
                    # Determine debit/credit
                    if self.is_westpac_debit(description, row_text):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if 'AustralianBankParser' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_westpac_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Westpac-specific text format"""
        transactions = []
        
        # Westpac patterns
        patterns = [
            # Date with Amount Currency In Out format (e.g., "2/11/2022 1,136.00 USD 1136.00")
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(\w+)\s+([\d,.-]+)',
            # Date Description Amount (e.g., "12/04/2022 Direct Debit to INSURANCE CORP $89.50")
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Date Amount Description
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+\$?([\d,]+\.?\d*)\s+(.+?)$',
            # Date with DD/MM format and description
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$'
        ]
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    if pattern_idx == 0:
                        # Date Amount Currency In/Out
                        amount_str = match.group(2)
                        currency = match.group(3)
                        in_out = match.group(4)
                        
                        # For this format, check if In/Out field has a negative sign
                        if in_out.startswith('-'):
                            amount_str = '-' + amount_str
                            
                        # Get description from previous line if available
                        description = ""
                        if i > 0:
                            prev_line = lines[i-1].strip()
                            if 'TRANSFER' in prev_line or 'Cash Out' in prev_line or len(prev_line) > 10:
                                description = prev_line
                            
                        # Also check if description is on the same line after the In/Out field
                        if len(match.group(0)) < len(line):
                            remaining = line[match.end():].strip()
                            if remaining:
                                description = remaining if not description else description + ' ' + remaining
                        
                        # Add the In/Out value to make transactions unique
                        if not description:
                            description = f"Westpac Transaction ({in_out})"
                        else:
                            description = f"{description} ({in_out})"
                    elif pattern_idx in [1, 3]:
                        # Date Description Amount
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    else:
                        # Date Amount Description
                        amount_str = match.group(2)
                        description = match.group(3).strip()
                    
                    # Parse date
                    date = self.parse_westpac_date(date_str, year)
                    if not date:
                        continue
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Clean description
                    description = self.clean_description(description)
                    
                    # Determine debit/credit
                    if self.is_westpac_debit(description, line):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if 'AustralianBankParser' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    break
        
        return transactions
    
    def is_westpac_debit(self, description: str, full_line: str) -> bool:
        """Determine if Westpac transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # Westpac credit indicators
        credit_keywords = ['deposit', 'credit', 'transfer credit', 'salary']
        
        # Westpac debit indicators
        debit_keywords = ['payment', 'withdrawal', 'eftpos', 'transfer debit', 'fee', 'cash out']
        
        # Special handling for transfers - if no specific indicator, check the amount sign
        if 'transfer' in desc_lower and 'account replenishment' in desc_lower:
            # This is ambiguous, will be determined by amount sign
            return True
            
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
    
    def remove_duplicates(self, transactions: List[Dict]) -> List[Dict]:
        """Override to handle Westpac's legitimate duplicate transactions"""
        # For Westpac, we don't remove duplicates because the same transaction
        # (same date, amount, description) can legitimately appear multiple times
        # Instead, we'll just return all transactions
        return transactions
