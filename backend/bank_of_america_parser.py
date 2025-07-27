#!/usr/bin/env python3
"""
Bank of America PDF Parser
Handles Bank of America business and personal account statements
"""

import re
import pandas as pd
from datetime import datetime
import tabula
import pdfplumber


class BankOfAmericaParser:
    def __init__(self):
        self.bank_name = "Bank of America"
        
    def extract_transactions(self, pdf_path):
        """Extract transactions from Bank of America PDF"""
        all_transactions = []
        
        try:
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
            print(f"Error parsing Bank of America PDF: {e}")
            
        return all_transactions
    
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
                # Bank of America typically has Date, Description, Amount columns
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
        # Convert column names to string and lowercase
        columns_lower = [str(col).lower() for col in df.columns]
        
        # Check for date-like columns
        has_date = any('date' in col or 
                      re.match(r'^\d{1,2}/\d{1,2}', str(col)) 
                      for col in df.columns)
        
        # Check for amount-like columns
        has_amount = any('amount' in col or 'balance' in col 
                        for col in columns_lower)
        
        # Check if first column contains dates
        if len(df) > 0:
            first_col_vals = df.iloc[:, 0].astype(str)
            date_pattern = r'^\d{1,2}/\d{1,2}/\d{2,4}'
            has_date_values = any(re.match(date_pattern, val) for val in first_col_vals[:5])
            
            return has_date or has_amount or has_date_values
        
        return False
    
    def _parse_transaction_table(self, df):
        """Parse a transaction table from Bank of America"""
        transactions = []
        
        # Identify columns
        date_col = None
        desc_col = None
        amount_col = None
        
        # Find date column
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if 'date' in col_str or re.match(r'^\d{1,2}/\d{1,2}', str(col)):
                date_col = i
                break
        
        # If no explicit date column, check first column
        if date_col is None and len(df.columns) > 0:
            # Check if first column contains dates
            first_vals = df.iloc[:5, 0].astype(str)
            if any(re.match(r'^\d{1,2}/\d{1,2}', val) for val in first_vals):
                date_col = 0
        
        # Find description column (usually after date)
        if date_col is not None and len(df.columns) > date_col + 1:
            desc_col = date_col + 1
        
        # Find amount column (usually last or contains $)
        for i in range(len(df.columns) - 1, -1, -1):
            col_vals = df.iloc[:, i].astype(str)
            if any('$' in val or re.match(r'^-?\d+\.?\d*$', val.replace(',', '')) 
                   for val in col_vals[:5] if pd.notna(val)):
                amount_col = i
                break
        
        # Parse rows
        for _, row in df.iterrows():
            try:
                transaction = {}
                
                # Get date
                if date_col is not None:
                    date_str = str(row.iloc[date_col])
                    date = self._parse_date(date_str)
                    if date:
                        transaction['date'] = date
                        transaction['date_string'] = date_str
                
                # Get description
                if desc_col is not None:
                    desc = str(row.iloc[desc_col])
                    if desc and desc != 'nan':
                        # Clean up description
                        desc = desc.strip()
                        # For BoA, sometimes description continues in amount column
                        if amount_col != desc_col + 1 and amount_col is not None:
                            next_col = row.iloc[desc_col + 1]
                            if pd.notna(next_col) and not self._is_amount(str(next_col)):
                                desc += " " + str(next_col)
                        transaction['description'] = desc
                
                # Get amount
                if amount_col is not None:
                    amount_str = str(row.iloc[amount_col])
                    amount = self._parse_amount(amount_str)
                    if amount is not None:
                        transaction['amount'] = amount
                        transaction['amount_string'] = amount_str
                
                # Only add if we have at least date and amount
                if 'date' in transaction and 'amount' in transaction:
                    transactions.append(transaction)
                    
            except Exception as e:
                continue
                
        return transactions
    
    def _parse_text_transactions(self, text):
        """Parse transactions from text using regex"""
        transactions = []
        
        # Bank of America transaction patterns
        # Format: MM/DD/YY Description Amount
        patterns = [
            # Standard format with date at start
            r'(\d{2}/\d{2}/\d{2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})\s*$',
            # With reference numbers
            r'(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})\s*$',
            # Zelle transfers
            r'(\d{2}/\d{2}/\d{2})\s+(Zelle Transfer.+?)\s+([\d,]+\.\d{2})',
            # Check card transactions
            r'(\d{2}/\d{2}/\d{2})\s+(CHECKCARD.+?)\s+([-]?\d+\.\d{2})',
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        date = self._parse_date(date_str)
                        
                        if len(match.groups()) == 4:  # Has reference date
                            desc = match.group(3)
                            amount_str = match.group(4)
                        else:
                            desc = match.group(2)
                            amount_str = match.group(3)
                        
                        amount = self._parse_amount(amount_str)
                        
                        if date and amount is not None:
                            transactions.append({
                                'date': date,
                                'date_string': date_str,
                                'description': desc.strip(),
                                'amount': amount,
                                'amount_string': amount_str
                            })
                            break
                            
                    except Exception as e:
                        continue
                        
        return transactions
    
    def _parse_date(self, date_str):
        """Parse Bank of America date format (MM/DD/YY)"""
        if not date_str or date_str == 'nan':
            return None
            
        date_str = str(date_str).strip()
        
        # Bank of America uses MM/DD/YY format
        formats = [
            '%m/%d/%y',
            '%m/%d/%Y',
            '%m-%d-%y',
            '%m-%d-%Y'
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
        
        # Handle negative amounts
        is_negative = False
        if amount_str.startswith('-'):
            is_negative = True
            amount_str = amount_str[1:]
        elif amount_str.startswith('(') and amount_str.endswith(')'):
            is_negative = True
            amount_str = amount_str[1:-1]
        
        try:
            amount = float(amount_str)
            return -amount if is_negative else amount
        except ValueError:
            return None
    
    def _is_amount(self, text):
        """Check if text looks like an amount"""
        text = str(text).strip()
        # Remove currency symbols
        text = text.replace('$', '').replace(',', '')
        # Check if it's a number
        try:
            float(text.replace('-', '').replace('(', '').replace(')', ''))
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
        parser = BankOfAmericaParser()
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