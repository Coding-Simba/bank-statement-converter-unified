#!/usr/bin/env python3
"""Debug Westpac parsing logic"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.westpac_parser import WestpacParser
import re

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"
parser = WestpacParser()

# Extract lines
lines = parser.extract_text_lines(pdf_path)
year = parser.detect_year_from_pdf(pdf_path)

print("=== Debugging parse_westpac_text ===")

# Manually run through the parsing logic
transactions = []
pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(\w+)\s+([\d,.-]+)'

for i, line in enumerate(lines):
    if not line.strip():
        continue
    
    match = re.match(pattern, line)
    if match:
        print(f"\nProcessing line {i}: {line[:60]}...")
        
        date_str = match.group(1)
        amount_str = match.group(2)
        currency = match.group(3)
        in_out = match.group(4)
        
        print(f"  Date: {date_str}")
        print(f"  Amount: {amount_str}")
        print(f"  Currency: {currency}")
        print(f"  In/Out: {in_out}")
        
        # Parse date
        date = parser.parse_date(date_str, year)
        print(f"  Parsed date: {date}")
        
        # Parse amount
        amount = parser.extract_amount(amount_str)
        print(f"  Parsed amount: {amount}")
        
        if date and amount is not None:
            # Get description from previous line
            description = ""
            if i > 0:
                prev_line = lines[i-1].strip()
                if 'TRANSFER' in prev_line or 'Cash Out' in prev_line or len(prev_line) > 10:
                    description = prev_line
                    
            # Check remaining text
            if len(match.group(0)) < len(line):
                remaining = line[match.end():].strip()
                if remaining:
                    description = remaining if not description else description + ' ' + remaining
                    
            print(f"  Description: {description}")
            
            transactions.append({
                'date': date,
                'amount': amount,
                'description': description
            })
            print(f"  -> Transaction added! Total: {len(transactions)}")
        else:
            print(f"  -> SKIPPED: date={date}, amount={amount}")

print(f"\n\nTotal transactions found: {len(transactions)}")