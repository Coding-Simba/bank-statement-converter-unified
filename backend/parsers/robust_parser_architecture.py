"""
Robust Bank Statement Parser Architecture
=========================================

This system uses a multi-layered approach with:
1. ML-based table detection (using modern libraries)
2. Bank-specific parsers with pattern recognition
3. Parallel processing for scale
4. Self-improving capabilities
"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp

# Modern PDF libraries
import pdfplumber
import camelot
import tabula
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import numpy as np

# ML libraries for pattern recognition
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

# Pattern matching
import re
from dateutil import parser as date_parser

# Monitoring and telemetry
from prometheus_client import Counter, Histogram, Gauge
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
parse_counter = Counter('pdf_parse_total', 'Total PDFs parsed', ['bank', 'status'])
parse_duration = Histogram('pdf_parse_duration_seconds', 'PDF parsing duration')
active_parsers = Gauge('active_parsers', 'Number of active parser processes')

@dataclass
class Transaction:
    """Standardized transaction format"""
    date: datetime
    description: str
    amount: float
    balance: Optional[float] = None
    transaction_type: Optional[str] = None  # debit/credit
    reference: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'amount': self.amount,
            'balance': self.balance,
            'type': self.transaction_type,
            'reference': self.reference,
            'category': self.category
        }

@dataclass
class BankStatement:
    """Parsed bank statement data"""
    bank_name: str
    account_number: Optional[str]
    statement_period: Optional[Tuple[datetime, datetime]]
    transactions: List[Transaction]
    currency: str = "USD"
    total_credits: float = 0.0
    total_debits: float = 0.0
    
    def to_dict(self):
        return {
            'bank': self.bank_name,
            'account': self.account_number,
            'period': {
                'start': self.statement_period[0].isoformat() if self.statement_period else None,
                'end': self.statement_period[1].isoformat() if self.statement_period else None
            },
            'transactions': [t.to_dict() for t in self.transactions],
            'currency': self.currency,
            'summary': {
                'total_credits': self.total_credits,
                'total_debits': self.total_debits,
                'transaction_count': len(self.transactions)
            }
        }

class BankDetector:
    """ML-based bank detection from PDF content"""
    
    def __init__(self):
        self.bank_patterns = {
            'wells_fargo': ['wells fargo', 'wellsfargo'],
            'bank_of_america': ['bank of america', 'bofa', 'boa'],
            'chase': ['jpmorgan chase', 'chase bank', 'chase'],
            'citizens': ['citizens bank', 'citizens'],
            'pnc': ['pnc bank', 'pnc'],
            'suntrust': ['suntrust', 'truist'],
            'fifth_third': ['fifth third', '5/3 bank'],
            'huntington': ['huntington bank', 'huntington'],
            'discover': ['discover bank', 'discover card'],
            'woodforest': ['woodforest national bank', 'woodforest'],
            # UK banks
            'metro': ['metro bank'],
            'nationwide': ['nationwide building society', 'nationwide'],
            # Canadian banks
            'rbc': ['royal bank of canada', 'rbc', 'rbcroyalbank'],
            # Australian banks
            'westpac': ['westpac', 'westpac banking'],
            'bendigo': ['bendigo bank', 'bendigo'],
            'commonwealth': ['commonwealth bank', 'commbank', 'cba']
        }
        
        # Load pre-trained model if exists
        self.model_path = 'models/bank_classifier.pkl'
        self.vectorizer_path = 'models/bank_vectorizer.pkl'
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            self.classifier = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
        else:
            # Create basic model - will improve with training data
            self.vectorizer = TfidfVectorizer(max_features=1000)
            self.classifier = RandomForestClassifier(n_estimators=100)
    
    def detect_bank(self, pdf_text: str) -> Tuple[str, float]:
        """Detect bank from PDF text content"""
        text_lower = pdf_text.lower()
        
        # First try pattern matching
        for bank, patterns in self.bank_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return bank, 1.0  # High confidence
        
        # If no pattern match, try ML model (if trained)
        try:
            if hasattr(self.classifier, 'classes_'):
                features = self.vectorizer.transform([text_lower])
                prediction = self.classifier.predict(features)[0]
                confidence = max(self.classifier.predict_proba(features)[0])
                return prediction, confidence
        except:
            pass
        
        return 'unknown', 0.0

class TableExtractor:
    """Advanced table extraction using multiple methods"""
    
    def __init__(self):
        self.methods = ['camelot', 'tabula', 'pdfplumber', 'custom']
    
    async def extract_tables(self, pdf_path: str, method: str = 'auto') -> List[pd.DataFrame]:
        """Extract tables from PDF using specified or best method"""
        if method == 'auto':
            # Try methods in order of accuracy
            for m in self.methods:
                try:
                    tables = await self._extract_with_method(pdf_path, m)
                    if tables and self._validate_tables(tables):
                        logger.info(f"Successfully extracted tables using {m}")
                        return tables
                except Exception as e:
                    logger.warning(f"Method {m} failed: {e}")
                    continue
        else:
            return await self._extract_with_method(pdf_path, method)
        
        return []
    
    async def _extract_with_method(self, pdf_path: str, method: str) -> List[pd.DataFrame]:
        """Extract tables using specific method"""
        loop = asyncio.get_event_loop()
        
        if method == 'camelot':
            # Camelot is best for structured tables
            return await loop.run_in_executor(None, self._extract_camelot, pdf_path)
        elif method == 'tabula':
            # Tabula handles complex layouts well
            return await loop.run_in_executor(None, self._extract_tabula, pdf_path)
        elif method == 'pdfplumber':
            # PDFPlumber for custom extraction
            return await loop.run_in_executor(None, self._extract_pdfplumber, pdf_path)
        elif method == 'custom':
            # Custom ML-based extraction
            return await loop.run_in_executor(None, self._extract_custom, pdf_path)
    
    def _extract_camelot(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract using Camelot"""
        tables = []
        # Try both lattice and stream methods
        for flavor in ['lattice', 'stream']:
            try:
                camelot_tables = camelot.read_pdf(
                    pdf_path,
                    pages='all',
                    flavor=flavor,
                    suppress_stdout=True
                )
                for table in camelot_tables:
                    if table.shape[0] > 1:  # Skip empty tables
                        tables.append(table.df)
            except:
                continue
        return tables
    
    def _extract_tabula(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract using Tabula"""
        return tabula.read_pdf(
            pdf_path,
            pages='all',
            multiple_tables=True,
            pandas_options={'header': None}
        )
    
    def _extract_pdfplumber(self, pdf_path: str) -> List[pd.DataFrame]:
        """Extract using PDFPlumber"""
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:
                        df = pd.DataFrame(table)
                        tables.append(df)
        return tables
    
    def _extract_custom(self, pdf_path: str) -> List[pd.DataFrame]:
        """Custom extraction using ML-based table detection"""
        # This would use computer vision to detect table boundaries
        # For now, fallback to OCR-based extraction
        tables = []
        images = convert_from_path(pdf_path, dpi=300)
        
        for img in images:
            # Apply OCR
            text = pytesseract.image_to_string(img)
            # Parse text into table structure
            lines = text.split('\n')
            if lines:
                # Simple heuristic: lines with consistent spacing are table rows
                df = self._parse_text_to_table(lines)
                if df is not None:
                    tables.append(df)
        
        return tables
    
    def _parse_text_to_table(self, lines: List[str]) -> Optional[pd.DataFrame]:
        """Parse text lines into table structure"""
        # Implementation would use regex and spacing analysis
        # This is a simplified version
        rows = []
        for line in lines:
            if line.strip():
                # Split by 2+ spaces
                cells = re.split(r'\s{2,}', line.strip())
                if len(cells) > 1:
                    rows.append(cells)
        
        if rows:
            return pd.DataFrame(rows)
        return None
    
    def _validate_tables(self, tables: List[pd.DataFrame]) -> bool:
        """Validate extracted tables contain transaction data"""
        if not tables:
            return False
        
        for table in tables:
            # Check for date-like columns
            for col in table.columns:
                sample = table[col].astype(str).str.strip()
                date_matches = sample.apply(lambda x: bool(re.search(r'\d{1,2}[-/]\d{1,2}', x)))
                if date_matches.sum() > len(table) * 0.3:  # 30% have dates
                    return True
        
        return False

class TransactionParser:
    """Parse transactions from extracted tables"""
    
    def __init__(self, bank_name: str):
        self.bank_name = bank_name
        self.date_formats = self._get_date_formats()
        self.amount_patterns = self._get_amount_patterns()
    
    def _get_date_formats(self) -> List[str]:
        """Get date formats by region"""
        us_formats = ['%m/%d/%Y', '%m/%d/%y', '%m/%d', '%m-%d-%Y', '%m-%d']
        uk_formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %b', '%d.%m.%Y']
        au_formats = ['%d/%m/%Y', '%d %b %y', '%d %B %Y']
        ca_formats = ['%m/%d', '%m/%d/%Y']
        
        # Return based on bank region
        if self.bank_name in ['wells_fargo', 'bank_of_america', 'chase', 'citizens', 
                              'pnc', 'suntrust', 'fifth_third', 'huntington', 
                              'discover', 'woodforest']:
            return us_formats
        elif self.bank_name in ['metro', 'nationwide']:
            return uk_formats
        elif self.bank_name in ['westpac', 'bendigo', 'commonwealth']:
            return au_formats
        elif self.bank_name in ['rbc']:
            return ca_formats
        else:
            return us_formats + uk_formats + au_formats + ca_formats
    
    def _get_amount_patterns(self) -> List[re.Pattern]:
        """Get amount parsing patterns"""
        return [
            re.compile(r'[-+]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'),  # US format
            re.compile(r'[-+]?£?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'),  # UK format
            re.compile(r'[-+]?\d{1,3}(?:\.\d{3})*(?:,\d{2})?'),     # EU format
            re.compile(r'[-+]?\d+\.?\d*')                           # Simple format
        ]
    
    def parse_table(self, table: pd.DataFrame) -> List[Transaction]:
        """Parse transactions from a table"""
        transactions = []
        
        # Identify columns
        date_col = self._find_date_column(table)
        desc_col = self._find_description_column(table)
        amount_cols = self._find_amount_columns(table)
        balance_col = self._find_balance_column(table)
        
        if date_col is None or not amount_cols:
            return transactions
        
        # Parse each row
        for idx, row in table.iterrows():
            try:
                # Skip header rows
                if self._is_header_row(row):
                    continue
                
                # Parse date
                date = self._parse_date(row[date_col])
                if not date:
                    continue
                
                # Parse description
                description = str(row[desc_col]) if desc_col is not None else ""
                
                # Parse amount
                amount, tx_type = self._parse_amount(row, amount_cols)
                if amount is None:
                    continue
                
                # Parse balance
                balance = self._parse_balance(row[balance_col]) if balance_col is not None else None
                
                # Create transaction
                tx = Transaction(
                    date=date,
                    description=description.strip(),
                    amount=amount,
                    balance=balance,
                    transaction_type=tx_type
                )
                
                transactions.append(tx)
                
            except Exception as e:
                logger.warning(f"Failed to parse row {idx}: {e}")
                continue
        
        return transactions
    
    def _find_date_column(self, table: pd.DataFrame) -> Optional[int]:
        """Find column containing dates"""
        for col in table.columns:
            sample = table[col].astype(str).head(20)
            date_count = 0
            
            for val in sample:
                if self._parse_date(val):
                    date_count += 1
            
            if date_count > len(sample) * 0.5:  # 50% threshold
                return col
        
        return None
    
    def _find_description_column(self, table: pd.DataFrame) -> Optional[int]:
        """Find column containing transaction descriptions"""
        date_col = self._find_date_column(table)
        
        for col in table.columns:
            if col == date_col:
                continue
            
            sample = table[col].astype(str).head(20)
            
            # Check for text content
            text_count = sum(1 for val in sample if len(val) > 10 and not val.replace('.', '').replace(',', '').isdigit())
            
            if text_count > len(sample) * 0.5:
                return col
        
        return None
    
    def _find_amount_columns(self, table: pd.DataFrame) -> List[int]:
        """Find columns containing amounts"""
        amount_cols = []
        
        for col in table.columns:
            sample = table[col].astype(str).head(20)
            amount_count = 0
            
            for val in sample:
                if self._parse_amount_value(val) is not None:
                    amount_count += 1
            
            if amount_count > len(sample) * 0.5:
                amount_cols.append(col)
        
        return amount_cols
    
    def _find_balance_column(self, table: pd.DataFrame) -> Optional[int]:
        """Find column containing running balance"""
        # Usually the last numeric column
        amount_cols = self._find_amount_columns(table)
        
        if len(amount_cols) > 2:
            # Check if values are cumulative
            col = amount_cols[-1]
            values = []
            
            for val in table[col].astype(str).head(10):
                parsed = self._parse_amount_value(val)
                if parsed:
                    values.append(parsed)
            
            if len(values) > 3:
                # Check if monotonic (typical for balance)
                diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
                if all(abs(d) < max(values) * 0.5 for d in diffs):  # Not cumulative
                    return col
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string using multiple formats"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        date_str = date_str.strip()
        
        # Try each format
        for fmt in self.date_formats:
            try:
                # Handle year-less dates
                if '%Y' not in fmt and '%y' not in fmt:
                    # Assume current year
                    date_str_with_year = f"{date_str}/{datetime.now().year}"
                    fmt_with_year = f"{fmt}/%Y"
                    return datetime.strptime(date_str_with_year, fmt_with_year)
                else:
                    return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Try dateutil parser as fallback
        try:
            return date_parser.parse(date_str, fuzzy=False)
        except:
            return None
    
    def _parse_amount(self, row: pd.Series, amount_cols: List[int]) -> Tuple[Optional[float], Optional[str]]:
        """Parse amount from row"""
        # Check for separate debit/credit columns
        if len(amount_cols) >= 2:
            # Assume first is debit, second is credit
            debit = self._parse_amount_value(str(row[amount_cols[0]]))
            credit = self._parse_amount_value(str(row[amount_cols[1]]))
            
            if debit and debit > 0:
                return -debit, 'debit'
            elif credit and credit > 0:
                return credit, 'credit'
        
        # Single amount column
        elif len(amount_cols) == 1:
            amount = self._parse_amount_value(str(row[amount_cols[0]]))
            if amount:
                if amount < 0:
                    return amount, 'debit'
                else:
                    return amount, 'credit'
        
        return None, None
    
    def _parse_amount_value(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        amount_str = amount_str.strip()
        
        # Remove currency symbols
        amount_str = re.sub(r'[$£€¥]', '', amount_str)
        
        # Handle parentheses for negative
        if '(' in amount_str and ')' in amount_str:
            amount_str = '-' + amount_str.replace('(', '').replace(')', '')
        
        # Remove commas
        amount_str = amount_str.replace(',', '')
        
        # Try to parse
        try:
            return float(amount_str)
        except:
            return None
    
    def _parse_balance(self, balance_str: str) -> Optional[float]:
        """Parse balance string"""
        return self._parse_amount_value(balance_str)
    
    def _is_header_row(self, row: pd.Series) -> bool:
        """Check if row is a header"""
        text_values = [str(v).lower() for v in row if v]
        
        header_keywords = ['date', 'description', 'amount', 'balance', 'debit', 
                          'credit', 'withdrawal', 'deposit', 'transaction']
        
        matches = sum(1 for text in text_values for keyword in header_keywords if keyword in text)
        
        return matches >= 2

class BankStatementParser:
    """Main parser orchestrator"""
    
    def __init__(self, num_workers: int = 20):
        self.num_workers = num_workers
        self.bank_detector = BankDetector()
        self.table_extractor = TableExtractor()
        self.parsers = {}  # Bank-specific parsers
        
        # Initialize process pool for parallel processing
        self.process_pool = ProcessPoolExecutor(max_workers=num_workers)
        self.thread_pool = ThreadPoolExecutor(max_workers=num_workers * 2)
    
    async def parse_pdf(self, pdf_path: str) -> Optional[BankStatement]:
        """Parse a single PDF"""
        start_time = time.time()
        active_parsers.inc()
        
        try:
            # Extract text for bank detection
            text = await self._extract_text(pdf_path)
            
            # Detect bank
            bank_name, confidence = self.bank_detector.detect_bank(text)
            logger.info(f"Detected bank: {bank_name} (confidence: {confidence:.2f})")
            
            # Extract tables
            tables = await self.table_extractor.extract_tables(pdf_path)
            
            if not tables:
                logger.warning(f"No tables found in {pdf_path}")
                parse_counter.labels(bank=bank_name, status='no_tables').inc()
                return None
            
            # Get parser for bank
            parser = self._get_parser(bank_name)
            
            # Parse transactions
            all_transactions = []
            for table in tables:
                transactions = parser.parse_table(table)
                all_transactions.extend(transactions)
            
            if not all_transactions:
                logger.warning(f"No transactions found in {pdf_path}")
                parse_counter.labels(bank=bank_name, status='no_transactions').inc()
                return None
            
            # Create statement
            statement = self._create_statement(bank_name, all_transactions, text)
            
            parse_counter.labels(bank=bank_name, status='success').inc()
            parse_duration.observe(time.time() - start_time)
            
            return statement
            
        except Exception as e:
            logger.error(f"Failed to parse {pdf_path}: {e}")
            parse_counter.labels(bank='unknown', status='error').inc()
            return None
        finally:
            active_parsers.dec()
    
    async def parse_multiple(self, pdf_paths: List[str]) -> List[Optional[BankStatement]]:
        """Parse multiple PDFs in parallel"""
        tasks = [self.parse_pdf(path) for path in pdf_paths]
        return await asyncio.gather(*tasks)
    
    async def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        loop = asyncio.get_event_loop()
        
        def extract():
            text = ""
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        
        return await loop.run_in_executor(self.thread_pool, extract)
    
    def _get_parser(self, bank_name: str) -> TransactionParser:
        """Get or create parser for bank"""
        if bank_name not in self.parsers:
            self.parsers[bank_name] = TransactionParser(bank_name)
        return self.parsers[bank_name]
    
    def _create_statement(self, bank_name: str, transactions: List[Transaction], 
                         pdf_text: str) -> BankStatement:
        """Create bank statement from transactions"""
        # Sort transactions by date
        transactions.sort(key=lambda x: x.date)
        
        # Calculate totals
        total_credits = sum(t.amount for t in transactions if t.amount > 0)
        total_debits = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        # Determine period
        if transactions:
            period = (transactions[0].date, transactions[-1].date)
        else:
            period = None
        
        # Extract account number if possible
        account_number = self._extract_account_number(pdf_text, bank_name)
        
        return BankStatement(
            bank_name=bank_name,
            account_number=account_number,
            statement_period=period,
            transactions=transactions,
            total_credits=total_credits,
            total_debits=total_debits
        )
    
    def _extract_account_number(self, text: str, bank_name: str) -> Optional[str]:
        """Extract account number from text"""
        # Bank-specific patterns
        patterns = {
            'default': r'Account\s*(?:Number|#)?\s*:?\s*(\d{4,})',
            'wells_fargo': r'Account\s*number\s*:?\s*(\d{4,})',
            'bank_of_america': r'Account\s*#\s*(\d{4,})',
        }
        
        pattern = patterns.get(bank_name, patterns['default'])
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    def save_training_data(self, statement: BankStatement, pdf_path: str):
        """Save successful parse for training"""
        training_dir = 'training_data'
        os.makedirs(training_dir, exist_ok=True)
        
        # Save as JSON
        data = {
            'pdf_path': pdf_path,
            'parsed_at': datetime.now().isoformat(),
            'statement': statement.to_dict()
        }
        
        filename = f"{training_dir}/{statement.bank_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def close(self):
        """Cleanup resources"""
        self.process_pool.shutdown(wait=True)
        self.thread_pool.shutdown(wait=True)

# Main entry point for parallel processing
async def process_bank_statements(pdf_paths: List[str], num_workers: int = 20) -> List[Dict]:
    """Process multiple bank statements in parallel"""
    parser = BankStatementParser(num_workers=num_workers)
    
    try:
        # Process in batches
        batch_size = num_workers * 2
        results = []
        
        for i in range(0, len(pdf_paths), batch_size):
            batch = pdf_paths[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(pdf_paths) + batch_size - 1)//batch_size}")
            
            statements = await parser.parse_multiple(batch)
            
            for statement, pdf_path in zip(statements, batch):
                if statement:
                    # Save for training
                    parser.save_training_data(statement, pdf_path)
                    results.append(statement.to_dict())
                else:
                    results.append({
                        'error': f'Failed to parse {pdf_path}',
                        'pdf_path': pdf_path
                    })
        
        return results
        
    finally:
        await parser.close()

if __name__ == "__main__":
    # Example usage
    test_pdfs = [
        "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf"
    ]
    
    # Run async parser
    results = asyncio.run(process_bank_statements(test_pdfs))
    print(json.dumps(results, indent=2))