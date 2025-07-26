#!/usr/bin/env python3
"""Examine the screenshot PDF content"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract

pdf_path = "/Users/MAC/Downloads/Shot-2024-09-14-at-19.24.43@2x.jpg.pdf"

print("Extracting OCR text from screenshot PDF...")
print("=" * 70)

# Convert to image
images = convert_from_path(pdf_path, dpi=300)

if images:
    # Get OCR text
    text = pytesseract.image_to_string(images[0])
    
    print("OCR Text:")
    print("-" * 50)
    print(text)
    print("-" * 50)
    
    # Look for transaction patterns
    lines = text.split('\n')
    print("\nLines with dates or amounts:")
    for line in lines:
        line = line.strip()
        if line:
            # Check if line has date pattern
            import re
            has_date = bool(re.search(r'\d{1,2}[/-]\d{1,2}', line))
            has_amount = bool(re.search(r'\$?\d+[.,]\d{2}', line))
            
            if has_date or has_amount:
                print(f"  {line}")