#!/usr/bin/env python3
"""Generate remaining bank parsers based on templates"""

import os

# Parser configurations
parsers_config = {
    'green_dot': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'Green Dot Bank',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$'],
        'credit_keywords': ['deposit', 'ides payments', 'credit', 'load'],
        'debit_keywords': ['fee', 'withdrawal', 'purchase', 'payment', 'monthly fee']
    },
    'lloyds': {
        'base_class': 'UKBankParser',
        'import_base': 'uk_bank_parser',
        'bank_name': 'Lloyds Bank',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$', r'^\d{1,2}-\d{1,2}-\d{2}$'],
        'credit_keywords': ['credit', 'deposit', 'transfer in', 'salary'],
        'debit_keywords': ['debit', 'dd', 'payment', 'withdrawal', 'purchase']
    },
    'metro': {
        'base_class': 'UKBankParser',
        'import_base': 'uk_bank_parser',
        'bank_name': 'Metro Bank',
        'date_patterns': [r'^\d{1,2}/\d{1,2}/\d{4}$'],
        'credit_keywords': ['credit', 'deposit', 'transfer in'],
        'debit_keywords': ['debit', 'payment', 'card payment', 'withdrawal']
    },
    'nationwide': {
        'base_class': 'UKBankParser',
        'import_base': 'uk_bank_parser',
        'bank_name': 'Nationwide',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$', r'^\d{1,2}\s+\w{3}$'],
        'credit_keywords': ['credit', 'deposit', 'salary', 'transfer in'],
        'debit_keywords': ['debit', 'visa', 'payment', 'withdrawal', 'dd']
    },
    'netspend': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'Netspend',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$', r'^\d{1,2}-\d{1,2}$'],
        'credit_keywords': ['deposit', 'load', 'credit', 'refund'],
        'debit_keywords': ['purchase', 'withdrawal', 'fee', 'payment']
    },
    'paypal': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'PayPal',
        'date_patterns': [r'^[A-Za-z]{3}\s+\d{1,2},\s+\d{4}$', r'^\d{1,2}/\d{1,2}/\d{2}$'],
        'credit_keywords': ['deposit', 'payment received', 'refund', 'transfer from'],
        'debit_keywords': ['payment sent', 'purchase', 'withdrawal', 'transfer to', 'fee']
    },
    'scotiabank': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'Scotiabank',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$', r'^\d{1,2}-\d{1,2}$'],
        'credit_keywords': ['deposit', 'credit', 'transfer in'],
        'debit_keywords': ['withdrawal', 'payment', 'purchase', 'debit']
    },
    'suntrust': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'SunTrust',
        'date_patterns': [r'^\d{1,2}/\d{1,2}/\d{4}$'],
        'credit_keywords': ['deposit', 'credit', 'transfer credit'],
        'debit_keywords': ['debit', 'purchase', 'payment', 'withdrawal']
    },
    'walmart': {
        'base_class': 'USBankParser',
        'import_base': 'us_bank_parser',
        'bank_name': 'Walmart MoneyCard',
        'date_patterns': [r'^\d{1,2}/\d{1,2}$'],
        'credit_keywords': ['deposit', 'load', 'credit', 'refund'],
        'debit_keywords': ['purchase', 'withdrawal', 'payment', 'fee']
    },
    'westpac': {
        'base_class': 'AustralianBankParser',
        'import_base': 'australian_bank_parser',
        'bank_name': 'Westpac',
        'date_patterns': [r'^\d{1,2}/\d{1,2}/\d{4}$'],
        'credit_keywords': ['deposit', 'credit', 'transfer credit', 'salary'],
        'debit_keywords': ['payment', 'withdrawal', 'eftpos', 'transfer debit', 'fee']
    }
}

