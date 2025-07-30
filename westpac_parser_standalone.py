"""Standalone Westpac parser without base class dependencies"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import pandas as pd
import pdfplumber

logger = logging.getLogger(__name__)

def parse_westpac_date(date_str: str, year: int = None) -> Optional[datetime]:
    """Parse Westpac's mixed date formats"""
    if not date_str:
        return None
        
    date_str = date_str.strip()
    
    # Handle dates with year
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        num1 = int(match.group(1))
        num2 = int(match.group(2))
        year_parsed = int(match.group(3))
        
        # Try M/DD/YYYY first (US format commonly used in Westpac PDFs)
        try:
            return datetime(year_parsed, num1, num2)
        except ValueError:
            # Try DD/MM/YYYY (Australian format)
            try:
                return datetime(year_parsed, num2, num1)
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None
    
    # Handle dates without year
    match = re.match(r'^(\d{1,2})/(\d{1,2})$', date_str)
    if match and year:
        num1 = int(match.group(1))
        num2 = int(match.group(2))
        
        # Try M/DD first
        try:
            return datetime(year, num1, num2)
        except ValueError:
            # Try DD/MM
            try:
                return datetime(year, num2, num1)
            except ValueError:
                return None
    
    return None

def parse_westpac(pdf_path: str) -> pd.DataFrame:
    """Parse Westpac PDF and return DataFrame of transactions"""
    logger.info(f"Parsing Westpac PDF: {pdf_path}")
    
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Find current year from statement
                current_year = datetime.now().year
                for line in lines:
                    year_match = re.search(r'\b(20\d{2})\b', line)
                    if year_match:
                        current_year = int(year_match.group(1))
                        break
                
                # Transaction patterns
                # Pattern 1: Date Description Amount (with possible multiple transactions per line)
                # Pattern 2: Date Description on one line, amount on next
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Skip empty lines and headers
                    if not line or 'Opening Balance' in line or 'Closing Balance' in line:
                        i += 1
                        continue
                    
                    # Pattern for transactions: starts with date
                    date_match = re.match(r'^(\d{1,2}/\d{1,2}(?:/\d{4})?)', line)
                    if date_match:
                        date_str = date_match.group(1)
                        parsed_date = parse_westpac_date(date_str, current_year)
                        
                        if parsed_date:
                            # Extract rest of line after date
                            rest_of_line = line[len(date_str):].strip()
                            
                            # Check for amount in the same line
                            amount_match = re.search(r'([+-]?\$?[\d,]+\.?\d*)\s*$', rest_of_line)
                            
                            if amount_match:
                                # Transaction complete on one line
                                amount_str = amount_match.group(1)
                                description = rest_of_line[:amount_match.start()].strip()
                                
                                # Clean amount
                                amount = float(amount_str.replace('$', '').replace(',', ''))
                                
                                transactions.append({
                                    'Date': parsed_date,
                                    'Description': description,
                                    'Amount': amount,
                                    'Balance': 0.0  # Will be calculated later
                                })
                            else:
                                # Amount might be on next line
                                description = rest_of_line
                                
                                # Check next line for amount
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    amount_match = re.search(r'^([+-]?\$?[\d,]+\.?\d*)\s*$', next_line)
                                    
                                    if amount_match:
                                        amount_str = amount_match.group(1)
                                        amount = float(amount_str.replace('$', '').replace(',', ''))
                                        
                                        transactions.append({
                                            'Date': parsed_date,
                                            'Description': description,
                                            'Amount': amount,
                                            'Balance': 0.0
                                        })
                                        i += 1  # Skip the amount line
                    
                    i += 1
        
        # Create DataFrame
        if transactions:
            df = pd.DataFrame(transactions)
            # Sort by date
            df = df.sort_values('Date')
            # Reset index
            df = df.reset_index(drop=True)
            logger.info(f"Extracted {len(df)} transactions from Westpac PDF")
            return df
        else:
            logger.warning("No transactions found in Westpac PDF")
            return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])
            
    except Exception as e:
        logger.error(f"Error parsing Westpac PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])

# For backward compatibility
def parse(pdf_path: str) -> pd.DataFrame:
    return parse_westpac(pdf_path)