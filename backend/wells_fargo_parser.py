#!/usr/bin/env python3
"""
Wells Fargo PDF Parser
Handles Wells Fargo personal and business account statements
"""

import re
import pandas as pd
from datetime import datetime
import tabula
import pdfplumber


class WellsFargoParser:
    def __init__(self):
        self.bank_name = "Wells Fargo"
        self.current_year = None
        
    def extract_transactions(self, pdf_path):
        """Extract transactions from Wells Fargo PDF"""
        all_transactions = []
        
        try:
            # Extract year from statement
            self.current_year = self._extract_statement_year(pdf_path)
            
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
            print(f"Error parsing Wells Fargo PDF: {e}")
            
        return all_transactions
    
    def _extract_statement_year(self, pdf_path):
        """Extract the statement year from the PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text()
                    # Look for statement period or year
                    year_match = re.search(r'20[1-2]\d', first_page_text)
                    if year_match:
                        return int(year_match.group())
        except:
            pass
        return datetime.now().year
    
    def _extract_with_tabula(self, pdf_path):
        """Extract using tabula-py"""
        transactions = []
        
        try:
            # Read all tables from all pages
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, silent=True)
            
            for table in tables:
                if table.empty:
                    continue
                
                # Wells Fargo tables often have date in first column
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
        if len(df) < 2:
            return False
        
        # Check first column for date patterns (M/D format)
        first_col = df.iloc[:, 0].astype(str)
        date_count = sum(1 for val in first_col[:10] if re.match(r'^\d{1,2}/\d{1,2}$', str(val)))
        
        # Check last columns for amount patterns
        has_amounts = False
        for col_idx in range(len(df.columns) - 1, max(0, len(df.columns) - 3), -1):
            col_vals = df.iloc[:, col_idx].astype(str)
            amount_count = sum(1 for val in col_vals[:10] 
                             if re.match(r'^-?\d+[,.]?\d*\.?\d*$', str(val).replace(',', '')))
            if amount_count > 2:
                has_amounts = True
                break
        
        return date_count > 2 or has_amounts
    
    def _parse_transaction_table(self, df):
        """Parse a transaction table from Wells Fargo"""
        transactions = []
        
        # Wells Fargo format: Date | Description | Amount (sometimes split across columns)
        for _, row in df.iterrows():
            try:
                transaction = {}
                
                # Get date from first column
                date_str = str(row.iloc[0]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
                    # Add year to date
                    full_date_str = f"{date_str}/{self.current_year}"
                    date = self._parse_date(full_date_str)
                    if date:
                        transaction['date'] = date
                        transaction['date_string'] = date_str
                
                # Get description (usually second column)
                if len(row) > 1:
                    desc_parts = []
                    for i in range(1, len(row) - 1):
                        val = str(row.iloc[i]).strip()
                        if val and val != 'nan' and not self._is_amount(val):
                            desc_parts.append(val)
                    if desc_parts:
                        transaction['description'] = ' '.join(desc_parts)
                
                # Get amount (usually last column or second to last)
                amount = None
                for i in range(len(row) - 1, max(0, len(row) - 3), -1):
                    amount_str = str(row.iloc[i])
                    amount = self._parse_amount(amount_str)
                    if amount is not None:
                        transaction['amount'] = amount
                        transaction['amount_string'] = amount_str
                        break
                
                # Only add if we have date and amount
                if 'date' in transaction and 'amount' in transaction:
                    transactions.append(transaction)
                    
            except Exception as e:
                continue
                
        return transactions
    
    def _parse_text_transactions(self, text):
        """Parse transactions from text using regex"""
        transactions = []
        
        # Wells Fargo transaction patterns
        patterns = [
            # Standard format: M/D Description Amount
            r'(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.?\d*)\s*$',
            # With authorized on date
            r'(\d{1,2}/\d{1,2})\s+(.*?authorized on \d{2}/\d{2}.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.?\d*)\s*$',
            # ATM transactions
            r'(\d{1,2}/\d{1,2})\s+(ATM.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.?\d*)\s*$',
            # Money transfers
            r'(\d{1,2}/\d{1,2})\s+(Money Transfer.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.?\d*)\s*$',
            # Square/payment processor transactions
            r'(\d{1,2}/\d{1,2})\s+(Square Inc.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.?\d*)\s*$',
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        # Add year to date
                        full_date_str = f"{date_str}/{self.current_year}"
                        date = self._parse_date(full_date_str)
                        
                        desc = match.group(2).strip()
                        amount_str = match.group(3)
                        amount = self._parse_amount(amount_str)
                        
                        if date and amount is not None:
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
        """Parse Wells Fargo date format (M/D/YYYY or M/D/YY)"""
        if not date_str or date_str == 'nan':
            return None
            
        date_str = str(date_str).strip()
        
        # Wells Fargo uses M/D/YYYY or M/D/YY format
        formats = [
            '%m/%d/%Y',
            '%m/%d/%y',
            '%-m/%-d/%Y',  # Handle single digit months/days
            '%-m/%-d/%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        return None
    
    def _parse_amount(self, amount_str):
        """Parse amount from string"""
        if not amount_str or amount_str == 'nan':
            return None
            
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and commas
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        
        # Wells Fargo uses negative sign for debits
        try:
            return float(amount_str)
        except ValueError:
            return None
    
    def _is_amount(self, text):
        """Check if text looks like an amount"""
        text = str(text).strip()
        # Remove currency symbols and commas
        text = text.replace('$', '').replace(',', '')
        # Check if it's a number
        try:
            float(text)
            return True
        except ValueError:
            return False
    
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
        pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf"
    
    parser = WellsFargoParser()
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