#!/usr/bin/env python3
"""Test OCR parser directly"""

import sys
sys.path.append('.')

from backend.ocr_parser import parse_ocr_text

# Sample OCR text
text = """FIRST NATIONAL BANK

Account Statement

Period: 01/01/2024 - 01/31/2024

Date Description Amount Balance
01/05/2024 WALMART SUPERCENTER #4521 -87.43 4,125.67
01/08/2024 DIRECT DEPOSIT - EMPLOYER 2,845.00 6,970.67
01/10/2024 AMAZON.COM PURCHASE -156.89 6,813.78
01/12/2024 STARBUCKS COFFEE #1234 -12.45 6,801.33
01/15/2024 UTILITY PAYMENT - ELECTRIC -234.56 6,566.77
01/18/2024 ATM WITHDRAWAL -200.00 6,366.77
01/22/2024 NETFLIX SUBSCRIPTION -15.99 6,350.78
01/25/2024 GROCERY STORE #5678 -145.23 6,205.55
01/28/2024 GAS STATION #9012 -67.89 6,137.66
01/30/2024 RESTAURANT DINING -89.50 6,048.16"""

print("Testing OCR text parsing...")
print("-" * 50)

transactions = parse_ocr_text(text)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    for trans in transactions:
        print(f"\nTransaction:")
        for key, value in trans.items():
            print(f"  {key}: {value}")
else:
    print("\nDebugging - checking each line:")
    lines = text.split('\n')
    
    import re
    patterns = [
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+?)\s+(-?[\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+?)\s+(-?[\d,]+\.?\d*)',
    ]
    
    for i, line in enumerate(lines):
        if '2024' in line and len(line) > 20:
            print(f"\nLine {i}: {line}")
            for j, pattern in enumerate(patterns):
                match = re.search(pattern, line)
                if match:
                    print(f"  Pattern {j} matched: {match.groups()}")
                else:
                    print(f"  Pattern {j}: No match")