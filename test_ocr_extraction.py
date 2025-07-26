#!/usr/bin/env python3
"""Test OCR extraction for page 2"""

from backend.universal_parser import parse_universal_pdf
from backend.ocr_parser import parse_scanned_pdf, check_ocr_requirements
import PyPDF2
import os

pdf_path = './test_example.pdf'

print("=== OCR EXTRACTION TEST ===")
print("=" * 60)

# Check OCR requirements
print("\n1. OCR Requirements Check:")
ocr_ready, message = check_ocr_requirements()
print(f"OCR Ready: {ocr_ready}")
print(f"Message: {message}")

# Try OCR extraction directly
print("\n2. Direct OCR Extraction:")
print("-" * 40)
try:
    transactions = parse_scanned_pdf(pdf_path)
    print(f"Transactions found via OCR: {len(transactions)}")
    
    for i, trans in enumerate(transactions[:10]):  # Show first 10
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'N/A')}")
        print(f"  Description: {trans.get('description', 'N/A')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
except Exception as e:
    print(f"OCR Error: {e}")
    import traceback
    traceback.print_exc()

# Let's force OCR in our parser by temporarily modifying the extraction
print("\n\n3. Forcing universal parser to use OCR:")
print("-" * 40)

# Create a test script that modifies the parser behavior
test_script = '''
import os
os.environ['FORCE_OCR'] = '1'
from backend.universal_parser import parse_universal_pdf

# Temporarily patch to force OCR
import backend.universal_parser as up
original_is_scanned = up.is_scanned_pdf
up.is_scanned_pdf = lambda x: True  # Force it to think it's scanned

try:
    transactions = parse_universal_pdf('./test_example.pdf')
    print(f"Transactions with forced OCR: {len(transactions)}")
    
    for i, trans in enumerate(transactions[:10]):
        print(f"\\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'N/A')}")
        print(f"  Description: {trans.get('description', 'N/A')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
finally:
    # Restore
    up.is_scanned_pdf = original_is_scanned
'''

with open('test_force_ocr.py', 'w') as f:
    f.write(test_script)

os.system('python test_force_ocr.py')

# Check what pdftotext sees with layout preserved
print("\n\n4. pdftotext with layout:")
print("-" * 40)
os.system('pdftotext -layout ./test_example.pdf - | head -100')