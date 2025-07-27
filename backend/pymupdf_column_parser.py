#!/usr/bin/env python3
"""
PyMuPDF (Fitz) parser with advanced column detection for bank statements
"""
import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PyMuPDFColumnParser:
    """Advanced column-based parser using PyMuPDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def parse(self) -> List[Dict]:
        """Main parsing method"""
        all_transactions = []
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            logger.info(f"Processing page {page_num + 1}")
            
            # Extract text with positioning
            blocks = page.get_text("dict")
            
            # Try different parsing strategies
            # 1. Table detection
            table_trans = self._parse_tables(page)
            if table_trans:
                all_transactions.extend(table_trans)
                continue
            
            # 2. Column-based parsing
            column_trans = self._parse_by_columns(blocks)
            if column_trans:
                all_transactions.extend(column_trans)
                continue
            
            # 3. Line-by-line parsing
            line_trans = self._parse_by_lines(page)
            if line_trans:
                all_transactions.extend(line_trans)
        
        return self._deduplicate(all_transactions)
    
    def _parse_tables(self, page) -> List[Dict]:
        """Parse tables using PyMuPDF's table detection"""
        transactions = []
        
        # Find tables on the page
        tabs = page.find_tables()
        
        for tab in tabs:
            # Extract table data
            for row in tab.extract():
                trans = self._parse_table_row(row)
                if trans:
                    transactions.append(trans)
        
        return transactions
    
    def _parse_by_columns(self, blocks: Dict) -> List[Dict]:
        """Parse text by detecting column structure"""
        transactions = []
        
        # Extract all text elements with positions
        text_elements = []
        for block in blocks.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_elements.append({
                            'text': span.get("text", "").strip(),
                            'x0': span.get("bbox", [0])[0],
                            'y0': span.get("bbox", [0, 0])[1],
                            'x1': span.get("bbox", [0, 0, 0])[2],
                            'y1': span.get("bbox", [0, 0, 0, 0])[3]
                        })
        
        # Group by Y coordinate (same line)
        lines = self._group_by_line(text_elements)
        
        # Detect column positions
        columns = self._detect_columns(text_elements)
        
        # Parse each line as a potential transaction
        for line_elements in lines:
            trans = self._parse_line_with_columns(line_elements, columns)
            if trans:
                transactions.append(trans)
        
        return transactions
    
    def _parse_by_lines(self, page) -> List[Dict]:
        """Simple line-by-line parsing"""
        transactions = []
        text = page.get_text()
        
        for line in text.split('\n'):
            trans = self._parse_transaction_line(line)
            if trans:
                transactions.append(trans)
        
        return transactions
    
    def _group_by_line(self, elements: List[Dict]) -> List[List[Dict]]:
        """Group text elements by Y coordinate (same line)"""
        if not elements:
            return []
        
        # Sort by Y then X
        elements.sort(key=lambda e: (round(e['y0'], 1), e['x0']))
        
        lines = []
        current_line = [elements[0]]
        current_y = elements[0]['y0']
        
        for elem in elements[1:]:
            # If Y coordinate is similar (within 2 pixels), same line
            if abs(elem['y0'] - current_y) < 2:
                current_line.append(elem)
            else:
                lines.append(current_line)
                current_line = [elem]
                current_y = elem['y0']
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _detect_columns(self, elements: List[Dict]) -> Dict[str, float]:
        """Detect column positions based on text alignment"""
        # Common column patterns for bank statements
        date_x = []
        desc_x = []
        debit_x = []
        credit_x = []
        balance_x = []
        
        for elem in elements:
            text = elem['text']
            x = elem['x0']
            
            # Detect dates
            if self._is_date(text):
                date_x.append(x)
            # Detect amounts (right-aligned typically)
            elif self._is_amount(text):
                if elem['x1'] > 400:  # Right side of page
                    balance_x.append(x)
                elif elem['x1'] > 300:
                    credit_x.append(x)
                else:
                    debit_x.append(x)
        
        # Find most common positions
        columns = {}
        if date_x:
            columns['date'] = self._most_common_x(date_x)
        if debit_x:
            columns['debit'] = self._most_common_x(debit_x)
        if credit_x:
            columns['credit'] = self._most_common_x(credit_x)
        if balance_x:
            columns['balance'] = self._most_common_x(balance_x)
        
        return columns
    
    def _parse_line_with_columns(self, elements: List[Dict], columns: Dict[str, float]) -> Optional[Dict]:
        """Parse a line of elements using detected columns"""
        if not elements:
            return None
        
        # Sort by X position
        elements.sort(key=lambda e: e['x0'])
        
        date = None
        description = []
        amount = None
        
        for elem in elements:
            text = elem['text']
            x = elem['x0']
            
            # Match to columns
            if 'date' in columns and abs(x - columns['date']) < 10:
                if self._is_date(text):
                    date = text
            elif self._is_amount(text):
                amount = self._parse_amount(text)
            else:
                # Likely description
                description.append(text)
        
        # Build transaction if we have minimum required fields
        if date and (description or amount):
            return {
                'date_string': date,
                'description': ' '.join(description),
                'amount': amount or 0.0
            }
        
        return None
    
    def _parse_table_row(self, row: List) -> Optional[Dict]:
        """Parse a table row"""
        if not row or len(row) < 2:
            return None
        
        # Clean row data
        row = [str(cell).strip() if cell else '' for cell in row]
        
        # Look for date, description, and amounts
        date_val = None
        desc_val = None
        amount_val = None
        
        for i, cell in enumerate(row):
            if not cell:
                continue
            
            # Check for date
            if not date_val and self._is_date(cell):
                date_val = cell
            # Check for amount
            elif self._is_amount(cell):
                parsed_amount = self._parse_amount(cell)
                if parsed_amount != 0:
                    # Check if this is debit or credit based on position or sign
                    if i >= len(row) - 2:  # Last or second-to-last column
                        amount_val = parsed_amount
                    else:
                        amount_val = -abs(parsed_amount)  # Debit
            # Use as description
            elif not desc_val and len(cell) > 3 and not cell.isdigit():
                desc_val = cell
        
        if date_val and (desc_val or amount_val):
            return {
                'date_string': date_val,
                'description': desc_val or 'Transaction',
                'amount': amount_val or 0.0
            }
        
        return None
    
    def _parse_transaction_line(self, line: str) -> Optional[Dict]:
        """Parse a single line of text as transaction"""
        line = line.strip()
        if not line:
            return None
        
        # Common patterns
        patterns = [
            # Date Description Debit Credit Balance
            r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})?\s*(\d+\.\d{2})?',
            # Date Description Amount
            r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+([-+]?\$?\d+\.\d{2})',
            # Date at start, amount at end
            r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+([-+]?\d+\.\d{2})$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                date_str = groups[0]
                
                if len(groups) >= 5:  # Has debit/credit columns
                    desc_str = groups[1]
                    debit = float(groups[2]) if groups[2] else 0
                    credit = float(groups[3]) if groups[3] else 0
                    amount = credit - debit if credit else -debit
                else:
                    desc_str = groups[1]
                    amount = self._parse_amount(groups[2])
                
                return {
                    'date_string': date_str,
                    'description': desc_str.strip(),
                    'amount': amount
                }
        
        return None
    
    def _is_date(self, text: str) -> bool:
        """Check if text is a date"""
        date_patterns = [
            r'^\d{1,2}/\d{1,2}(?:/\d{2,4})?$',
            r'^\d{1,2}-\d{1,2}(?:-\d{2,4})?$',
            r'^\d{4}-\d{1,2}-\d{1,2}$'
        ]
        return any(re.match(p, text.strip()) for p in date_patterns)
    
    def _is_amount(self, text: str) -> bool:
        """Check if text is an amount"""
        amount_pattern = r'^[-+]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$'
        return bool(re.match(amount_pattern, text.strip().replace(' ', '')))
    
    def _parse_amount(self, text: str) -> float:
        """Parse amount from text"""
        # Remove currency symbols and spaces
        text = text.replace('$', '').replace(',', '').strip()
        
        # Handle parentheses for negative
        if text.startswith('(') and text.endswith(')'):
            text = '-' + text[1:-1]
        
        try:
            return float(text)
        except:
            return 0.0
    
    def _most_common_x(self, x_positions: List[float]) -> float:
        """Find most common X position (with tolerance)"""
        if not x_positions:
            return 0
        
        # Round to nearest 5 pixels
        rounded = [round(x / 5) * 5 for x in x_positions]
        
        # Find most common
        from collections import Counter
        counter = Counter(rounded)
        return counter.most_common(1)[0][0]
    
    def _deduplicate(self, transactions: List[Dict]) -> List[Dict]:
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for trans in transactions:
            key = (
                trans.get('date_string', ''),
                trans.get('description', ''),
                trans.get('amount', 0)
            )
            if key not in seen:
                seen.add(key)
                unique.append(trans)
        
        return unique
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()

def parse_with_pymupdf(pdf_path: str) -> List[Dict]:
    """Main entry point for PyMuPDF parsing"""
    parser = PyMuPDFColumnParser(pdf_path)
    try:
        return parser.parse()
    finally:
        parser.close()