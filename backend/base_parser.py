"""Base parser class with common functionality for all bank parsers"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pdfplumber
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseBankParser(ABC):
    """Base class for all bank-specific parsers"""
    
    def __init__(self):
        self.bank_name = "Unknown Bank"
        self.supported_date_formats = []
        self.currency_symbols = ['$', '€', '£', '¥', '₹', 'USD', 'EUR', 'GBP']
        
    def parse(self, pdf_path: str) -> List[Dict]:
        """Main parsing method - to be implemented by subclasses"""
        try:
            logger.info(f"Parsing {self.bank_name} statement: {pdf_path}")
            transactions = self.extract_transactions(pdf_path)
            
            # Clean and validate transactions
            valid_transactions = self.validate_transactions(transactions)
            
            # Remove duplicates
            unique_transactions = self.remove_duplicates(valid_transactions)
            
            # Sort by date
            sorted_transactions = sorted(
                unique_transactions, 
                key=lambda x: x.get('date') or datetime.min
            )
            
            logger.info(f"Successfully parsed {len(sorted_transactions)} transactions from {self.bank_name}")
            return sorted_transactions
            
        except Exception as e:
            logger.error(f"Error parsing {self.bank_name} statement: {e}")
            return []
    
    @abstractmethod
    def extract_transactions(self, pdf_path: str) -> List[Dict]:
        """Extract raw transactions from PDF - must be implemented by subclasses"""
        pass
    
    def parse_date(self, date_str: str, year: Optional[int] = None) -> Optional[datetime]:
        """Parse date string using configured formats"""
        if not date_str or not date_str.strip():
            return None
            
        # Clean the date string
        date_str = date_str.strip()
        
        # Try each supported format
        for date_format in self.supported_date_formats:
            try:
                if '%Y' not in date_format and '%y' not in date_format and year:
                    # Format doesn't include year, add it
                    parsed_date = datetime.strptime(date_str, date_format)
                    # Replace the year with the detected year
                    parsed_date = parsed_date.replace(year=year)
                else:
                    parsed_date = datetime.strptime(date_str, date_format)
                
                # Validate the date is reasonable (not in future, not too old)
                if parsed_date <= datetime.now() and parsed_date.year >= 1900:
                    return parsed_date
                    
            except ValueError:
                continue
        
        # If no format matched, try some common variations
        if year:
            # Try adding year to common formats
            common_patterns = [
                (r'^(\d{1,2})/(\d{1,2})$', lambda m: f"{m.group(1)}/{m.group(2)}/{year}"),
                (r'^(\d{1,2})-(\d{1,2})$', lambda m: f"{m.group(1)}-{m.group(2)}-{year}"),
                (r'^(\d{1,2})\s+([A-Za-z]{3})$', lambda m: f"{m.group(1)} {m.group(2)} {year}"),
            ]
            
            for pattern, formatter in common_patterns:
                import re
                match = re.match(pattern, date_str)
                if match:
                    try:
                        formatted_date = formatter(match)
                        # Try common formats with year
                        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y', '%d %b %Y']:
                            try:
                                return datetime.strptime(formatted_date, fmt)
                            except:
                                continue
                    except:
                        continue
        
        return None
    
    def extract_amount(self, amount_str: str) -> Optional[float]:
        """Extract numeric amount from string"""
        if not amount_str or not isinstance(amount_str, str):
            return None
            
        try:
            # Clean the string
            cleaned = amount_str.strip()
            
            # Remove currency symbols
            for symbol in self.currency_symbols:
                cleaned = cleaned.replace(symbol, '')
            
            # Remove commas and spaces
            cleaned = cleaned.replace(',', '').replace(' ', '')
            
            # Handle parentheses for negative amounts
            is_negative = False
            if '(' in cleaned and ')' in cleaned:
                is_negative = True
                cleaned = re.sub(r'[()]', '', cleaned)
            elif cleaned.startswith('-'):
                is_negative = True
                cleaned = cleaned[1:]
            
            # Handle CR/DR indicators
            if cleaned.upper().endswith('CR'):
                cleaned = cleaned[:-2].strip()
            elif cleaned.upper().endswith('DR'):
                is_negative = True
                cleaned = cleaned[:-2].strip()
            
            # Convert to float
            amount = float(cleaned)
            
            # Apply negative sign if needed
            if is_negative:
                amount = -amount
            
            # Validate amount is reasonable
            if self.is_valid_amount(amount):
                return amount
                
        except (ValueError, AttributeError):
            pass
            
        return None
    
    def is_valid_amount(self, amount: float) -> bool:
        """Check if amount is within reasonable range"""
        return -1000000 <= amount <= 1000000
    
    def is_valid_date(self, date_str: str) -> bool:
        """Check if string could be a valid date"""
        if not date_str:
            return False
            
        # Reject phone numbers
        phone_patterns = [
            r'^1-\d{2,3}$',
            r'^\d{3}-\d{3}-\d{4}$',
            r'^\d{10,11}$',
            r'^1-\d{3}-\d{3}-\d{4}$'
        ]
        
        for pattern in phone_patterns:
            if re.match(pattern, date_str):
                return False
                
        return True
    
    def clean_description(self, desc: str) -> str:
        """Clean transaction description"""
        if not desc:
            return ""
            
        # Remove excessive whitespace
        desc = ' '.join(desc.split())
        
        # Remove common noise
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^[-\s]+$',  # Just dashes or spaces
            r'^[^\w\s]+$'  # Just symbols
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, desc):
                return ""
                
        return desc.strip()
    
    def validate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Validate and clean transactions"""
        valid_transactions = []
        
        for trans in transactions:
            # Check if we have date_string but no date object
            if not trans.get('date') and trans.get('date_string'):
                # Try to parse the date_string
                date_obj = self.parse_date(trans['date_string'], self.detect_year_from_pdf(None))
                if date_obj:
                    trans['date'] = date_obj
            
            # Must have date
            if not trans.get('date'):
                continue
                
            # Must have amount
            if trans.get('amount') is None:
                continue
                
            # Must have description
            desc = self.clean_description(trans.get('description', ''))
            if not desc or len(desc) < 2:
                continue
                
            # Create clean transaction - preserve the correct date format
            date_format = '%m/%d/%Y'  # Default US format
            if hasattr(self, 'bank_name'):
                if self.bank_name in ['ANZ Bank', 'Commonwealth Bank', 'Westpac']:
                    date_format = '%d/%m/%Y'
                elif self.bank_name in ['Lloyds Bank', 'Metro Bank', 'Nationwide']:
                    date_format = '%d/%m/%Y'
            
            valid_trans = {
                'date': trans['date'],
                'date_string': trans.get('date_string', trans['date'].strftime(date_format)),
                'description': desc,
                'amount': trans['amount'],
                'amount_string': f"{abs(trans['amount']):.2f}"
            }
            
            valid_transactions.append(valid_trans)
            
        return valid_transactions
    
    def remove_duplicates(self, transactions: List[Dict]) -> List[Dict]:
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for trans in transactions:
            # Create unique key
            key = (
                trans['date'].strftime('%Y-%m-%d'),
                round(trans['amount'], 2),
                trans['description'][:50]  # First 50 chars of description
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(trans)
                
        return unique
    
    def detect_year_from_pdf(self, pdf_path: str) -> Optional[int]:
        """Try to detect statement year from PDF content"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first few pages
                text = ""
                for i in range(min(3, len(pdf.pages))):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # Look for year patterns
                year_patterns = [
                    r'Statement Period:.*?(\d{4})',
                    r'Statement Date:.*?(\d{4})',
                    r'(\d{1,2}/\d{1,2}/(\d{4}))',
                    r'(\d{4})-\d{2}-\d{2}',
                    r'For the period.*?(\d{4})',
                    r'Statement.*?(\d{4})',
                    r'(\b20\d{2}\b)',  # Any 4-digit year starting with 20
                    r'(\b19\d{2}\b)'   # Any 4-digit year starting with 19
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        for match in matches:
                            year_str = match if isinstance(match, str) else match[-1]
                            try:
                                year = int(year_str)
                                if 1990 <= year <= 2030:
                                    return year
                            except:
                                continue
                                
        except Exception as e:
            logger.warning(f"Could not detect year from PDF: {e}")
            
        # Default to current year
        return datetime.now().year
    
    def extract_table_data(self, pdf_path: str) -> List[List[str]]:
        """Extract all tables from PDF"""
        all_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Filter out empty rows
                            cleaned_table = [
                                row for row in table 
                                if row and any(cell and str(cell).strip() for cell in row)
                            ]
                            if cleaned_table:
                                all_tables.extend(cleaned_table)
                                
        except Exception as e:
            logger.warning(f"Error extracting tables: {e}")
            
        return all_tables
    
    def extract_text_lines(self, pdf_path: str) -> List[str]:
        """Extract all text lines from PDF"""
        all_lines = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        all_lines.extend([line.strip() for line in lines if line.strip()])
                        
        except Exception as e:
            logger.warning(f"Error extracting text: {e}")
            
        return all_lines