#!/usr/bin/env python3
"""Debug multi-line PayPal transactions"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf"

with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    lines = text.split('\n')
    
    print("Lines around the multi-line transaction:")
    for i, line in enumerate(lines[13:18]):
        print(f"{i+14}: '{line}'")