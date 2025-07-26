#!/usr/bin/env python3
"""Analyze exact column positions in the PDF"""

import subprocess
import re

pdf_path = '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf'

# Get the PDF text with layout
result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                        capture_output=True, text=True)

lines = result.stdout.split('\n')

# Find some key lines and show positions
print("Column position analysis:")
print("=" * 100)

for i, line in enumerate(lines):
    if 'money' in line.lower() and 'out' in line.lower():
        print(f"Header line {i}: {line}")
        print("Position markers:")
        print("0123456789" * 10)
        print(line)
        print()
        
    if '4 February' in line and 'YourJob' in line:
        print(f"Line {i}: 4 February deposit")
        print("Position markers:")
        print("0123456789" * 10)
        print(line)
        # Find position of 2,575.00
        import re
        match = re.search(r'2,575\.00', line)
        if match:
            print(f"Amount '2,575.00' found at position: {match.start()}")
        print()
        
    if '1 February' in line and 'Card payment' in line:
        print(f"Line {i}: 1 February withdrawal")
        print("Position markers:")
        print("0123456789" * 10)
        print(line)
        # Find position of 24.50
        match = re.search(r'24\.50', line)
        if match:
            print(f"Amount '24.50' found at position: {match.start()}")
        print()