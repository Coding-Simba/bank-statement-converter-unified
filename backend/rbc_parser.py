#!/usr/bin/env python3
"""
RBC (Royal Bank of Canada) PDF Parser
Handles RBC personal and business account statements
"""

import re
import pandas as pd
from datetime import datetime
import tabula
import pdfplumber


class RBCParser:
    def __init__(self):
        self.bank_name = "RBC"
        self.statement_year = None
        self.statement_months = []
        
    def extract_transactions(self, pdf_path):
        """Extract transactions from RBC PDF"""
        all_transactions = []
        
        try:
            # Extract statement period to get year
            self._extract_statement_period(pdf_path)
            
            # Try tabula first for table extraction
            transactions_tabula = self._extract_with_tabula(pdf_path)
            if transactions_tabula:
                all_transactions.extend(transactions_tabula)
            
            # Also try pdfplumber for better text extraction
            transactions_plumber = self._extract_with_pdfplumber(pdf_path)
            if transactions_plumber:
                all_transactions.extend(transactions_plumber)
            
            # Remove duplicates
            all_transactions = self._remove_duplicates(all_transactions)
            
            # Sort by date
            all_transactions.sort(key=lambda x: x.get('date', datetime.min))
            
        except Exception as e:
            print(f"Error parsing RBC PDF: {e}")
            
        return all_transactions
    
    def _extract_statement_period(self, pdf_path):
        """Extract the statement period from the PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text()
                    # Look for "From Month DD, YYYY to Month DD, YYYY"
                    period_match = re.search(r'From\s+(\w+)\s+(\d+),\s+(\d{4})\s+to\s+(\w+)\s+(\d+),\s+(\d{4})', first_page_text)
                    if period_match:
                        self.statement_year = int(period_match.group(3))
                        self.statement_months = [period_match.group(1), period_match.group(4)]
                        return
                    # Alternative format
                    year_match = re.search(r'20[1-2]\d', first_page_text)
                    if year_match:
                        self.statement_year = int(year_match.group())
        except:
            pass
        if not self.statement_year:
            self.statement_year = datetime.now().year
    
    def _extract_with_tabula(self, pdf_path):
        """Extract using tabula-py"""
        transactions = []
        
        try:
            # Read all tables from all pages
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, silent=True)
            
            for table in tables:
                if table.empty:
                    continue
                
                # Look for transaction tables with Date, Description, Withdrawals, Deposits, Balance
                if self._is_transaction_table(table):
                    trans = self._parse_transaction_table(table)
                    transactions.extend(trans)
                    
        except Exception as e:
            print(f"Tabula extraction error: {e}")
            
        return transactions
    
    def _extract_with_pdfplumber(self, pdf_path):
        """Extract using pdfplumber for better text handling"""
        transactions = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Look for transaction patterns in text
                        trans = self._parse_text_transactions(text)
                        transactions.extend(trans)
                        
        except Exception as e:
            print(f"PDFPlumber extraction error: {e}")
            
        return transactions
    
    def _is_transaction_table(self, df):
        """Check if dataframe is likely a transaction table"""
        # Convert column names to string and check for RBC headers
        columns_str = ' '.join([str(col).lower() for col in df.columns])
        
        # RBC specific headers
        has_rbc_headers = any(term in columns_str for term in ['withdrawal', 'deposit', 'balance', 'description'])
        
        # Check for date patterns in first column
        if len(df) > 0:
            first_col = df.iloc[:, 0].astype(str)
            # RBC uses "D Mon" format (e.g., "3 Apr")
            date_pattern = r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            has_dates = any(re.match(date_pattern, val, re.IGNORECASE) for val in first_col[:5])
            
            return has_rbc_headers or has_dates
        
        return False
    
    def _parse_transaction_table(self, df):
        """Parse a transaction table from RBC"""
        transactions = []
        
        # Identify columns
        date_col = None
        desc_col = None
        withdrawal_col = None
        deposit_col = None
        
        # Find columns by header names
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if 'date' in col_str or re.match(r'^\d{1,2}\s+\w{3}', str(df.iloc[0, i]) if len(df) > 0 else ''):
                date_col = i
            elif 'description' in col_str:
                desc_col = i
            elif 'withdrawal' in col_str:
                withdrawal_col = i
            elif 'deposit' in col_str:
                deposit_col = i
        
        # If no explicit columns found, use positions
        if date_col is None and len(df.columns) >= 4:
            date_col = 0
            desc_col = 1
            withdrawal_col = 2
            deposit_col = 3
        
        # Parse rows
        for _, row in df.iterrows():
            try:
                transaction = {}
                
                # Get date
                if date_col is not None:
                    date_str = str(row.iloc[date_col]).strip()
                    date = self._parse_date(date_str)
                    if date:
                        transaction['date'] = date
                        transaction['date_string'] = date_str
                
                # Get description
                if desc_col is not None:
                    desc = str(row.iloc[desc_col]).strip()
                    if desc and desc != 'nan' and desc != 'Opening Balance' and desc != 'Closing Balance':
                        transaction['description'] = desc
                
                # Get amount (check both withdrawal and deposit)
                amount = None
                amount_str = None
                
                if withdrawal_col is not None:
                    withdrawal_str = str(row.iloc[withdrawal_col]).strip()
                    withdrawal = self._parse_amount(withdrawal_str)
                    if withdrawal is not None:
                        amount = -abs(withdrawal)  # Withdrawals are negative
                        amount_str = withdrawal_str
                
                if deposit_col is not None and amount is None:
                    deposit_str = str(row.iloc[deposit_col]).strip()
                    deposit = self._parse_amount(deposit_str)
                    if deposit is not None:
                        amount = abs(deposit)  # Deposits are positive
                        amount_str = deposit_str
                
                if amount is not None:
                    transaction['amount'] = amount
                    transaction['amount_string'] = amount_str
                
                # Only add if we have date, description and amount
                if all(key in transaction for key in ['date', 'description', 'amount']):
                    transactions.append(transaction)
                    
            except Exception as e:
                continue
                
        return transactions
    
    def _parse_text_transactions(self, text):
        """Parse transactions from text using regex"""
        transactions = []
        
        # RBC transaction patterns
        # Format: D Mon Description Amount
        patterns = [
            # Standard transaction with date
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:[\d,]+\.\d{2})?\s*$',
            # e-Transfer patterns
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(e-Transfer.+?)\s+([\d,]+\.\d{2})',
            # Interac purchase patterns
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+((?:Contactless\s+)?Interac\s+purchase.+?)\s+([\d,]+\.\d{2})',
            # Online banking payment
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(Online Banking payment.+?)\s+([\d,]+\.\d{2})',
        ]
        
        lines = text.split('\n')
        
        # Track if we're in the withdrawals or deposits section
        current_type = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if 'Withdrawals ($)' in line:
                current_type = 'withdrawal'
                continue
            elif 'Deposits ($)' in line:
                current_type = 'deposit'
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        date = self._parse_date(date_str)
                        
                        desc = match.group(2).strip()
                        amount_str = match.group(3)
                        amount = self._parse_amount(amount_str)
                        
                        if date and amount is not None:
                            # Determine if it's a withdrawal based on description keywords
                            withdrawal_keywords = ['purchase', 'payment', 'withdrawal', 'transfer sent']
                            is_withdrawal = any(keyword in desc.lower() for keyword in withdrawal_keywords)
                            
                            if is_withdrawal:
                                amount = -abs(amount)
                            else:
                                amount = abs(amount)
                            
                            transactions.append({
                                'date': date,
                                'date_string': date_str,
                                'description': desc,
                                'amount': amount,
                                'amount_string': amount_str
                            })
                            break
                            
                    except Exception as e:
                        continue
                        
        return transactions
    
    def _parse_date(self, date_str):
        """Parse RBC date format (D Mon or DD Mon)"""
        if not date_str or date_str == 'nan':
            return None
            
        date_str = str(date_str).strip()
        
        # RBC uses "D Mon" format (e.g., "3 Apr", "15 May")
        date_match = re.match(r'^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', date_str, re.IGNORECASE)
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2).title()
            
            # Add year
            if self.statement_year:
                try:
                    # Handle month abbreviations
                    month_map = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    month = month_map.get(month_str, 1)
                    return datetime(self.statement_year, month, day)
                except ValueError:
                    pass
        
        return None
    
    def _parse_amount(self, amount_str):
        """Parse amount from string"""
        if not amount_str or amount_str == 'nan' or amount_str == '':
            return None
            
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and commas
        amount_str = amount_str.replace('$', '').replace(',', '').replace('CAD', '').strip()
        
        try:
            return float(amount_str)
        except ValueError:
            return None
    
    def _remove_duplicates(self, transactions):
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for trans in transactions:
            key = (
                trans.get('date'),
                trans.get('description', ''),
                trans.get('amount')
            )
            if key not in seen and key[0] is not None:
                seen.add(key)
                unique.append(trans)
                
        return unique


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf"
    
    parser = RBCParser()
    transactions = parser.extract_transactions(pdf_path)
    
    print(f"Found {len(transactions)} transactions")
    
    # Show first 5 transactions
    for i, trans in enumerate(transactions[:5]):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date')}")
        print(f"  Description: {trans.get('description')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
        
    # Save to CSV
    if transactions:
        df = pd.DataFrame(transactions)
        output_file = pdf_path.replace('.pdf', '_parsed.csv')
        df.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")