#!/usr/bin/env python3
"""Test advanced OCR parser"""

from backend.advanced_ocr_parser import parse_scanned_pdf_advanced
from backend.universal_parser import parse_universal_pdf

pdf_path = './test_example.pdf'

print("=== TESTING ADVANCED OCR PARSER ===")
print("=" * 60)

# Test direct OCR parsing
print("\n1. Direct Advanced OCR Parsing:")
print("-" * 40)
try:
    transactions = parse_scanned_pdf_advanced(pdf_path)
    print(f"Found {len(transactions)} transactions")
    
    for i, trans in enumerate(transactions):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'N/A')}")
        print(f"  Description: {trans.get('description', 'N/A')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Now test full parser with forced OCR
print("\n\n2. Universal Parser with Advanced OCR:")
print("-" * 40)

# Temporarily make the universal parser use advanced OCR for all pages
import backend.universal_parser as up

# Save original
original_is_scanned = up.is_scanned_pdf

# Force it to use OCR
up.is_scanned_pdf = lambda x: True

try:
    transactions = parse_universal_pdf(pdf_path)
    print(f"Found {len(transactions)} transactions with universal parser")
    
    # Group by amount type
    deposits = [t for t in transactions if t.get('amount', 0) > 0]
    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
    
    print(f"\nDeposits: {len(deposits)}")
    for trans in deposits:
        print(f"  {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
    
    print(f"\nWithdrawals: {len(withdrawals)}")
    for trans in withdrawals:
        print(f"  {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
        
finally:
    # Restore
    up.is_scanned_pdf = original_is_scanned