"""Discover Bank parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from us_bank_parser import USBankParser

logger = logging.getLogger(__name__)

class DiscoverParser(USBankParser):
    """Parser for Discover Bank statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "Discover Bank"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from Discover Bank statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Discover has complex layouts, try multiple approaches
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_discover_tables(tables, year))
        
        # Also try text extraction with special handling
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_discover_text(lines, year))
        
        # If still no transactions, try alternative parsing
        if not transactions:
            transactions.extend(self.parse_discover_alternative(pdf_path, year))
        
        return transactions
    
    def parse_discover_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse Discover Bank-specific table format"""
        transactions = []
        
        for table in tables:
            # Discover uses various table formats
            # Look for transaction-like patterns
            for row in table:
                if not row or len(row) < 2:
                    continue
                
                # Skip headers
                row_text = ' '.join(str(cell).lower() for cell in row if cell)
                if any(header in row_text for header in ['date', 'description', 'amount', 'balance', 'transaction']):
                    continue
                
                # Try to extract transaction data
                date = None
                description = ""
                amount = None
                
                # Look for date patterns in cells
                for i, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    
                    # Check for date
                    if not date:
                        # Discover might use MM/DD or MM-DD format
                        date_match = re.match(r'^(\d{1,2}[/-]\d{1,2})$', cell_str)
                        if date_match:
                            date = self.parse_date(date_match.group(1), year)
                            continue
                    
                    # Check for amount
                    if not amount:
                        # Skip transaction/reference numbers
                        if re.match(r'^\d{2}-\d{2}-\d{4}$', cell_str):
                            continue
                        
                        amount_candidate = self.extract_amount(cell_str)
                        if amount_candidate is not None and amount_candidate != 0:
                            amount = amount_candidate
                            continue
                    
                    # Everything else could be description
                    if cell_str and not re.match(r'^[\d\s\-]+$', cell_str):
                        if description:
                            description += " " + cell_str
                        else:
                            description = cell_str
                
                if date and amount is not None:
                    # Clean up description
                    description = self.clean_discover_description(description)
                    
                    # Determine debit/credit
                    if self.is_discover_debit(description, row_text):
                        amount = -abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description if description else "Discover Transaction",
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
        
        return transactions
    
    def parse_discover_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse Discover Bank-specific text format"""
        transactions = []
        
        # Discover patterns
        patterns = [
            # MMM DD MMM DD Description Amount (e.g., "Oct 13 Oct 13 INTERNET PAYMENT - THANK YOU -80.00")
            r'^([A-Za-z]{3}\s+\d{1,2})\s+[A-Za-z]{3}\s+\d{1,2}\s+(.+?)\s+([-]?[\d,]+\.?\d*)\s*$',
            # Date Reference Description Amount
            r'^(\d{1,2}[/-]\d{1,2})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Date Description Amount
            r'^(\d{1,2}[/-]\d{1,2})\s+(.+?)\s+\$?([\d,]+\.?\d*)\s*$',
            # Special format with transaction codes
            r'^(\d{2}-\d{2})-(\d{4})\s+(\d{2}-\d{2})\d{2,}\s+\$?([\d,]+\.?\d*)\s*$'
        ]
        
        in_transaction_section = False
        
        for i, line in enumerate(lines):
            # Check for transaction section markers
            if 'transaction' in line.lower():
                in_transaction_section = True
                continue
            
            if 'summary' in line.lower() or 'total' in line.lower():
                in_transaction_section = False
            
            if not line.strip():
                continue
            
            # Try patterns
            matched = False
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    if pattern_idx == 0:
                        # MMM DD MMM DD Description Amount
                        date_str = match.group(1)  # e.g., "Oct 13"
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    elif pattern_idx == 1:
                        # Has reference number
                        date_str = match.group(1)
                        ref_num = match.group(2)
                        description = match.group(3).strip()
                        amount_str = match.group(4)
                    elif pattern_idx == 2:
                        # Standard format
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                    else:
                        # Special format
                        date_str = f"{match.group(1)}-{match.group(2)}"
                        description = "Transaction"
                        amount_str = match.group(4)
                    
                    # Parse date
                    date = self.parse_date(date_str, year)
                    if not date:
                        continue
                    
                    # Clean description
                    description = self.clean_discover_description(description)
                    
                    # Parse amount
                    amount = self.extract_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Check next line for additional description
                    if i + 1 < len(lines) and not re.match(r'^\d{1,2}[/-]\d{1,2}', lines[i + 1]):
                        next_line = lines[i + 1].strip()
                        if next_line and not any(skip in next_line.lower() for skip in ['total', 'balance', 'page']):
                            description += " " + next_line
                    
                    # Determine debit/credit
                    if self.is_discover_debit(description, line):
                        amount = -abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{abs(amount):.2f}"
                    })
                    matched = True
                    break
            
            # If no pattern matched but we're in transaction section, try alternative parsing
            if not matched and in_transaction_section and re.search(r'\d', line):
                # Try to extract any date and amount
                date_match = re.search(r'(\d{1,2}[/-]\d{1,2})', line)
                amount_match = re.search(r'\$?([\d,]+\.?\d{2})', line)
                
                if date_match and amount_match:
                    date = self.parse_date(date_match.group(1), year)
                    amount = self.extract_amount(amount_match.group(1))
                    
                    if date and amount is not None:
                        # Extract description by removing date and amount
                        description = line
                        description = description.replace(date_match.group(0), '')
                        description = description.replace(amount_match.group(0), '')
                        description = self.clean_discover_description(description)
                        
                        transactions.append({
                            'date': date,
                            'date_string': date.strftime('%m/%d/%Y'),
                            'description': description if description else "Discover Transaction",
                            'amount': -abs(amount),  # Default to debit
                            'amount_string': f"{abs(amount):.2f}"
                        })
        
        return transactions
    
    def parse_discover_alternative(self, pdf_path: str, year: int) -> List[Dict]:
        """Alternative parsing method for difficult Discover formats"""
        transactions = []
        
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Try to extract with layout preservation
                    text = page.extract_text(layout=True)
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    # Look for transaction patterns with better spacing
                    for line in lines:
                        # Pattern for spaced layout
                        parts = re.split(r'\s{2,}', line.strip())
                        if len(parts) >= 3:
                            # Check first part for date
                            date_match = re.match(r'^(\d{1,2}[/-]\d{1,2})$', parts[0])
                            if date_match:
                                date = self.parse_date(date_match.group(1), year)
                                if date:
                                    # Look for amount in remaining parts
                                    for part in reversed(parts[1:]):
                                        amount = self.extract_amount(part)
                                        if amount is not None:
                                            # Description is everything between date and amount
                                            desc_parts = parts[1:-1] if part == parts[-1] else parts[1:]
                                            description = ' '.join(desc_parts).strip()
                                            description = self.clean_discover_description(description)
                                            
                                            transactions.append({
                                                'date': date,
                                                'date_string': date.strftime('%m/%d/%Y'),
                                                'description': description if description else "Discover Transaction",
                                                'amount': -abs(amount),  # Default to debit
                                                'amount_string': f"{abs(amount):.2f}"
                                            })
                                            break
        except Exception as e:
            logger.warning(f"Alternative Discover parsing failed: {e}")
        
        return transactions
    
    def clean_discover_description(self, desc: str) -> str:
        """Clean Discover-specific description format"""
        # Remove reference numbers
        desc = re.sub(r'\d{2}-\d{2}-\d{4}', '', desc)
        desc = re.sub(r'\d{2}-\d{2}\d{3,}', '', desc)
        
        # Remove transaction codes
        desc = re.sub(r'^\d{6,}\s*', '', desc)
        desc = re.sub(r'\s+\d{10,}$', '', desc)
        
        # Clean up
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        return self.clean_description(desc)
    
    def is_discover_debit(self, description: str, full_line: str) -> bool:
        """Determine if Discover transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        credit_keywords = [
            'payment', 'credit', 'refund', 'cashback',
            'reward', 'adjustment credit', 'return'
        ]
        
        # For Discover, credits are payments TO the card
        for keyword in credit_keywords:
            if keyword in desc_lower or keyword in line_lower:
                return False
        
        # Most Discover transactions are debits (purchases)
        return True