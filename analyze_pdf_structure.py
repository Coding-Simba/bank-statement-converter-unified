#!/usr/bin/env python3
"""Analyze PDF structure to understand transaction layout"""

import os
import subprocess
import re

pdf_path = './test_example.pdf'

print("=== PDF STRUCTURE ANALYSIS ===")
print("=" * 60)

# Extract text with layout from both pages
print("\n1. Full text extraction with layout (both pages):")
print("-" * 40)

# Use pdftotext to extract each page separately
for page in [1, 2]:
    print(f"\n--- Page {page} ---")
    result = subprocess.run(['pdftotext', '-layout', '-f', str(page), '-l', str(page), pdf_path, '-'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
        print(f"\n[Page {page} has {len(result.stdout)} characters]")
    else:
        print(f"Error: {result.stderr}")

# Try with pdf2txt which sometimes works better
print("\n\n2. Using pdf2txt.py (if available):")
print("-" * 40)
result = subprocess.run(['pdf2txt.py', pdf_path], capture_output=True, text=True)
if result.returncode == 0:
    text = result.stdout
    # Look for transaction patterns
    lines = text.split('\n')
    transaction_lines = []
    
    for i, line in enumerate(lines):
        # Look for dates or amounts
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) or \
           re.search(r'[$-]?\d+\.\d{2}', line):
            transaction_lines.append((i, line))
    
    print(f"Found {len(transaction_lines)} potential transaction lines:")
    for line_num, line in transaction_lines[:20]:  # Show first 20
        print(f"Line {line_num}: {line.strip()}")
else:
    print("pdf2txt.py not available or error occurred")

# Use OCR specifically on page 2
print("\n\n3. OCR on page 2 only:")
print("-" * 40)

# First extract page 2 as a separate PDF
try:
    from pypdf import PdfReader, PdfWriter
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[1])  # Page 2 (0-indexed)
    
    with open('page2_only.pdf', 'wb') as f:
        writer.write(f)
    
    print("Extracted page 2 to page2_only.pdf")
    
    # Now OCR just page 2
    from backend.ocr_parser import parse_scanned_pdf
    transactions = parse_scanned_pdf('page2_only.pdf')
    print(f"OCR found {len(transactions)} transactions on page 2")
    
    if len(transactions) == 0:
        # Try to get raw OCR text
        print("\nTrying raw OCR text extraction:")
        result = subprocess.run(['tesseract', 'page2_only.pdf', '-', '--psm', '6'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Raw OCR text:")
            print(result.stdout[:1000])  # First 1000 chars
        else:
            print(f"Tesseract error: {result.stderr}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Check with pdfimages if page 2 has extractable images
print("\n\n4. Checking for images in PDF:")
print("-" * 40)
result = subprocess.run(['pdfimages', '-list', pdf_path], capture_output=True, text=True)
if result.returncode == 0:
    print("Images found:")
    print(result.stdout)
else:
    print("pdfimages not available or error")