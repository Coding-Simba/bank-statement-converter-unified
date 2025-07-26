#!/usr/bin/env python3
"""Debug OCR processing"""

import sys
sys.path.append('.')

from backend.ocr_parser import parse_scanned_pdf, check_ocr_requirements
from pdf2image import convert_from_path
import pytesseract

pdf_path = "scanned_bank_statement.pdf"

print("Converting PDF to images...")
images = convert_from_path(pdf_path, dpi=300)
print(f"Got {len(images)} pages")

if images:
    print("\nExtracting text from first page...")
    text = pytesseract.image_to_string(images[0])
    print("OCR Text:")
    print("-" * 50)
    print(text)
    print("-" * 50)
    
    print("\nTrying to parse transactions...")
    try:
        transactions = parse_scanned_pdf(pdf_path)
        print(f"Found {len(transactions)} transactions")
        
        if transactions:
            for trans in transactions[:5]:
                print(f"- {trans}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()