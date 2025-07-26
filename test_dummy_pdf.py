#!/usr/bin/env python3
"""Test the dummy_statement.pdf to see why it's failing"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf
from backend.ocr_parser import is_scanned_pdf
import PyPDF2

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print(f"Testing: {pdf_path}")
print("=" * 70)

# First, check if it's text-based or scanned
print("\n1. Checking PDF type...")
try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"   Pages: {len(pdf_reader.pages)}")
        
        # Extract text from first page
        if len(pdf_reader.pages) > 0:
            text = pdf_reader.pages[0].extract_text()
            print(f"   Text length on page 1: {len(text)} characters")
            if text.strip():
                print(f"   First 500 characters:")
                print("   " + "-" * 50)
                print(text[:500].replace('\n', '\n   '))
            else:
                print("   No text extracted - likely a scanned PDF")
except Exception as e:
    print(f"   Error reading PDF: {e}")

# Check if it's detected as scanned
print(f"\n2. Is scanned PDF: {is_scanned_pdf(pdf_path)}")

# Try parsing
print("\n3. Attempting to parse...")
try:
    transactions = parse_universal_pdf(pdf_path)
    print(f"   Found {len(transactions)} transactions")
    
    if transactions:
        print("\n   First 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            date_str = trans['date'].strftime('%Y-%m-%d') if trans.get('date') else 'No date'
            desc = trans.get('description', 'No description')
            amount = trans.get('amount', 0)
            print(f"   {i+1}. {date_str} | {desc[:40]:40} | ${amount:>10.2f}")
    else:
        print("   No transactions found!")
        
except Exception as e:
    print(f"   Error parsing: {e}")
    import traceback
    traceback.print_exc()

# If no transactions, try to understand why
if 'transactions' not in locals() or not transactions:
    print("\n4. Debugging extraction methods...")
    
    # Try pdftotext
    print("\n   Trying pdftotext...")
    import subprocess
    try:
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   pdftotext output length: {len(result.stdout)} characters")
            if result.stdout.strip():
                print("   First 1000 characters:")
                print("   " + "-" * 50)
                print(result.stdout[:1000].replace('\n', '\n   '))
        else:
            print(f"   pdftotext failed: {result.stderr}")
    except Exception as e:
        print(f"   pdftotext error: {e}")