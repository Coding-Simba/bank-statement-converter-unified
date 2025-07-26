#!/usr/bin/env python3
"""Analyze the PDF content to understand its structure"""

import PyPDF2
import re

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    print(f"Total pages: {len(pdf_reader.pages)}")
    
    # Look at first few pages
    for page_num in range(min(3, len(pdf_reader.pages))):
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*60}")
        
        text = pdf_reader.pages[page_num].extract_text()
        lines = text.split('\n')
        
        # Show first 50 lines
        for i, line in enumerate(lines[:50]):
            if line.strip():
                print(f"{i:3}: {line}")
        
        # Look for date patterns
        print("\nSearching for date patterns...")
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"Found dates with pattern {pattern}: {matches[:5]}")
        
        # Look for amount patterns
        print("\nSearching for amount patterns...")
        amount_patterns = [
            r'[\d,]+\.\d{2}',
            r'[\d.]+,\d{2}',
            r'\$[\d,]+\.\d{2}',
            r'€[\d.]+,\d{2}',
            r'£[\d,]+\.\d{2}'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"Found amounts with pattern {pattern}: {matches[:10]}")