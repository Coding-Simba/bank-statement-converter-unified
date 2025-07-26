#!/usr/bin/env python3
"""Test OCR to see raw data from dummy PDF"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print("Extracting OCR text from dummy PDF...")
print("=" * 70)

images = convert_from_path(pdf_path, dpi=300)

for page_num, image in enumerate(images):
    print(f"\n--- Page {page_num + 1} OCR Text ---")
    text = pytesseract.image_to_string(image)
    
    # Show first 20 lines
    lines = text.split('\n')
    for i, line in enumerate(lines[:30]):
        if line.strip():
            print(f"{i+1:3d}: {line}")