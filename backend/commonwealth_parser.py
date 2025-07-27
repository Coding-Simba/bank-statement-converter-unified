#\!/usr/bin/env python3
"""
Commonwealth Bank of Australia PDF Parser
Handles Commonwealth Bank personal and business account statements
"""

import re
import pandas as pd
from datetime import datetime
import tabula
import pdfplumber


class CommonwealthParser:
    def __init__(self):
        self.bank_name = "Commonwealth Bank"
        self.statement_year = None
        self.statement_period = None
        
    def extract_transactions(self, pdf_path):
        """Extract transactions from Commonwealth Bank PDF"""
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
            print(f"Error parsing Commonwealth Bank PDF: {e}")
            
        return all_transactions
    
    def _extract_statement_period(self, pdf_path):
        """Extract the statement period from the PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text()
                    # Look for "Period DD Mon YYYY - DD Mon YYYY"
                    period_match = re.search(r'Period\s+(\d{1,2}\s+\w{3}\s+\d{4})\s*-\s*(\d{1,2}\s+\w{3}\s+\d{4})', first_page_text)
                    if period_match:
                        # Extract year from the period
                        year_match = re.search(r'(\d{4})', period_match.group(1))
                        if year_match:
                            self.statement_year = int(year_match.group(1))
                        self.statement_period = (period_match.group(1), period_match.group(2))
                        return
                    # Alternative: look for year in statement
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
                
                # Look for transaction tables
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
                for page_num, page in enumerate(pdf.pages):
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
        # Convert column names to string and check for headers
        columns_str = ' '.join([str(col).lower() for col in df.columns])
        
        # Commonwealth specific headers
        has_headers = any(term in columns_str for term in ['date', 'transaction', 'debit', 'credit', 'balance'])
        
        # Check for date patterns in first column
        if len(df) > 0:
            first_col = df.iloc[:, 0].astype(str)
            # Commonwealth uses "DD Mon" format
            date_pattern = r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            has_dates = any(re.match(date_pattern, val, re.IGNORECASE) for val in first_col[:5])
            
            return has_headers or has_dates
        
        return False
    
    def _parse_transaction_table(self, df):
        """Parse a transaction table from Commonwealth Bank"""
        transactions = []
        
        # Identify columns (Date, Transaction, Debit, Credit, Balance)
        date_col = None
        desc_col = None
        debit_col = None
        credit_col = None
        
        # Find columns by header names or position
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if 'date' in col_str or i == 0:
                date_col = i
            elif 'transaction' in col_str or i == 1:
                desc_col = i
            elif 'debit' in col_str:
                debit_col = i
            elif 'credit' in col_str:
                credit_col = i
        
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
                    if desc and desc != 'nan' and 'BALANCE' not in desc.upper():
                        transaction['description'] = desc
                
                # Get amount (check both debit and credit)
                amount = None
                amount_str = None
                
                if debit_col is not None:
                    debit_str = str(row.iloc[debit_col]).strip()
                    debit = self._parse_amount(debit_str)
                    if debit is not None:
                        amount = -abs(debit)  # Debits are negative
                        amount_str = debit_str
                
                if credit_col is not None and amount is None:
                    credit_str = str(row.iloc[credit_col]).strip()
                    credit = self._parse_amount(credit_str)
                    if credit is not None:
                        amount = abs(credit)  # Credits are positive
                        amount_str = credit_str
                
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
        
        # Commonwealth Bank transaction patterns
        patterns = [
            # Date at start followed by merchant and amount
            r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(.+?)\s+([\d,]+\.\d{2})\s+\$[\d,]+\.\d{2}\s+CR',
            # With card number
            r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(.+?Card\s+xx\d+.*?)\s+([\d,]+\.\d{2})',
            # Transfer patterns
            r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(Transfer\s+.+?)\s+([\d,]+\.\d{2})',
            # Direct debit/credit
            r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+(Direct\s+(?:Debit|Credit).+?)\s+([\d,]+\.\d{2})',
            # Generic pattern
            r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+([A-Z].+?)\s+([\d,]+\.\d{2})',
        ]
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or 'OPENING BALANCE' in line or 'CLOSING BALANCE' in line:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        date = self._parse_date(date_str)
                        
                        desc = match.group(2).strip()
                        
                        # Clean up description - remove extra info
                        desc = re.sub(r'\s+Value Date:.*', '', desc)
                        desc = re.sub(r'\s+AUD\s+[\d,]+\.\d{2}', '', desc)
                        desc = desc.strip()
                        
                        amount_str = match.group(3)
                        amount = self._parse_amount(amount_str)
                        
                        if date and amount is not None:
                            # Check if it's a debit or credit
                            # Look at the balance change or presence of CR
                            if 'CR' in line and i < len(lines) - 1:
                                # This is likely a credit
                                amount = abs(amount)
                            else:
                                # Check next line for value date info
                                if i + 1 < len(lines) and 'Value Date:' in lines[i + 1]:
                                    # This is typically a debit
                                    amount = -abs(amount)
                                else:
                                    # Default to debit for purchases
                                    if any(keyword in desc.lower() for keyword in ['purchase', 'payment', 'withdrawal', 'transfer to']):
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
        """Parse Commonwealth Bank date format (DD Mon)"""
        if not date_str or date_str == 'nan':
            return None
            
        date_str = str(date_str).strip()
        
        # Commonwealth uses "DD Mon" format with optional year
        date_patterns = [
            (r'^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})$', '%d %b %Y'),
            (r'^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$', None)
        ]
        
        for pattern, fmt in date_patterns:
            match = re.match(pattern, date_str, re.IGNORECASE)
            if match:
                if fmt:
                    # Full date with year
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        pass
                else:
                    # Date without year - use statement year
                    day = int(match.group(1))
                    month_str = match.group(2).title()
                    
                    if self.statement_year:
                        try:
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
        
        # Remove currency symbols and text
        amount_str = amount_str.replace('$', '').replace(',', '').replace('AUD', '').replace('CR', '').strip()
        
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
        pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf"
    
    parser = CommonwealthParser()
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