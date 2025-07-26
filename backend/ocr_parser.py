"""OCR parser for scanned PDFs using Tesseract and pdf2image"""

import os
import tempfile
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

# OCR and image processing imports
try:
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    print(f"OCR dependencies not installed: {e}")
    print("Install with: pip install pdf2image pillow pytesseract opencv-python")

logger = logging.getLogger(__name__)

def check_ocr_requirements():
    """Check if OCR requirements are met"""
    if not OCR_AVAILABLE:
        return False, "OCR libraries not installed"
    
    # Check if Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
        return True, "OCR ready"
    except Exception:
        return False, "Tesseract not installed. Install with: brew install tesseract (Mac) or apt-get install tesseract-ocr (Linux)"

def preprocess_image(image):
    """Preprocess image for better OCR accuracy"""
    # Convert PIL image to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to get better contrast
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    # Deskew if needed
    coords = np.column_stack(np.where(denoised > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:  # Only deskew if angle is significant
            (h, w) = denoised.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            denoised = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    # Convert back to PIL
    return Image.fromarray(denoised)

def extract_text_from_image(image, preprocess=True):
    """Extract text from image using Tesseract"""
    if preprocess:
        image = preprocess_image(image)
    
    # Configure Tesseract
    custom_config = r'--oem 3 --psm 6'  # Use LSTM OCR Engine with uniform block of text
    
    # Extract text
    text = pytesseract.image_to_string(image, config=custom_config)
    
    # Also get detailed data for better parsing
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=custom_config)
    
    return text, data

def parse_ocr_text(text):
    """Parse OCR text to extract transactions"""
    transactions = []
    
    # Clean up common OCR errors
    text = clean_ocr_text(text)
    
    lines = text.split('\n')
    
    # Common patterns for transactions in OCR text
    patterns = [
        # Date (MM/DD) at start followed by description and amount
        r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$',
        
        # Date (MM/DD) at start followed by description (amount might be on next line)
        r'^(\d{1,2}/\d{1,2})\s+(.+?)$',
        
        # Date at start followed by description and negative amount and balance
        r'^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+([A-Z0-9#\-\s]+.*?)\s+(-?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
        
        # Date at start of line followed by description and amount (no balance)
        r'^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+([A-Z0-9#\-\s]+.*?)\s+(-?[\d,]+\.\d{2})$',
        
        # With currency symbols
        r'^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+?)\s+(-?[£$€]\s*[\d,]+\.\d{2})',
        
        # Check entries: "1234 10/05 $9.98"
        r'^(\d{4})\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.\d{2})',
    ]
    
    # Try to identify header row to understand column structure
    header_keywords = ['date', 'description', 'amount', 'debit', 'credit', 'balance', 'transaction']
    header_line = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Check if this line has multiple header keywords (not just a date)
        keyword_count = sum(1 for keyword in header_keywords if keyword in line_lower)
        if keyword_count >= 2:  # At least 2 keywords to be considered a header
            header_line = i
            break
    
    # Process all lines, but skip the header if found
    start_line = 0
    
    for i, line in enumerate(lines[start_line:]):
        line = line.strip()
        if not line or len(line) < 10:  # Skip short lines
            continue
            
        # Skip the header line if identified
        if header_line is not None and i + start_line == header_line:
            continue
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) >= 4:
                    # Date, description, amount, balance
                    date_str = clean_ocr_date(match.group(1))
                    description = match.group(2).strip()
                    amount_str = match.group(3)  # Transaction amount
                    # balance = match.group(4)  # We could use this for validation
                elif len(match.groups()) >= 3:
                    # Extract date, description, amount
                    date_str = clean_ocr_date(match.group(1))
                    description = match.group(2).strip()
                    amount_str = match.group(3)
                elif len(match.groups()) == 3 and re.match(r'^\d{4}', line):
                    # Check pattern: check# date amount
                    check_num = match.group(1)
                    date_str = match.group(2)
                    amount_str = match.group(3)
                    description = f"CHECK {check_num}"
                elif len(match.groups()) == 2:
                    # Could be date+description or description+amount
                    if re.match(r'^\d{1,2}[/\-\.]\d{1,2}', match.group(1)):
                        # Date + description (no amount)
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount_str = "0.00"  # Default, might find amount later
                    else:
                        # Description + amount
                        date_str = None
                        description = match.group(1).strip()
                        amount_str = match.group(2)
                else:
                    continue
                
                # Clean and validate
                if description and len(description) > 3:
                    amount = extract_amount_ocr(amount_str)
                    if amount is not None and amount != 0:
                        transaction = {
                            'description': clean_description(description),
                            'amount': amount,
                            'amount_string': amount_str
                        }
                        
                        if date_str:
                            date = parse_ocr_date(date_str)
                            if date:
                                transaction['date'] = date
                                transaction['date_string'] = date_str
                        
                        transactions.append(transaction)
                break
    
    return transactions

