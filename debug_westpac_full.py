#!/usr/bin/env python3
"""Debug Westpac parser in detail"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.westpac_parser import WestpacParser
import re

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"
parser = WestpacParser()

print("=== Westpac Parser Debug ===")

# Extract using text method directly
lines = parser.extract_text_lines(pdf_path)
print(f"Total lines extracted: {len(lines)}")

# Extract year
year = parser.detect_year_from_pdf(pdf_path)
print(f"Detected year: {year}")

# Look for all lines with dates
date_pattern = r'^\d{1,2}/\d{1,2}/\d{4}'
date_lines = []
for i, line in enumerate(lines):
    if re.match(date_pattern, line):
        date_lines.append((i, line))
        
print(f"\nTotal lines with dates: {len(date_lines)}")
for idx, (line_num, line) in enumerate(date_lines[:10]):
    print(f"{idx+1}. Line {line_num}: {line[:80]}...")

# Parse using text method
print("\n=== Testing parse_westpac_text ===")
transactions = parser.parse_westpac_text(lines, year)
print(f"Transactions from text parsing: {len(transactions)}")

# Show unique dates
unique_dates = set()
for trans in transactions:
    unique_dates.add(trans['date_string'])
print(f"\nUnique transaction dates: {len(unique_dates)}")
for date in sorted(unique_dates):
    count = sum(1 for t in transactions if t['date_string'] == date)
    print(f"  {date}: {count} transactions")

# Also try table method
print("\n=== Testing parse_westpac_tables ===")
tables = parser.extract_table_data(pdf_path)
print(f"Tables found: {len(tables)}")
if tables:
    table_trans = parser.parse_westpac_tables(tables, year)
    print(f"Transactions from table parsing: {len(table_trans)}")
    
# Try parsing with pdfplumber directly
print("\n=== Direct PDF content analysis ===")
import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    lines_direct = text.split('\n')
    
    # Find all date patterns with the full Westpac format
    westpac_pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(\w+)\s+([\d,.-]+)'
    matches = []
    for i, line in enumerate(lines_direct):
        match = re.match(westpac_pattern, line)
        if match:
            matches.append((i, line, match.groups()))
            
    print(f"Direct pattern matches: {len(matches)}")
    for idx, (line_num, line, groups) in enumerate(matches[:5]):
        print(f"{idx+1}. Line {line_num}: {line[:60]}...")
        print(f"   Groups: {groups}")