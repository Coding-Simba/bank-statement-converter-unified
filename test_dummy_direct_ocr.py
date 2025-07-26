#!/usr/bin/env python3
"""Test OCR directly on dummy PDF"""

import sys
sys.path.append('.')

from backend.ocr_parser import parse_scanned_pdf
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print(f"Testing direct OCR on: {pdf_path}")
print("=" * 70)

try:
    transactions = parse_scanned_pdf(pdf_path)
    print(f"\nFound {len(transactions)} transactions")
    
    if transactions:
        for i, trans in enumerate(transactions[:10]):
            print(f"\n{i+1}. Transaction:")
            for key, value in trans.items():
                print(f"   {key}: {value}")
    else:
        print("\nNo transactions found!")
        
        # Let's see what the OCR text looks like
        from pdf2image import convert_from_path
        import pytesseract
        
        print("\nExtracting raw OCR text from first page...")
        images = convert_from_path(pdf_path, dpi=300)
        if images:
            text = pytesseract.image_to_string(images[0])
            print("\nOCR Text:")
            print("-" * 50)
            print(text)
            
            # Test parsing directly
            print("\n\nTesting parse_ocr_text directly...")
            from backend.ocr_parser import parse_ocr_text
            transactions2 = parse_ocr_text(text)
            print(f"Found {len(transactions2)} transactions from direct parsing")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()