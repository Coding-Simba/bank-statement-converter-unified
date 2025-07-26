#!/usr/bin/env python3
"""Test parsing Commerce Bank format directly"""

import sys
sys.path.append('.')

from backend.ocr_parser import parse_ocr_text

# The OCR text from the Commerce Bank statement
text = """Commerce Bank

Member FOIC

1000 Walnut
Kansas City MO 64106-3686

Jane Customer
1234 Anywhere Dr.
Small Town, MO 12345-6789

Bank Statement

If you have any questions about your statement,
please call us at 816-234-2265

CONNECTIONS CHECKING Account # 000009752
Account Summary Account # 000009752
Beginning Balance on May 3, 2003
Deposits & Other Credits
ATM Withdrawals & Debits
VISA Check Card Purchases & Debits
Withdrawals & Other Debits
Checks Paid

Ending Balance on June 5, 2003
Deposits & Other Credits Account # 000009752
Description
Deposit Ref Nbr: 130012345
Total Deposits & Other Credits
ATM Withdrawals & Debits Account # 000009752

Description Tran Date

ATM Withdrawal
1000 Walnut St M119
Kansas City MO 00005678 05-18

Total ATM Withdrawals & Debits

Checks Paid Account # 000009752

Date Paid Check Number Amount Reference Number
05-12 1001 75.00 00012576589
05-18 1002 30.00 00036547854
05-24 1003 200.00 00094613547

Total Checks Paid

Primary Account Number:

Statement Date:
Page Number:

Date Credited

05-15

Date Paid

05-19

000009752

June 5, 2003
1

$7,126.11
+3,615.08
-20.00
-0.00
-0.00
-200.00

$10,521.19

Amount

$3,615.08

$3,615.08

Amount

$20.00

$20.00

$305.00"""

print("Testing OCR parser on Commerce Bank text...")
print("=" * 70)

transactions = parse_ocr_text(text)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    for i, trans in enumerate(transactions):
        print(f"\n{i+1}. Transaction:")
        for key, value in trans.items():
            print(f"   {key}: {value}")
else:
    print("\nNo transactions found!")