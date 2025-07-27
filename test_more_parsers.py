#!/usr/bin/env python3
"""Test more parsers directly"""

from backend.walmart_parser import parse_walmart
from backend.woodforest_parser import parse_woodforest
from backend.suntrust_parser import parse_suntrust
from backend.netspend_parser import parse_netspend
from backend.dummy_pdf_parser import parse_dummy_pdf

test_cases = [
    ('Walmart', parse_walmart, '/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf', 16),
    ('Woodforest', parse_woodforest, '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf', 51),
    ('SunTrust', parse_suntrust, '/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf', 9),
    ('Netspend', parse_netspend, '/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf', 24),
    ('Dummy', parse_dummy_pdf, '/Users/MAC/Desktop/pdfs/dummy_statement.pdf', 12)
]

print("MORE PARSER TESTS")
print("=" * 60)

for name, parser_func, path, expected in test_cases:
    print(f"\nTesting {name} parser...")
    try:
        transactions = parser_func(path)
        count = len(transactions)
        
        if count == expected:
            print(f"✅ PASS: Found {count} transactions")
        else:
            print(f"⚠️  WARN: Found {count} transactions (expected {expected})")
            
        # Count deposits/withdrawals
        deposits = len([t for t in transactions if t.get('amount', 0) > 0])
        withdrawals = len([t for t in transactions if t.get('amount', 0) < 0])
        print(f"   Deposits: {deposits}, Withdrawals: {withdrawals}")
            
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")

print("\n" + "=" * 60)