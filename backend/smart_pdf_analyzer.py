#!/usr/bin/env python3
"""
Smart PDF Analyzer - Chooses the best extraction method based on PDF characteristics
"""
import pdfplumber
import PyPDF2
import camelot
import tabula
from typing import List, Dict, Tuple
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SmartPDFAnalyzer:
    """Analyzes PDF and chooses the best extraction method"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_info = self._analyze_pdf_structure()
    
    def _analyze_pdf_structure(self) -> Dict:
        """Analyze PDF to determine its characteristics"""
        info = {
            'has_tables': False,
            'has_forms': False,
            'is_scanned': False,
            'has_columns': False,
            'text_density': 0,
            'page_count': 0,
            'has_images': False,
            'layout_complexity': 'simple'  # simple, moderate, complex
        }
        
        try:
            # Analyze with pdfplumber for detailed structure
            with pdfplumber.open(self.pdf_path) as pdf:
                info['page_count'] = len(pdf.pages)
                
                total_chars = 0
                total_tables = 0
                total_images = 0
                
                for page in pdf.pages[:3]:  # Check first 3 pages
                    # Check for tables
                    tables = page.extract_tables()
                    if tables:
                        total_tables += len(tables)
                        info['has_tables'] = True
                    
                    # Check text density
                    text = page.extract_text()
                    if text:
                        total_chars += len(text)
                    
                    # Check for columns (words at similar x positions)
                    words = page.extract_words()
                    if words:
                        x_positions = [w['x0'] for w in words]
                        unique_x = len(set(round(x, -1) for x in x_positions))  # Round to nearest 10
                        if unique_x > 5 and unique_x < 20:  # Likely columnar
                            info['has_columns'] = True
                    
                    # Check for images
                    if hasattr(page, 'images') and page.images:
                        total_images += len(page.images)
                        info['has_images'] = True
                
                # Calculate text density
                info['text_density'] = total_chars / max(info['page_count'], 1)
                
                # Determine if scanned (low text density with images)
                if info['text_density'] < 100 and info['has_images']:
                    info['is_scanned'] = True
                
                # Determine layout complexity
                if total_tables > 2 or info['has_columns']:
                    info['layout_complexity'] = 'complex'
                elif total_tables > 0 or info['text_density'] > 1000:
                    info['layout_complexity'] = 'moderate'
                    
        except Exception as e:
            logger.error(f"Error analyzing PDF structure: {e}")
        
        return info
    
    def choose_best_parser(self) -> str:
        """Choose the best parser based on PDF characteristics"""
        
        # Priority rules based on PDF characteristics
        if self.pdf_info['is_scanned']:
            return 'ocr'  # Need OCR for scanned documents
        
        if self.pdf_info['has_tables'] and self.pdf_info['layout_complexity'] == 'complex':
            return 'camelot'  # Best for complex tables
        
        if self.pdf_info['has_tables']:
            return 'tabula'  # Good for simple tables
        
        if self.pdf_info['has_columns'] or self.pdf_info['layout_complexity'] == 'complex':
            return 'pdfplumber'  # Best for layout preservation
        
        if self.pdf_info['text_density'] < 500:
            return 'pymupdf'  # Better for sparse text
        
        # Default to pdfplumber for general use
        return 'pdfplumber'
    
    def extract_transactions(self) -> List[Dict]:
        """Extract transactions using the best method"""
        parser_name = self.choose_best_parser()
        print(f"PDF Analysis: {self.pdf_info}")
        print(f"Chosen parser: {parser_name}")
        
        if parser_name == 'camelot':
            return self._extract_with_camelot()
        elif parser_name == 'tabula':
            return self._extract_with_tabula()
        elif parser_name == 'pdfplumber':
            return self._extract_with_pdfplumber()
        elif parser_name == 'pymupdf':
            return self._extract_with_pymupdf()
        elif parser_name == 'ocr':
            return self._extract_with_ocr()
        else:
            return self._extract_with_pdfplumber()  # Fallback
    
    def _extract_with_pdfplumber(self) -> List[Dict]:
        """Extract using pdfplumber"""
        from pdfplumber_parser import parse_with_pdfplumber
        return parse_with_pdfplumber(self.pdf_path)
    
    def _extract_with_camelot(self) -> List[Dict]:
        """Extract using camelot for complex tables"""
        transactions = []
        try:
            # Try both lattice and stream methods
            for flavor in ['lattice', 'stream']:
                tables = camelot.read_pdf(self.pdf_path, pages='all', flavor=flavor)
                
                for table in tables:
                    df = table.df
                    # Parse table data
                    for _, row in df.iterrows():
                        trans = self._parse_table_row(row.tolist())
                        if trans:
                            transactions.append(trans)
        except Exception as e:
            logger.error(f"Camelot extraction failed: {e}")
        
        return transactions
    
    def _extract_with_tabula(self) -> List[Dict]:
        """Extract using tabula-py"""
        transactions = []
        try:
            # Extract all tables
            tables = tabula.read_pdf(self.pdf_path, pages='all', multiple_tables=True)
            
            for df in tables:
                # Parse each table
                for _, row in df.iterrows():
                    trans = self._parse_table_row(row.tolist())
                    if trans:
                        transactions.append(trans)
        except Exception as e:
            logger.error(f"Tabula extraction failed: {e}")
        
        return transactions
    
    def _extract_with_pymupdf(self) -> List[Dict]:
        """Extract using PyMuPDF for better text positioning"""
        transactions = []
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(self.pdf_path)
            for page in doc:
                # Get text with positions
                blocks = page.get_text("dict")
                
                # Process text blocks
                for block in blocks["blocks"]:
                    if block["type"] == 0:  # Text block
                        for line in block["lines"]:
                            text = " ".join([span["text"] for span in line["spans"]])
                            trans = self._parse_transaction_line(text)
                            if trans:
                                transactions.append(trans)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
        
        return transactions
    
    def _extract_with_ocr(self) -> List[Dict]:
        """Extract using OCR for scanned documents"""
        try:
            from advanced_ocr_parser import parse_scanned_pdf_advanced
            print("Using advanced OCR parser...")
            return parse_scanned_pdf_advanced(self.pdf_path)
        except Exception as e:
            print(f"Advanced OCR failed: {e}, trying basic OCR...")
            # Fallback to basic OCR
            try:
                from ocr_parser import parse_scanned_pdf
                return parse_scanned_pdf(self.pdf_path)
            except Exception as e2:
                print(f"Basic OCR also failed: {e2}")
                return []
    
    def _parse_table_row(self, row: List) -> Dict:
        """Parse a table row into a transaction"""
        if not row or len(row) < 2:
            return None
        
        # Clean row data
        row = [str(cell).strip() if cell else '' for cell in row]
        
        # Look for date, description, and amount
        date_val = None
        desc_val = None
        amount_val = None
        
        for cell in row:
            if not cell:
                continue
            
            # Check for date
            if not date_val and self._is_date(cell):
                date_val = cell
            # Check for amount
            elif not amount_val and self._is_amount(cell):
                amount_val = self._parse_amount(cell)
            # Use as description
            elif not desc_val and len(cell) > 3:
                desc_val = cell
        
        if date_val and (desc_val or amount_val):
            return {
                'date_string': date_val,
                'description': desc_val or 'Transaction',
                'amount': amount_val or 0.0
            }
        
        return None
    
    def _parse_transaction_line(self, line: str) -> Dict:
        """Parse a text line as a transaction"""
        line = line.strip()
        if not line:
            return None
        
        # Common patterns
        patterns = [
            # Date Description Amount
            r'(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
            # YYYY-MM-DD Description Amount
            r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
            # DD MMM YYYY Description Amount
            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                return {
                    'date_string': groups[0],
                    'description': groups[1].strip(),
                    'amount': self._parse_amount(groups[2])
                }
        
        return None
    
    def _is_date(self, text: str) -> bool:
        """Check if text is a date"""
        date_patterns = [
            r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}$',
            r'^[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}$'
        ]
        return any(re.match(p, text.strip()) for p in date_patterns)
    
    def _is_amount(self, text: str) -> bool:
        """Check if text is an amount"""
        amount_pattern = r'^[-+]?\$?[\d,]+\.?\d*$'
        return bool(re.match(amount_pattern, text.strip()))
    
    def _parse_amount(self, text: str) -> float:
        """Parse amount from text"""
        text = text.replace('$', '').replace(',', '').strip()
        
        # Handle parentheses for negative
        if text.startswith('(') and text.endswith(')'):
            text = '-' + text[1:-1]
        
        try:
            return float(text)
        except:
            return 0.0