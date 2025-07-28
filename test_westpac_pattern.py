#!/usr/bin/env python3
"""Test Westpac pattern matching"""

import re

# Test data from the PDF
lines = [
    'TRANSFER (Internet Banking) Account Replenishment (John Citizen',
    '2/11/2022 1,136.00 USD 1136.00',
    '2050558317341020)',
    'TRANSFER (Internet Banking) Account Replenishment (John Citizen', 
    '2/11/2022 55.00 USD -55.00',
    '2050558317341020)',
    'TRANSFER (Internet Banking) Account Replenishment (John Citizen',
    '2/11/2022 55.00 USD -55.00', 
    '2050558317341020)',
    'TRANSFER (Internet Banking) Account Replenishment (John Citizen',
    '2/11/2022 55.00 USD 55.00',
    '2050558317341020)',
    '1081.00 Balance – Closing balance of the account at the end of the day',
    '2/12/2022 1,081.06 USD -1081.06 Cash Out Order JOHN CITIZEN 000308536'
]

# Pattern from Westpac parser
pattern = r'^(\d{1,2}/\d{1,2}/\d{4})\s+([\d,]+\.?\d*)\s+(\w+)\s+([\d,.-]+)'

print("Testing Westpac pattern matching:")
print("=" * 60)

for i, line in enumerate(lines):
    match = re.match(pattern, line)
    if match:
        print(f"\nLine {i}: {line}")
        print(f"  Date: {match.group(1)}")
        print(f"  Amount: {match.group(2)}")
        print(f"  Currency: {match.group(3)}")
        print(f"  In/Out: {match.group(4)}")
        
        # Check remaining text
        if len(match.group(0)) < len(line):
            remaining = line[match.end():].strip()
            print(f"  Remaining text: {remaining}")
            
        # Check previous line for description
        if i > 0:
            print(f"  Previous line: {lines[i-1]}")

print(f"\n\nTotal matches found: {sum(1 for line in lines if re.match(pattern, line))}")