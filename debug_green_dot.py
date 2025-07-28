#!/usr/bin/env python3
"""Debug Green Dot parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.green_dot_parser import GreenDotParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf"

print("=== Green Dot PDF Debug ===")

# Check PDF content
with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for page_num in range(min(2, len(pdf.pages))):
        print(f"\n=== Page {page_num + 1} ===")
        text = pdf.pages[page_num].extract_text()
        lines = text.split('\n')[:30]
        
        print("First 30 lines:")
        for i, line in enumerate(lines):
            print(f"{i+1}: {line}")

# Test the parser
print("\n=== Testing Green Dot Parser ===")
parser = GreenDotParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test extraction
transactions = parser.parse(pdf_path)
print(f"\nTotal transactions from custom parser: {len(transactions)}")

if transactions:
    print("\nAll transactions:")
    for i, trans in enumerate(transactions):
        print(f"{i+1}. {trans}")