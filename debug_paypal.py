#!/usr/bin/env python3
"""Debug PayPal date parsing issues"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.paypal_parser import PaypalParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf"

print("=== PayPal PDF Debug ===")

# Check PDF content
with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    lines = text.split('\n')[:30]
    
    print("First 30 lines:")
    for i, line in enumerate(lines):
        print(f"{i+1}: {line}")

# Test the parser
print("\n=== Testing PayPal Parser ===")
parser = PaypalParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test date parsing
test_dates = ["Apr 01, 2022", "04/01/22", "May 31, 2022"]
year = parser.detect_year_from_pdf(pdf_path)
print(f"\nDetected year: {year}")

for date_str in test_dates:
    parsed = parser.parse_date(date_str, year)
    print(f"'{date_str}' -> {parsed}")