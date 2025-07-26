#!/usr/bin/env python3
"""Test OCR on page 2 of dummy PDF which should have dated transactions"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract
from backend.ocr_parser import parse_ocr_text

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print("Extracting text from page 2...")
print("=" * 70)

images = convert_from_path(pdf_path, dpi=300)
if len(images) >= 2:
    # Get text from page 2
    text = pytesseract.image_to_string(images[1])
    
    print("Page 2 OCR Text:")
    print("-" * 50)
    print(text)
    
    print("\n\nParsing transactions from page 2...")
    transactions = parse_ocr_text(text)
    
    print(f"\nFound {len(transactions)} transactions")
    
    if transactions:
        for i, trans in enumerate(transactions):
            print(f"\n{i+1}. Transaction:")
            for key, value in trans.items():
                print(f"   {key}: {value}")
    else:
        # Debug - look for date patterns
        import re
        lines = text.split('\n')
        
        print("\nDebugging - lines with dates:")
        for line in lines:
            if re.search(r'\d{1,2}/\d{1,2}', line):
                print(f"  {line}")
else:
    print("PDF doesn't have page 2!")