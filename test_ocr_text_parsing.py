#!/usr/bin/env python3
"""Test OCR text parsing directly"""

from backend.advanced_ocr_parser import parse_multiline_transactions

# The OCR text from page 2
ocr_text = """Bankof America

ABELNEWTON | Account # 333 44445555 | May 1, 2019 to May 31, 2019

Deposits and other additions

Date Description Amount
01/05/19 Deposit 50.00
11/05/19 Counter credit 50.00
19/05/19 SEVEN ELEVEN SALARY MAY 50.00
29/05/2019 Deposit 50.00

Total deposits and other additions $200.00

Withdrawals and other subtractions
Date Description Amount

01/05/19 ATM Withdrawal -25.00
06/05/19 debit card payment 4747 STARBUCKS PLAZA BOTERO BT 1234567654532109875322 -10.49
11/05/19 ATM Withdrawal -25.00
17/05/19 Checkcard 2201 TOYSRUS 333-267-6947 BA 123456789012345 -89.51
22/05/19 Checkcard 2202 MACDONALDS 678-344-6314 BO 1338635736666635790652 -32.81
30/05/19 Payment Debit Card 4747 UNIVERSITY OF BOGOTA BO 1234567654532109875322 -17.19

Total withdrawals and other subtractions -$200.00

Page 2 of 2"""

print("=== TESTING OCR TEXT PARSING ===")
print("=" * 60)

transactions = parse_multiline_transactions(ocr_text)

print(f"\nFound {len(transactions)} transactions")

# Group by type
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"\nDeposits: {len(deposits)}")
for trans in deposits:
    print(f"  {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")

print(f"\nWithdrawals: {len(withdrawals)}")
for trans in withdrawals:
    print(f"  {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")

print(f"\nTotal deposits: ${sum(t['amount'] for t in deposits):.2f}")
print(f"Total withdrawals: ${sum(t['amount'] for t in withdrawals):.2f}")