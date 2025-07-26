#!/usr/bin/env python3
"""Test the parser with different text formats to show what it can handle"""

import sys
sys.path.append('.')
from backend.universal_parser import extract_transactions_from_text

# Test different bank statement formats
test_formats = [
    # Format 1: US Bank style
    """
    Date        Description                     Amount      Balance
    01/15/2024  WALMART STORE #1234            -45.67      1,234.56
    01/16/2024  DIRECT DEPOSIT PAYROLL       2,500.00      3,734.56
    01/17/2024  NETFLIX.COM                    -15.99      3,718.57
    """,
    
    # Format 2: European style with different separators
    """
    Datum       Omschrijving                    Bedrag      Saldo
    15-01-2024  ALBERT HEIJN 1234             -45,67 EUR   1.234,56 EUR
    16-01-2024  SALARIS JANUARI              2.500,00 EUR  3.734,56 EUR
    17-01-2024  NETFLIX SUBSCRIPTION          -15,99 EUR   3.718,57 EUR
    """,
    
    # Format 3: Credit card style
    """
    Transaction Date    Description                         Amount
    Jan 15, 2024       AMAZON.COM*12345                    $123.45
    Jan 16, 2024       SHELL GAS STATION                    $67.89
    Jan 17, 2024       RESTAURANT XYZ                       $45.00
    """,
    
    # Format 4: Debit/Credit columns
    """
    Date       Reference   Description          Debit    Credit   Balance
    15/01/24   TXN001     ATM WITHDRAWAL       100.00            900.00
    16/01/24   TXN002     SALARY PAYMENT                1500.00  2400.00
    17/01/24   TXN003     UTILITY BILL          75.50            2324.50
    """,
]

print("Testing parser with different bank statement formats:")
print("=" * 70)

for i, test_text in enumerate(test_formats, 1):
    print(f"\nFormat {i}:")
    print("-" * 50)
    print(test_text.strip())
    print("\nExtracted transactions:")
    
    transactions = extract_transactions_from_text(test_text)
    
    if transactions:
        for trans in transactions:
            date_str = trans['date'].strftime('%Y-%m-%d') if trans.get('date') else 'No date'
            desc = trans.get('description', 'No description')
            amount = trans.get('amount', 0)
            print(f"  - {date_str}: {desc} | ${amount:.2f}")
    else:
        print("  No transactions extracted")
    
    print(f"  Total: {len(transactions)} transactions found")

# Show what patterns the parser looks for
print("\n" + "=" * 70)
print("PARSER CAPABILITIES:")
print("=" * 70)
print("""
1. Date formats recognized:
   - 01/15/2024 (MM/DD/YYYY)
   - 15/01/2024 (DD/MM/YYYY)
   - 2024-01-15 (YYYY-MM-DD)
   - 15-Jan-2024
   - Jan 15, 2024

2. Amount formats:
   - 1,234.56 (US format)
   - 1.234,56 (European format)
   - $123.45 (with currency symbol)
   - -123.45 (negative)
   - (123.45) (negative in parentheses)

3. Transaction patterns:
   - Table-based layouts
   - Date + Description + Amount
   - Debit/Credit columns
   - Various delimiters (spaces, tabs, pipes)
""")