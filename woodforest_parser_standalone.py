"""Standalone Woodforest parser without base class dependencies"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
import pandas as pd
import pdfplumber

logger = logging.getLogger(__name__)

def parse_woodforest(pdf_path: str) -> pd.DataFrame:
    """Parse Woodforest PDF and return DataFrame of transactions"""
    logger.info(f"Parsing Woodforest PDF: {pdf_path}")
    
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                current_year = datetime.now().year
                
                # Find year from statement
                for line in lines:
                    year_match = re.search(r'Statement Period.*\b(20\d{2})\b', line)
                    if year_match:
                        current_year = int(year_match.group(1))
                        break
                
                # Process each line
                for line in lines:
                    line = line.strip()
                    
                    # Skip headers and empty lines
                    if not line or 'Beginning Balance' in line or 'Ending Balance' in line:
                        continue
                    
                    # Woodforest format: MM-DD Description Amount Balance
                    # Example: 02-01 203.00 205.01 DEPOSIT
                    # Also check for MM/DD format
                    
                    # Match date at start of line (both MM-DD and MM/DD formats)
                    date_match = re.match(r'^(\d{2}[-/]\d{2})\s+', line)
                    if date_match:
                        date_str = date_match.group(1)
                        
                        try:
                            # Parse MM/DD or MM-DD format
                            if '/' in date_str:
                                month, day = map(int, date_str.split('/'))
                            else:
                                month, day = map(int, date_str.split('-'))
                            trans_date = datetime(current_year, month, day)
                            
                            # Extract rest of line
                            rest_of_line = line[len(date_match.group(0)):]
                            
                            # Woodforest format: Date Credits Debits Balance Description
                            # Example: 02-01 203.00 205.01 DEPOSIT
                            # Numbers without $ sign
                            
                            # Find all numbers in the line
                            numbers = re.findall(r'[\d,]+\.?\d*', rest_of_line)
                            
                            if numbers and len(numbers) >= 2:
                                # Could be Credits Debits Balance or just Amount Balance
                                # Check which columns have values
                                if len(numbers) >= 3:
                                    # Might have credits, debits, balance
                                    credit_str = numbers[0]
                                    debit_str = numbers[1] 
                                    balance_str = numbers[2]
                                    
                                    # Determine if credit or debit
                                    credit = float(credit_str.replace(',', '')) if credit_str != '0.00' else 0
                                    debit = float(debit_str.replace(',', '')) if debit_str != '0.00' else 0
                                    
                                    if credit > 0:
                                        amount = credit
                                    elif debit > 0:
                                        amount = -debit
                                    else:
                                        # Check the third number - might be the actual amount
                                        amount = float(balance_str.replace(',', ''))
                                        
                                    # Find description after all numbers
                                    last_num_pos = rest_of_line.rfind(balance_str) + len(balance_str)
                                    description = rest_of_line[last_num_pos:].strip()
                                else:
                                    # Just amount and balance
                                    amount = float(numbers[0].replace(',', ''))
                                    balance_str = numbers[1] if len(numbers) > 1 else "0"
                                    
                                    # Description after numbers
                                    last_num_pos = rest_of_line.rfind(numbers[-1]) + len(numbers[-1])
                                    description = rest_of_line[last_num_pos:].strip()
                                
                                # Parse balance if available
                                balance = 0.0
                                if balance_str:
                                    balance = float(balance_str.replace('$', '').replace(',', '').replace('-', ''))
                                
                                transactions.append({
                                    'Date': trans_date,
                                    'Description': description,
                                    'Amount': amount,
                                    'Balance': balance
                                })
                                
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Could not parse line: {line} - {e}")
                            continue
        
        # Create DataFrame
        if transactions:
            df = pd.DataFrame(transactions)
            df = df.sort_values('Date')
            df = df.reset_index(drop=True)
            logger.info(f"Extracted {len(df)} transactions from Woodforest PDF")
            return df
        else:
            logger.warning("No transactions found in Woodforest PDF")
            return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])
            
    except Exception as e:
        logger.error(f"Error parsing Woodforest PDF: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Balance'])

# For backward compatibility
def parse(pdf_path: str) -> pd.DataFrame:
    return parse_woodforest(pdf_path)