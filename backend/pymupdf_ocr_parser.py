#!/usr/bin/env python3
"""
PyMuPDF parser with OCR support for scanned/image PDFs
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
from typing import List, Dict, Tuple, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

class PyMuPDFOCRParser:
    """PyMuPDF parser with OCR capabilities"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def parse(self) -> List[Dict]:
        """Main parsing method with OCR fallback"""
        all_transactions = []
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            logger.info(f"Processing page {page_num + 1}")
            
            # First try to extract text normally
            text = page.get_text()
            
            if len(text.strip()) < 50:  # Likely image-based
                logger.info(f"Page {page_num + 1} appears to be image-based, using OCR")
                transactions = self._parse_with_ocr(page)
            else:
                # Use column parser for text-based pages
                transactions = self._parse_text_page(page)
            
            all_transactions.extend(transactions)
        
        return self._deduplicate(all_transactions)
    
    def _parse_with_ocr(self, page) -> List[Dict]:
        """Parse page using OCR with column detection"""
        # Convert page to image
        mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_data))
        
        # Get OCR data with positioning
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Parse OCR data with column detection
        return self._parse_ocr_data(ocr_data)
    
    def _parse_ocr_data(self, ocr_data: Dict) -> List[Dict]:
        """Parse OCR data with intelligent column detection"""
        transactions = []
        
        # Group words by line
        lines = self._group_ocr_by_lines(ocr_data)
        
        # Detect column structure
        columns = self._detect_ocr_columns(lines)
        
        # Parse each line
        for line in lines:
            trans = self._parse_ocr_line(line, columns)
            if trans:
                transactions.append(trans)
        
        return transactions
    
    def _group_ocr_by_lines(self, ocr_data: Dict) -> List[List[Dict]]:
        """Group OCR words by line"""
        lines = {}
        
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            if ocr_data['text'][i].strip():
                line_num = ocr_data['line_num'][i]
                if line_num not in lines:
                    lines[line_num] = []
                
                lines[line_num].append({
                    'text': ocr_data['text'][i],
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'conf': ocr_data['conf'][i]
                })
        
        # Sort lines by top position
        sorted_lines = sorted(lines.items(), key=lambda x: min(w['top'] for w in x[1]))
        
        return [line[1] for line in sorted_lines]
    
    def _detect_ocr_columns(self, lines: List[List[Dict]]) -> Dict[str, int]:
        """Detect column positions from OCR data"""
        # Collect X positions for different data types
        date_positions = []
        amount_positions = []
        
        for line in lines:
            for word in line:
                text = word['text']
                left = word['left']
                
                if self._is_date(text):
                    date_positions.append(left)
                elif self._is_amount(text):
                    amount_positions.append(left)
        
        columns = {}
        
        # Find common column positions
        if date_positions:
            columns['date'] = self._find_column_position(date_positions)
        
        if amount_positions:
            # Group amounts by position (debit vs credit)
            amount_groups = self._cluster_positions(amount_positions)
            if len(amount_groups) >= 2:
                columns['debit'] = min(amount_groups[0])
                columns['credit'] = min(amount_groups[1])
            elif amount_groups:
                columns['amount'] = min(amount_groups[0])
        
        return columns
    
    def _parse_ocr_line(self, line: List[Dict], columns: Dict[str, int]) -> Optional[Dict]:
        """Parse a line of OCR data"""
        # Sort words by left position
        line.sort(key=lambda w: w['left'])
        
        # Extract components
        date = None
        description_parts = []
        debit = None
        credit = None
        
        for word in line:
            text = word['text'].strip()
            left = word['left']
            
            # Skip low confidence words
            if word['conf'] < 30:
                continue
            
            # Check if it's a date
            if self._is_date(text) and not date:
                date = text
            # Check if it's an amount
            elif self._is_amount(text):
                amount = self._parse_amount(text)
                
                # Determine if debit or credit based on position
                if 'debit' in columns and abs(left - columns['debit']) < 50:
                    debit = amount
                elif 'credit' in columns and abs(left - columns['credit']) < 50:
                    credit = amount
                elif 'amount' in columns and abs(left - columns['amount']) < 50:
                    # Single amount column - need to determine sign
                    if amount > 0:
                        credit = amount
                    else:
                        debit = abs(amount)
                else:
                    # No clear column - use as is
                    if amount > 0:
                        credit = amount
                    else:
                        debit = abs(amount)
            # Everything else is description
            else:
                # Skip common headers
                if text.upper() not in ['DATE', 'DESCRIPTION', 'DEBIT', 'CREDIT', 'BALANCE', 'AMOUNT']:
                    description_parts.append(text)
        
        # Build transaction if we have required fields
        if date and (description_parts or debit or credit):
            amount = 0
            if credit:
                amount = credit
            if debit:
                amount = -debit
            
            return {
                'date_string': date,
                'description': ' '.join(description_parts),
                'amount': amount
            }
        
        return None
    
    def _parse_text_page(self, page) -> List[Dict]:
        """Parse text-based page"""
        transactions = []
        
        # Get text with layout
        blocks = page.get_text("dict")
        
        # Extract text elements with positions
        elements = []
        for block in blocks.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    line_text = []
                    line_bbox = None
                    
                    for span in line.get("spans", []):
                        line_text.append(span.get("text", ""))
                        if not line_bbox:
                            line_bbox = span.get("bbox", [0, 0, 0, 0])
                    
                    if line_text:
                        elements.append({
                            'text': ' '.join(line_text),
                            'bbox': line_bbox
                        })
        
        # Parse elements
        for elem in elements:
            trans = self._parse_text_line(elem['text'])
            if trans:
                transactions.append(trans)
        
        return transactions
    
    def _parse_text_line(self, line: str) -> Optional[Dict]:
        """Parse a line of text"""
        line = line.strip()
        if not line:
            return None
        
        # Patterns for bank statement lines
        patterns = [
            # Date Description Amount
            r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+([-+]?\$?\d+\.\d{2})',
            # Date at start, amounts in columns
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+(\d+\.\d{2})\s*(\d+\.\d{2})?\s*(\d+\.\d{2})?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                date_str = groups[0]
                desc_str = groups[1].strip()
                
                # Handle different amount formats
                if len(groups) >= 5:  # Multiple amount columns
                    # Assuming: debit, credit, balance
                    debit = float(groups[2]) if groups[2] else 0
                    credit = float(groups[3]) if groups[3] else 0
                    amount = credit - debit if credit else -debit
                else:
                    amount = self._parse_amount(groups[2])
                
                return {
                    'date_string': date_str,
                    'description': desc_str,
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
        # Clean text
        text = text.strip().replace(' ', '').replace(',', '')
        amount_pattern = r'^[-+]?\$?\d+\.?\d*$'
        return bool(re.match(amount_pattern, text))
    
    def _parse_amount(self, text: str) -> float:
        """Parse amount from text"""
        # Remove currency symbols and spaces
        text = text.replace('$', '').replace(',', '').replace(' ', '').strip()
        
        # Handle parentheses for negative
        if text.startswith('(') and text.endswith(')'):
            text = '-' + text[1:-1]
        
        try:
            return float(text)
        except:
            return 0.0
    
    def _find_column_position(self, positions: List[int]) -> int:
        """Find most common column position"""
        if not positions:
            return 0
        
        # Round to nearest 10 pixels
        rounded = [round(p / 10) * 10 for p in positions]
        
        # Find most common
        from collections import Counter
        counter = Counter(rounded)
        return counter.most_common(1)[0][0]
    
    def _cluster_positions(self, positions: List[int], threshold: int = 100) -> List[List[int]]:
        """Cluster positions that are close together"""
        if not positions:
            return []
        
        sorted_pos = sorted(positions)
        clusters = [[sorted_pos[0]]]
        
        for pos in sorted_pos[1:]:
            if pos - clusters[-1][-1] < threshold:
                clusters[-1].append(pos)
            else:
                clusters.append([pos])
        
        return clusters
    
    def _deduplicate(self, transactions: List[Dict]) -> List[Dict]:
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for trans in transactions:
            key = (
                trans.get('date_string', ''),
                trans.get('description', ''),
                round(trans.get('amount', 0), 2)
            )
            if key not in seen:
                seen.add(key)
                unique.append(trans)
        
        return unique
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()

def parse_with_pymupdf_ocr(pdf_path: str) -> List[Dict]:
    """Main entry point for PyMuPDF OCR parsing"""
    parser = PyMuPDFOCRParser(pdf_path)
    try:
        return parser.parse()
    finally:
        parser.close()