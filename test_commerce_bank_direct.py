#!/usr/bin/env python3
"""Test Commerce Bank parser directly"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract
from backend.commerce_bank_parser import parse_commerce_bank_text, extract_commerce_bank_summary

pdf_path = "/Users/MAC/Downloads/Shot-2024-09-14-at-19.24.43@2x.jpg.pdf"

print(f"Testing Commerce Bank parser on: {pdf_path}")
print("=" * 70)

# Convert PDF to text
images = convert_from_path(pdf_path, dpi=300)
text = ''
for image in images:
    text += pytesseract.image_to_string(image)

# Extract summary
print("\nStatement Summary:")
print("-" * 30)
summary = extract_commerce_bank_summary(text)
for key, value in summary.items():
    print(f"{key}: ${value:,.2f}")

# Parse transactions
print("\nParsing transactions...")
transactions = parse_commerce_bank_text(text)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    # Group by type
    deposits = [t for t in transactions if t.get('amount', 0) > 0]
    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
    
    print(f"\nDeposits: {len(deposits)}")
    print(f"Withdrawals: {len(withdrawals)}")
    
    if deposits:
        print("\n--- Deposits ---")
        for trans in deposits:
            date_str = trans.get('date_string', 'No date')
            desc = trans.get('description', 'No description')[:50]
            amount = trans.get('amount', 0)
            print(f"{date_str:8} | {desc:50} | ${amount:>10.2f}")
    
    if withdrawals:
        print("\n--- Withdrawals ---")
        for trans in withdrawals:
            date_str = trans.get('date_string', 'No date')
            desc = trans.get('description', 'No description')[:50]
            amount = trans.get('amount', 0)
            print(f"{date_str:8} | {desc:50} | ${amount:>10.2f}")
    
    # Summary
    total_credits = sum(t.get('amount', 0) for t in deposits)
    total_debits = sum(t.get('amount', 0) for t in withdrawals)
    
    print(f"\n--- Totals ---")
    print(f"Total deposits: ${total_credits:,.2f}")
    print(f"Total withdrawals: ${total_debits:,.2f}")
    print(f"Net: ${total_credits + total_debits:,.2f}")