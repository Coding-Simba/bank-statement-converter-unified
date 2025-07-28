#\!/usr/bin/env python3
"""Test pdfplumber parser"""

from backend.pdfplumber_parser import parse_with_pdfplumber
import os

def test_pdf(pdf_path):
    print(f"\nTesting: {os.path.basename(pdf_path)}")
    print("="*60)
    
    try:
        trans = parse_with_pdfplumber(pdf_path)
        print(f"✓ Found {len(trans)} transactions")
        
        if trans:
            print("\nFirst 5 transactions:")
            for i, t in enumerate(trans[:5], 1):
                date = t.get('date_string', 'No date')
                desc = t.get('description', 'No description')[:40]
                amount = t.get('amount', 0)
                print(f"{i}. {date:<15} | {desc:<40} | ${amount:>10.2f}")
                
    except Exception as e:
        print(f"✗ Error: {e}")

# Test PDFs
pdfs = [
    "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
    "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf",
    "/Users/MAC/Desktop/pdfs/example_bank_statement.pdf"
]

for pdf in pdfs:
    if os.path.exists(pdf):
        test_pdf(pdf)
