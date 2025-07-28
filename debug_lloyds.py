#!/usr/bin/env python3
"""Debug Lloyds parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.lloyds_parser import LloydsParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/UK Lloyds Bank.pdf"

print("=== Lloyds PDF Debug ===")

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
print("\n=== Testing Lloyds Parser ===")
parser = LloydsParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test extraction
year = parser.detect_year_from_pdf(pdf_path)
print(f"\nDetected year: {year}")

transactions = parser.parse(pdf_path)
print(f"\nTotal transactions from custom parser: {len(transactions)}")

if transactions:
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. Date: {trans.get('date_string', 'N/A')}, Amount: ${trans.get('amount', 0):.2f}, Desc: {trans.get('description', 'N/A')[:50]}")