def clean_ocr_text(text):
    """Clean common OCR errors"""
    # Fix common OCR mistakes
    replacements = {
        ' l ': ' 1 ',  # l often mistaken for 1
        ' O ': ' 0 ',  # O often mistaken for 0
        ' S ': ' $ ',  # S often mistaken for $
        '|': '1',      # Pipe often mistaken for 1
        '，': ',',     # Full-width comma
        '．': '.',     # Full-width period
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    return text

def clean_ocr_date(date_str):
    """Clean OCR errors in dates"""
    # Replace common OCR errors in dates
    date_str = date_str.replace('O', '0').replace('o', '0')
    date_str = date_str.replace('l', '1').replace('I', '1')
    date_str = date_str.replace(' ', '')
    return date_str

def parse_ocr_date(date_str):
    """Parse date from OCR text with error tolerance"""
    if not date_str:
        return None
    
    # Clean the date string
    date_str = clean_ocr_date(date_str)
    
    # Try multiple date formats
    formats = [
        '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
        '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d',
        '%m.%d.%Y', '%d.%m.%Y',
        '%m/%d/%y', '%d/%m/%y',  # 2-digit year
        '%m/%d', '%d/%m',  # Month/day only - will use current year
        '%m-%d', '%d-%m',  # Month-day only
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            # If no year, use current year
            if parsed_date.year == 1900:  # Default year when not specified
                current_year = datetime.now().year
                parsed_date = parsed_date.replace(year=current_year)
            return parsed_date
        except ValueError:
            continue
    
    return None

def extract_amount_ocr(amount_str):
    """Extract amount from OCR text with error tolerance"""
    try:
        # Clean the amount string
        amount_str = amount_str.strip()
        
        # Remove currency symbols
        amount_str = re.sub(r'[£$€¥₹]', '', amount_str)
        
        # Fix OCR errors
        amount_str = amount_str.replace('O', '0').replace('o', '0')
        amount_str = amount_str.replace('l', '1').replace('I', '1')
        amount_str = amount_str.replace(' ', '')
        
        # Handle different decimal separators
        if ',' in amount_str and '.' in amount_str:
            # Both present - determine which is decimal
            if amount_str.rfind(',') > amount_str.rfind('.'):
                # Comma is decimal separator (European)
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # Period is decimal separator (US)
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Only comma - check if it's decimal or thousand separator
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely decimal separator
                amount_str = amount_str.replace(',', '.')
            else:
                # Likely thousand separator
                amount_str = amount_str.replace(',', '')
        
        return float(amount_str)
    except:
        return None

def clean_description(desc):
    """Clean transaction description from OCR"""
    # Remove excessive spaces
    desc = ' '.join(desc.split())
    
    # Remove common OCR artifacts
    desc = re.sub(r'[|_]{2,}', '', desc)  # Remove multiple pipes or underscores
    desc = re.sub(r'\s+[-–—]\s+', ' - ', desc)  # Normalize dashes
    
    # Capitalize first letter
    if desc:
        desc = desc[0].upper() + desc[1:]
    
    return desc

def parse_scanned_pdf(pdf_path, enhance_quality=True):
    """Main function to parse scanned PDFs using OCR"""
    if not OCR_AVAILABLE:
        raise ImportError("OCR dependencies not installed. Run: pip install pdf2image pillow pytesseract opencv-python")
    
    transactions = []
    
    logger.info(f"Starting OCR processing for {pdf_path}")
    
    try:
        # Convert PDF to images
        # Use higher DPI for better OCR accuracy
        images = convert_from_path(pdf_path, dpi=300)
        
        logger.info(f"Converted PDF to {len(images)} images")
        
        # Process each page
        for i, image in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")
            
            # Enhance image quality if requested
            if enhance_quality:
                # Increase contrast
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
                
                # Sharpen
                image = image.filter(ImageFilter.SHARPEN)
            
            # Extract text using OCR
            text, data = extract_text_from_image(image)
            
            # Parse transactions from text
            page_transactions = parse_ocr_text(text)
            
            if page_transactions:
                logger.info(f"Found {len(page_transactions)} transactions on page {i+1}")
                transactions.extend(page_transactions)
            
            # Also try table detection using the detailed data
            table_transactions = extract_table_from_ocr_data(data)
            if table_transactions:
                transactions.extend(table_transactions)
        
        # Remove duplicates
        seen = set()
        unique_transactions = []
        for trans in transactions:
            key = (trans.get('description', ''), trans.get('amount'))
            if key not in seen:
                seen.add(key)
                unique_transactions.append(trans)
        
        return unique_transactions
        
    except Exception as e:
        logger.error(f"OCR parsing failed: {e}")
        raise

def extract_table_from_ocr_data(data):
    """Extract transactions from OCR data with positional information"""
    transactions = []
    
    # Group text by lines based on vertical position
    lines = {}
    for i in range(len(data['text'])):
        if data['text'][i].strip():
            top = data['top'][i]
            # Group items within 10 pixels as same line
            line_key = round(top / 10) * 10
            
            if line_key not in lines:
                lines[line_key] = []
            
            lines[line_key].append({
                'text': data['text'][i],
                'left': data['left'][i],
                'width': data['width'][i],
                'conf': data['conf'][i]  # Confidence score
            })
    
    # Sort lines by vertical position
    sorted_lines = sorted(lines.items(), key=lambda x: x[0])
    
    # For statements like the dummy PDF, also look for check entries
    check_pattern = r'^\d{4}\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.\d{2})'
    
    # Try to identify columns
    for _, line_items in sorted_lines:
        # Sort by horizontal position
        line_items.sort(key=lambda x: x['left'])
        
        # Combine into line text
        line_text = ' '.join(item['text'] for item in line_items if item['conf'] > 30)
        
        # Try to parse as transaction
        if line_text:
            # Look for date pattern at start
            date_match = re.match(r'^(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+)', line_text)
            if date_match:
                date_str = date_match.group(1)
                rest = date_match.group(2)
                
                # Look for amount at end
                amount_match = re.search(r'([\d,]+\.?\d*)\s*$', rest)
                if amount_match:
                    amount_str = amount_match.group(1)
                    description = rest[:amount_match.start()].strip()
                    
                    amount = extract_amount_ocr(amount_str)
                    if amount and description:
                        transaction = {
                            'description': clean_description(description),
                            'amount': amount,
                            'amount_string': amount_str
                        }
                        
                        date = parse_ocr_date(date_str)
                        if date:
                            transaction['date'] = date
                            transaction['date_string'] = date_str
                        
                        transactions.append(transaction)
            
            # Also check for check entries (check# date amount)
            check_match = re.search(check_pattern, line_text)
            if check_match:
                date_str = check_match.group(1)
                amount_str = check_match.group(2)
                check_num = re.search(r'^(\d{4})', line_text)
                
                if check_num:
                    description = f"CHECK {check_num.group(1)}"
                    amount = extract_amount_ocr(amount_str)
                    
                    if amount:
                        transaction = {
                            'description': description,
                            'amount': -amount,  # Checks are withdrawals
                            'amount_string': amount_str
                        }
                        
                        date = parse_ocr_date(date_str)
                        if date:
                            transaction['date'] = date
                            transaction['date_string'] = date_str
                        
                        transactions.append(transaction)
    
    return transactions

# Export check function
def is_scanned_pdf(pdf_path):
    """Check if a PDF is likely scanned (image-based)"""
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check first few pages
            pages_to_check = min(3, len(pdf_reader.pages))
            total_text_length = 0
            
            for i in range(pages_to_check):
                text = pdf_reader.pages[i].extract_text()
                total_text_length += len(text.strip())
            
            # If very little text extracted, likely scanned
            avg_text_per_page = total_text_length / pages_to_check
            return avg_text_per_page < 100  # Less than 100 chars per page
            
    except Exception:
        return False