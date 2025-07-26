#!/usr/bin/env python3
"""Test OCR parsing on the extracted text from dummy PDF"""

import sys
sys.path.append('.')

from backend.ocr_parser import parse_ocr_text

# Sample text from the dummy PDF
ocr_text = """Activity for Relationship Checking - Account #12345678

Account Transactions by date with daily balance information

Description Credit Balance
POS PURCHASE 65.73
PREAUTHORIZED CREDIT 763.01 828.74
POS PURCHASE 817.06
CHECK 1234 807.08
POS PURCHASE 781.58

Account Transactions by type with detailed description

Deposits and Other Credits

Date Description Amount
10/03 PREAUTHORIZED CREDIT PAYROLL0987654678990 763.01
10/16 PREAUTHORIZED CREDIT USTREASURY 310 SOC SEC 763.01
10/31 PREAUTHORIZED CREDIT DEPOSIT TERMINAL 350.00
11/09 INTEREST CREDIT 0.26

Withdrawals and Other Debits

Date Description Amount
10/02 POS PURCHASE WAL-MART#3492 WICHITA KS 65.73
10/04 POS PURCHASE PLAYERS SPORTS BAR AND GRILL 11.68
10/05 POS PURCHASE KWAN COURT WICHITA KS 9.98"""

print("Testing OCR text parsing...")
print("-" * 70)

transactions = parse_ocr_text(ocr_text)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    for i, trans in enumerate(transactions):
        print(f"\n{i+1}. Transaction:")
        for key, value in trans.items():
            print(f"   {key}: {value}")
else:
    print("\nNo transactions found - let's debug...")
    
    # Check what patterns would match
    import re
    lines = ocr_text.split('\n')
    
    # Look for lines with dates
    date_pattern = r'(\d{1,2}/\d{1,2})'
    
    print("\nLines with dates:")
    for line in lines:
        if re.search(date_pattern, line):
            print(f"  {line}")
            
    print("\nTrying simpler patterns...")
    # Pattern for MM/DD at start of line
    simple_pattern = r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$'
    
    for line in lines:
        match = re.match(simple_pattern, line)
        if match:
            print(f"\nMatched: {line}")
            print(f"  Date: {match.group(1)}")
            print(f"  Description: {match.group(2)}")
            print(f"  Amount: {match.group(3)}")