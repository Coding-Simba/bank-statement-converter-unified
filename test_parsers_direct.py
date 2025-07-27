#!/usr/bin/env python3
"""Test parsers directly without universal parser"""

from backend.boa_parser import parse_boa
from backend.paypal_parser import parse_paypal
from backend.monzo_parser import parse_monzo
from backend.commonwealth_simple_parser import parse_commonwealth_simple as parse_commonwealth
from backend.rbc_parser_v2 import parse_rbc_v2 as parse_rbc

test_cases = [
    ('Bank of America', parse_boa, '/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf', 69),
    ('PayPal', parse_paypal, '/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf', 10),
    ('Monzo', parse_monzo, '/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf', 28),
    ('Commonwealth', parse_commonwealth, '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf', 461),
    ('RBC', parse_rbc, '/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf', 50)
]

print("DIRECT PARSER TEST")
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