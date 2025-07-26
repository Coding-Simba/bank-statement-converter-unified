#!/usr/bin/env python3
"""Quick test for Commonwealth Bank PDF"""

import subprocess

pdf_path = '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf'

# Just try pdftotext parsing
print("Testing Commonwealth Bank PDF with pdftotext...")

# Extract with pdftotext
result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                        capture_output=True, text=True)

lines = result.stdout.split('\n')

# Look for transaction lines
trans_count = 0
for line in lines:
    # Look for date pattern at start
    if line.strip() and line[:2].isdigit() and ' ' in line[2:5]:
        trans_count += 1
        if trans_count <= 5:
            print(f"Transaction {trans_count}: {line[:80]}...")

print(f"\nTotal potential transaction lines found: {trans_count}")