# Template for bank parser
parser_template = '''"""{bank_name} parser"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from {import_base} import {base_class}

logger = logging.getLogger(__name__)

class {class_name}Parser({base_class}):
    """Parser for {bank_name} statements"""
    
    def __init__(self):
        super().__init__()
        self.bank_name = "{bank_name}"
    
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract transactions from {bank_name} statement"""
        transactions = []
        
        # Detect year from PDF
        year = self.detect_year_from_pdf(pdf_path)
        
        # Try table extraction first
        tables = self.extract_table_data(pdf_path)
        if tables:
            transactions.extend(self.parse_{parser_name}_tables(tables, year))
        
        # Also try text extraction
        lines = self.extract_text_lines(pdf_path)
        if lines:
            transactions.extend(self.parse_{parser_name}_text(lines, year))
        
        return transactions
    
    def parse_{parser_name}_tables(self, tables: List[List[str]], year: int) -> List[Dict]:
        """Parse {bank_name}-specific table format"""
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
                    # Try date patterns
                    for pattern in {date_patterns}:
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
                    if cell_str and not re.match(r'^[\\d,\\.\\$\\-]+$', cell_str) and not re.match(r'^\\d{{1,2}}[/-]\\d{{1,2}}', cell_str):
                        desc_parts.append(cell_str)
                
                description = ' '.join(desc_parts)
                
                # Extract amount (usually last columns)
                for i in range(len(row)-1, -1, -1):
                    amount = self.extract_amount(str(row[i]))
                    if amount is not None:
                        break
                
                if date and amount is not None:
                    description = self.clean_description(description) if description else "{bank_name} Transaction"
                    
                    # Determine debit/credit
                    if self.is_{parser_name}_debit(description, row_text):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({{
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if '{base_class}' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{{abs(amount):.2f}}"
                    }})
        
        return transactions
    
    def parse_{parser_name}_text(self, lines: List[str], year: int) -> List[Dict]:
        """Parse {bank_name}-specific text format"""
        transactions = []
        
        # {bank_name} patterns
        patterns = [
            # Date Description Amount
            r'^({date_pattern_combined})\\s+(.+?)\\s+\\$?([\\d,]+\\.?\\d*)\\s*$',
            # Date Amount Description
            r'^({date_pattern_combined})\\s+\\$?([\\d,]+\\.?\\d*)\\s+(.+?)$'
        ]
        
        for line in lines:
            if not line.strip():
                continue
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    date_str = match.group(1)
                    
                    if pattern_idx == 0:
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
                    if self.is_{parser_name}_debit(description, line):
                        amount = -abs(amount)
                    else:
                        amount = abs(amount)
                    
                    transactions.append({{
                        'date': date,
                        'date_string': date.strftime('%m/%d/%Y' if '{base_class}' == 'USBankParser' else '%d/%m/%Y'),
                        'description': description,
                        'amount': amount,
                        'amount_string': f"{{abs(amount):.2f}}"
                    }})
                    break
        
        return transactions
    
    def is_{parser_name}_debit(self, description: str, full_line: str) -> bool:
        """Determine if {bank_name} transaction is a debit"""
        desc_lower = description.lower()
        line_lower = full_line.lower()
        
        # {bank_name} credit indicators
        credit_keywords = {credit_keywords}
        
        # {bank_name} debit indicators
        debit_keywords = {debit_keywords}
        
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
'''

def generate_parser(parser_name, config):
    """Generate a parser file"""
    class_name = ''.join(word.capitalize() for word in parser_name.split('_'))
    
    # Combine date patterns
    date_pattern_combined = '|'.join(config['date_patterns'])
    
    content = parser_template.format(
        bank_name=config['bank_name'],
        import_base=config['import_base'],
        base_class=config['base_class'],
        class_name=class_name,
        parser_name=parser_name,
        date_patterns=config['date_patterns'],
        date_pattern_combined=date_pattern_combined,
        credit_keywords=config['credit_keywords'],
        debit_keywords=config['debit_keywords']
    )
    
    # Write file
    file_path = f'parsers/{parser_name}_parser.py'
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Generated {file_path}")

def main():
    """Generate all remaining parsers"""
    # Create parsers directory if it doesn't exist
    os.makedirs('parsers', exist_ok=True)
    
    print("Generating remaining bank parsers...")
    
    for parser_name, config in parsers_config.items():
        generate_parser(parser_name, config)
    
    print(f"\nGenerated {len(parsers_config)} parsers successfully!")
    
    # Create __init__.py for parsers module
    init_content = '''"""Bank statement parsers module"""

# Import all parsers
from .becu_parser import BECUParser
from .citizens_parser import CitizensParser
from .commonwealth_parser import CommonwealthParser
from .discover_parser import DiscoverParser
from .green_dot_parser import GreenDotParser
from .lloyds_parser import LloydsParser
from .metro_parser import MetroParser
from .nationwide_parser import NationwideParser
from .netspend_parser import NetspendParser
from .paypal_parser import PaypalParser
from .scotiabank_parser import ScotiabankParser
from .suntrust_parser import SuntrustParser
from .walmart_parser import WalmartParser
from .westpac_parser import WestpacParser

# Parser mapping
BANK_PARSERS = {
    'becu': BECUParser,
    'citizens': CitizensParser,
    'commonwealth': CommonwealthParser,
    'discover': DiscoverParser,
    'green_dot': GreenDotParser,
    'lloyds': LloydsParser,
    'metro': MetroParser,
    'nationwide': NationwideParser,
    'netspend': NetspendParser,
    'paypal': PaypalParser,
    'scotiabank': ScotiabankParser,
    'suntrust': SuntrustParser,
    'walmart': WalmartParser,
    'westpac': WestpacParser
}
'''
    
    with open('parsers/__init__.py', 'w') as f:
        f.write(init_content)
    
    print("Created parsers/__init__.py")

if __name__ == "__main__":
    main()