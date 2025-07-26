"""Advanced OCR parser that handles complex PDF layouts using multiple strategies"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import defaultdict

try:
    from pdf2image import convert_from_path
    from PIL import Image
    import pytesseract
    import cv2
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedOCRParser:
    """Advanced OCR parser with multi-pass processing and intelligent layout detection"""
    
    def __init__(self):
        self.date_patterns = [
            (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', '%m/%d/%Y'),
            (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b', '%m/%d/%y'),
            (r'\b(\d{1,2}[/-]\d{1,2})\b', '%m/%d'),
            (r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b', '%Y/%m/%d'),
            (r'\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b', '%m.%d.%Y'),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}\b', '%b %d, %Y'),
            (r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}\b', '%d %b %Y'),
        ]
        
        self.amount_patterns = [
            r'[$€£¥₹]?\s*[-+]?\s*\d{1,3}(?:[,.\s]\d{3})*(?:[,.]\d{1,2})?',
            r'[-+]?\s*\d{1,3}(?:[,.\s]\d{3})*(?:[,.]\d{1,2})?\s*[$€£¥₹]?',
            r'\(\s*\d{1,3}(?:[,.\s]\d{3})*(?:[,.]\d{1,2})?\s*\)',  # Negative in parentheses
        ]
    
    def parse_pdf(self, pdf_path: str, enhance_quality: bool = True) -> List[Dict]:
        """Main entry point for parsing any PDF"""
        if not OCR_AVAILABLE:
            raise ImportError("OCR dependencies not installed")
        
        all_transactions = []
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"Converted PDF to {len(images)} images")
            
            for page_num, image in enumerate(images):
                logger.info(f"Processing page {page_num + 1}/{len(images)}")
                
                # Get OCR data with positional information
                page_data = self._extract_page_data(image, enhance_quality)
                
                # Try multiple parsing strategies
                transactions = []
                
                # Strategy 1: Layout-based parsing (best for tables)
                layout_trans = self._parse_with_layout_detection(page_data)
                if layout_trans:
                    logger.info(f"Layout parser found {len(layout_trans)} transactions")
                    transactions.extend(layout_trans)
                
                # Strategy 2: Pattern-based parsing (fallback)
                if not transactions:
                    pattern_trans = self._parse_with_patterns(page_data)
                    if pattern_trans:
                        logger.info(f"Pattern parser found {len(pattern_trans)} transactions")
                        transactions.extend(pattern_trans)
                
                # Strategy 3: Multi-line parsing (for complex layouts)
                if not transactions:
                    multiline_trans = self._parse_multiline_format(page_data)
                    if multiline_trans:
                        logger.info(f"Multi-line parser found {len(multiline_trans)} transactions")
                        transactions.extend(multiline_trans)
                
                # Add page number to transactions
                for trans in transactions:
                    trans['page'] = page_num + 1
                
                all_transactions.extend(transactions)
        
        except Exception as e:
            logger.error(f"OCR parsing failed: {e}")
            raise
        
        # Post-process and deduplicate
        return self._post_process_transactions(all_transactions)
    
    def _extract_page_data(self, image: Image, enhance: bool = True) -> Dict:
        """Extract text and layout information from page"""
        if enhance:
            # Enhance image for better OCR
            image = self._enhance_image(image)
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Also get plain text
        text = pytesseract.image_to_string(image)
        
        # Get text with preserved layout
        layout_text = pytesseract.image_to_string(image, config='--psm 6')
        
        return {
            'data': data,
            'text': text,
            'layout_text': layout_text,
            'lines': text.split('\n'),
            'image_size': image.size
        }
    
    def _enhance_image(self, image: Image) -> Image:
        """Enhance image for better OCR accuracy"""
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Convert back to PIL
        return Image.fromarray(denoised)
    
    def _parse_with_layout_detection(self, page_data: Dict) -> List[Dict]:
        """Parse using layout detection to identify table structures"""
        transactions = []
        data = page_data['data']
        
        # Group text by lines based on vertical position
        lines = defaultdict(list)
        for i in range(len(data['text'])):
            if data['text'][i].strip() and data['conf'][i] > 30:
                # Group by approximate line (within 10 pixels)
                line_y = round(data['top'][i] / 10) * 10
                lines[line_y].append({
                    'text': data['text'][i],
                    'left': data['left'][i],
                    'width': data['width'][i],
                    'conf': data['conf'][i]
                })
        
        # Sort lines by vertical position
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        
        # Detect column positions
        column_positions = self._detect_columns(sorted_lines)
        
        # Parse each line based on detected columns
        for line_y, items in sorted_lines:
            # Sort items by horizontal position
            items.sort(key=lambda x: x['left'])
            
            # Try to extract transaction from line
            trans = self._extract_transaction_from_line(items, column_positions)
            if trans:
                transactions.append(trans)
        
        # Handle transactions that span multiple lines
        transactions = self._merge_multiline_transactions(transactions, sorted_lines)
        
        return transactions
    
    def _detect_columns(self, sorted_lines: List[Tuple]) -> Dict[str, int]:
        """Detect column positions based on text alignment"""
        # Collect all x-positions
        x_positions = defaultdict(int)
        
        for _, items in sorted_lines:
            for item in items:
                # Round to nearest 10 pixels
                x = round(item['left'] / 10) * 10
                x_positions[x] += 1
        
        # Find common x-positions (likely column starts)
        common_positions = sorted(
            [(pos, count) for pos, count in x_positions.items() if count > 2],
            key=lambda x: x[0]
        )
        
        # Guess column types based on position and content
        columns = {}
        if len(common_positions) >= 2:
            columns['date'] = common_positions[0][0]
            columns['description'] = common_positions[1][0] if len(common_positions) > 1 else None
            columns['amount'] = common_positions[-1][0] if len(common_positions) > 2 else None
        
        return columns
    
    def _extract_transaction_from_line(self, items: List[Dict], columns: Dict[str, int]) -> Optional[Dict]:
        """Extract transaction from a line of items"""
        # Combine all text in line
        full_line = ' '.join(item['text'] for item in items)
        
        # Look for transaction patterns
        transaction = {}
        
        # Extract date
        for pattern, date_format in self.date_patterns:
            match = re.search(pattern, full_line)
            if match:
                date_str = match.group(1)
                date = self._parse_date(date_str, date_format)
                if date:
                    transaction['date'] = date
                    transaction['date_string'] = date_str
                    break
        
        # Extract amount
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, full_line)
            if matches:
                # Take the last amount found (usually the transaction amount)
                amount_str = matches[-1]
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    transaction['amount'] = amount
                    transaction['amount_string'] = amount_str
                    break
        
        # Extract description
        if items:
            # Remove date and amount from description
            desc_parts = []
            for item in items:
                text = item['text']
                # Skip if it's a date or amount
                if not (transaction.get('date_string') and transaction['date_string'] in text):
                    if not (transaction.get('amount_string') and transaction['amount_string'] in text):
                        desc_parts.append(text)
            
            if desc_parts:
                transaction['description'] = ' '.join(desc_parts).strip()
        
        # Only return if we have meaningful data
        if transaction.get('description') or transaction.get('amount') is not None:
            return transaction
        
        return None
    
    def _parse_with_patterns(self, page_data: Dict) -> List[Dict]:
        """Parse using regex patterns on the text"""
        transactions = []
        lines = page_data['lines']
        
        # Common transaction patterns
        patterns = [
            # Date, description, amount on same line
            r'^(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s+(.+?)\s+([$€£¥₹]?\s*[-+]?\s*[\d,]+\.?\d*)\s*$',
            
            # Check entries: "1234 10/05 $9.98"
            r'^(\d{4})\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.\d{2})',
            
            # Amount at end of line with description
            r'^(.+?)\s+([$€£¥₹]?\s*[-+]?\s*[\d,]+\.?\d{2})\s*$',
            
            # Date at start, rest is description
            r'^(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s+(.+)$',
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    trans = self._parse_pattern_match(match, pattern)
                    if trans:
                        # Check if next line might contain missing amount
                        if trans.get('amount') is None and i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            amount = self._extract_amount_from_text(next_line)
                            if amount is not None:
                                trans['amount'] = amount
                                i += 1  # Skip next line
                        
                        transactions.append(trans)
                        matched = True
                        break
            
            if not matched:
                # Check if this line contains transaction keywords
                if self._is_likely_transaction(line):
                    trans = self._parse_free_form_transaction(line, lines, i)
                    if trans:
                        transactions.append(trans)
            
            i += 1
        
        return transactions
    
    def _parse_multiline_format(self, page_data: Dict) -> List[Dict]:
        """Parse transactions that span multiple lines"""
        transactions = []
        lines = page_data['lines']
        
        # Look for sections with transaction data
        in_transaction_section = False
        current_transaction = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect transaction section headers
            if any(keyword in line.lower() for keyword in ['transactions', 'activity', 'deposits', 'withdrawals']):
                in_transaction_section = True
                continue
            
            if not in_transaction_section:
                continue
            
            # Check if line has a date
            date_found = False
            for pattern, date_format in self.date_patterns:
                match = re.search(pattern, line)
                if match:
                    # Save previous transaction if exists
                    if current_transaction:
                        transactions.append(current_transaction)
                    
                    # Start new transaction
                    current_transaction = {
                        'date': self._parse_date(match.group(1), date_format),
                        'date_string': match.group(1),
                        'description': line[match.end():].strip()
                    }
                    date_found = True
                    break
            
            if not date_found and current_transaction:
                # This might be continuation of description or amount
                amount = self._extract_amount_from_text(line)
                if amount is not None:
                    current_transaction['amount'] = amount
                elif line and not any(skip in line.lower() for skip in ['total', 'balance', 'page']):
                    # Append to description
                    current_transaction['description'] = current_transaction.get('description', '') + ' ' + line
        
        # Don't forget last transaction
        if current_transaction:
            transactions.append(current_transaction)
        
        return transactions
    
    def _merge_multiline_transactions(self, transactions: List[Dict], sorted_lines: List[Tuple]) -> List[Dict]:
        """Merge transactions that span multiple lines"""
        merged = []
        i = 0
        
        while i < len(transactions):
            trans = transactions[i].copy()
            
            # If transaction is missing amount, look for it in nearby transactions
            if trans.get('amount') is None:
                for j in range(i + 1, min(i + 3, len(transactions))):
                    next_trans = transactions[j]
                    if next_trans.get('amount') is not None and not next_trans.get('date'):
                        # Likely the amount for previous transaction
                        trans['amount'] = next_trans['amount']
                        i = j  # Skip the amount-only entry
                        break
            
            merged.append(trans)
            i += 1
        
        return merged
    
    def _parse_pattern_match(self, match: re.Match, pattern: str) -> Optional[Dict]:
        """Parse a regex match into a transaction"""
        groups = match.groups()
        trans = {}
        
        # Check pattern
        if 'check' in pattern.lower() or len(groups) == 3 and re.match(r'^\d{4}', groups[0]):
            # Check entry pattern
            trans['description'] = f"CHECK {groups[0]}"
            trans['date_string'] = groups[1]
            trans['amount'] = -self._parse_amount(groups[2])  # Checks are withdrawals
        elif len(groups) >= 3:
            # Date, description, amount
            trans['date_string'] = groups[0]
            trans['description'] = groups[1].strip()
            trans['amount'] = self._parse_amount(groups[2])
        elif len(groups) == 2:
            # Could be various formats
            if re.match(r'^\d{1,2}[/-]\d{1,2}', groups[0]):
                # Date + description
                trans['date_string'] = groups[0]
                trans['description'] = groups[1].strip()
            else:
                # Description + amount
                trans['description'] = groups[0].strip()
                trans['amount'] = self._parse_amount(groups[1])
        
        # Parse date if we have it
        if trans.get('date_string'):
            for pattern, date_format in self.date_patterns:
                if re.match(pattern, trans['date_string']):
                    date = self._parse_date(trans['date_string'], date_format)
                    if date:
                        trans['date'] = date
                    break
        
        return trans if trans else None
    
    def _is_likely_transaction(self, line: str) -> bool:
        """Check if a line likely contains transaction data"""
        # Transaction keywords
        keywords = [
            'purchase', 'payment', 'withdrawal', 'deposit', 'transfer',
            'credit', 'debit', 'check', 'atm', 'pos', 'ach', 'wire',
            'fee', 'charge', 'interest', 'dividend'
        ]
        
        line_lower = line.lower()
        
        # Has transaction keyword
        has_keyword = any(keyword in line_lower for keyword in keywords)
        
        # Has amount-like pattern
        has_amount = bool(re.search(r'\d+[.,]\d{2}', line))
        
        # Has date-like pattern
        has_date = bool(re.search(r'\d{1,2}[/-]\d{1,2}', line))
        
        return has_keyword or (has_amount and len(line) > 10) or has_date
    
    def _parse_free_form_transaction(self, line: str, all_lines: List[str], line_idx: int) -> Optional[Dict]:
        """Parse a transaction from free-form text"""
        trans = {}
        
        # Extract date
        for pattern, date_format in self.date_patterns:
            match = re.search(pattern, line)
            if match:
                trans['date'] = self._parse_date(match.group(1), date_format)
                trans['date_string'] = match.group(1)
                # Remove date from line for description
                line = line[:match.start()] + line[match.end():]
                break
        
        # Extract amount
        amount = self._extract_amount_from_text(line)
        if amount is not None:
            trans['amount'] = amount
            # Remove amount from description
            for pattern in self.amount_patterns:
                line = re.sub(pattern, '', line)
        
        # Clean description
        desc = line.strip()
        if desc and len(desc) > 3:
            trans['description'] = desc
        
        # If no amount, check next line
        if trans.get('amount') is None and line_idx + 1 < len(all_lines):
            next_line = all_lines[line_idx + 1].strip()
            amount = self._extract_amount_from_text(next_line)
            if amount is not None:
                trans['amount'] = amount
        
        return trans if trans.get('description') or trans.get('amount') is not None else None
    
    def _extract_amount_from_text(self, text: str) -> Optional[float]:
        """Extract amount from text using multiple patterns"""
        if not text:
            return None
        
        # Try each amount pattern
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Usually the last match is the amount
                amount_str = matches[-1]
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    return amount
        
        return None
    
    def _parse_date(self, date_str: str, date_format: str) -> Optional[datetime]:
        """Parse date string with given format"""
        try:
            # Clean date string
            date_str = date_str.strip()
            
            # Handle dates without year
            if '%Y' not in date_format and '%y' not in date_format:
                # Add current year
                current_year = datetime.now().year
                date_str += f"/{current_year}"
                date_format += "/%Y"
            
            return datetime.strptime(date_str, date_format)
        except:
            return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            if not amount_str:
                return None
            
            # Clean string
            amount_str = amount_str.strip()
            
            # Check if negative (parentheses)
            is_negative = amount_str.startswith('(') and amount_str.endswith(')')
            if is_negative:
                amount_str = amount_str[1:-1]
            
            # Remove currency symbols
            amount_str = re.sub(r'[$€£¥₹]', '', amount_str)
            
            # Handle negative sign
            if amount_str.startswith('-'):
                is_negative = True
                amount_str = amount_str[1:]
            elif amount_str.startswith('+'):
                amount_str = amount_str[1:]
            
            # Remove spaces
            amount_str = amount_str.replace(' ', '')
            
            # Handle different decimal/thousand separators
            if ',' in amount_str and '.' in amount_str:
                # Both present - determine which is which
                if amount_str.rfind(',') > amount_str.rfind('.'):
                    # Comma is decimal separator
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                else:
                    # Period is decimal separator
                    amount_str = amount_str.replace(',', '')
            elif ',' in amount_str:
                # Only comma - check if it's decimal or thousand
                parts = amount_str.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # Likely decimal
                    amount_str = amount_str.replace(',', '.')
                else:
                    # Likely thousand separator
                    amount_str = amount_str.replace(',', '')
            
            amount = float(amount_str)
            return -amount if is_negative else amount
            
        except:
            return None
    
    def _post_process_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Post-process and clean up transactions"""
        processed = []
        
        # Keywords that indicate non-transaction lines
        skip_keywords = [
            'page', 'account #', 'statement', 'balance', 'summary', 
            'beginning', 'ending', 'your city', 'james c. morrison',
            'sheridan drive', 'activity for', 'description', 'date',
            'deposits and other', 'withdrawals and other', 'continued'
        ]
        
        for trans in transactions:
            # Skip empty transactions
            if not trans.get('description') and trans.get('amount') is None:
                continue
            
            # Clean description
            if trans.get('description'):
                trans['description'] = ' '.join(trans['description'].split())
                
                # Skip if description contains skip keywords
                desc_lower = trans['description'].lower()
                if any(keyword in desc_lower for keyword in skip_keywords):
                    continue
                
                # Skip very short descriptions that are likely headers
                if len(trans['description']) < 3:
                    continue
            
            # Skip amounts that are likely not transactions
            if trans.get('amount') is not None:
                # Skip unrealistic amounts (likely OCR errors)
                if abs(trans['amount']) > 100000:
                    continue
                # Skip if no description and small amount
                if not trans.get('description') and abs(trans['amount']) < 10:
                    continue
            else:
                trans['amount'] = 0.0
            
            # Determine transaction type based on keywords
            if trans.get('description'):
                desc_lower = trans['description'].lower()
                if any(word in desc_lower for word in ['deposit', 'credit', 'refund', 'interest']):
                    trans['amount'] = abs(trans['amount'])
                elif any(word in desc_lower for word in ['withdrawal', 'purchase', 'payment', 'fee', 'charge']):
                    trans['amount'] = -abs(trans['amount'])
            
            # Fix check amounts (they should be negative)
            if trans.get('description', '').upper().startswith('CHECK'):
                trans['amount'] = -abs(trans['amount'])
            
            processed.append(trans)
        
        # Remove duplicates
        seen = set()
        unique = []
        for trans in processed:
            key = (
                trans.get('date'),
                trans.get('description', ''),
                trans.get('amount', 0)
            )
            if key not in seen:
                seen.add(key)
                unique.append(trans)
        
        return unique

# Main function to use the advanced parser
def parse_scanned_pdf_advanced(pdf_path: str) -> List[Dict]:
    """Parse scanned PDF using advanced OCR techniques"""
    parser = AdvancedOCRParser()
    return parser.parse_pdf(pdf_path)