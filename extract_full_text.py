#!/usr/bin/env python3
"""Extract full text from PDF to understand structure"""

import PyPDF2
import subprocess
import os

pdf_path = './test_example.pdf'

print("=== FULL TEXT EXTRACTION ===")
print("=" * 60)

# Method 1: PyPDF2 full text
print("\n1. PyPDF2 Full Text:")
print("-" * 40)
try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        for i in range(len(pdf_reader.pages)):
            print(f"\n--- Page {i+1} ---")
            text = pdf_reader.pages[i].extract_text()
            print(text)
            print(f"\n[Page {i+1} character count: {len(text)}]")
except Exception as e:
    print(f"Error: {e}")

# Method 2: pdftotext
print("\n\n2. pdftotext Output:")
print("-" * 40)
try:
    result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True)
    if result.returncode == 0:
        text = result.stdout
        print(text)
        print(f"\n[Total character count: {len(text)}]")
        
        # Look for transaction patterns
        print("\n\nSearching for transaction patterns:")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Look for date patterns
            import re
            if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
                print(f"Line {i}: {line}")
                # Show context
                if i > 0:
                    print(f"  Previous: {lines[i-1]}")
                if i < len(lines) - 1:
                    print(f"  Next: {lines[i+1]}")
    else:
        print(f"pdftotext error: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Check if it's a scanned PDF
print("\n\n3. PDF Type Analysis:")
print("-" * 40)
from backend.ocr_parser import is_scanned_pdf
try:
    is_scanned = is_scanned_pdf(pdf_path)
    print(f"Is scanned PDF: {is_scanned}")
    
    # Get more info about the PDF
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Number of pages: {len(pdf_reader.pages)}")
        
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            print(f"\nPage {i+1}:")
            
            # Check for text
            text = page.extract_text()
            print(f"  Has text: {len(text) > 0}")
            print(f"  Text length: {len(text)}")
            
            # Check for images
            if '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                images = [x for x in xobjects if xobjects[x]['/Subtype'] == '/Image']
                print(f"  Has images: {len(images) > 0}")
                print(f"  Number of images: {len(images)}")
            else:
                print(f"  No XObject resources")
                
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()