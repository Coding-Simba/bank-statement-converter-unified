#!/usr/bin/env python3
"""Test the merged PDF to see what's happening"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf
import os

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

if os.path.exists(pdf_path):
    print(f"Testing PDF: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
    print("-" * 60)
    
    transactions = parse_universal_pdf(pdf_path)
    
    print(f"\nFound {len(transactions)} transactions")
    
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"\n{i+1}. Date: {trans.get('date')}")
            print(f"   Description: {trans.get('description')}")
            print(f"   Amount: {trans.get('amount')}")
    else:
        print("\nNo transactions found!")
        
        # Let's try to see what's in the PDF
        import PyPDF2
        print("\nTrying to extract raw text from first page:")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) > 0:
                text = pdf_reader.pages[0].extract_text()
                print(text[:500])  # First 500 chars
else:
    print(f"PDF not found at {pdf_path}")