#!/usr/bin/env python3
"""Test Westpac parser on all lines"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.westpac_parser import WestpacParser
import re

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"
parser = WestpacParser()

print("=== Testing Westpac pattern on ALL lines ===")

# Extract lines
lines = parser.extract_text_lines(pdf_path)
print(f"Total lines extracted: {len(lines)}")

# Test the pattern on ALL lines
pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(\w+)\s+([\d,.-]+)'
matches = 0
matched_lines = []

for i, line in enumerate(lines):
    match = re.match(pattern, line)
    if match:
        matches += 1
        matched_lines.append((i, line))
        print(f"Match {matches} - Line {i}: {line[:60]}...")

print(f"\nTotal pattern matches: {matches}")

# Now test the actual parse_westpac_text method
print("\n=== Testing parse_westpac_text method ===")
year = parser.detect_year_from_pdf(pdf_path)
transactions = parser.parse_westpac_text(lines, year)
print(f"Transactions extracted: {len(transactions)}")

# Compare what's missing
print("\n=== Debugging why some matches aren't becoming transactions ===")
for idx, (line_num, line) in enumerate(matched_lines):
    # Check if this line resulted in a transaction
    found = False
    for trans in transactions:
        if line_num < 30:  # Only check first few
            print(f"Line {line_num}: {line[:40]}... -> Transaction: {found}")