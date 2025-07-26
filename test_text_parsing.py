#!/usr/bin/env python3
"""Simple test of text parsing functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions directly
from backend.universal_parser import extract_transactions_from_text

# Test US Bank format
print("Testing US Bank format (MM/DD/YYYY):")
text1 = """01/15/2024    STARBUCKS STORE #123    -5.75
01/16/2024    DEPOSIT FROM EMPLOYER    +2500.00"""

transactions = extract_transactions_from_text(text1)
print(f"Found {len(transactions)} transactions")
for t in transactions:
    print(f"  {t['date_string']} - {t['description']} - ${t['amount']}")

# Test European format
print("\nTesting European format:")
text2 = """15-01-2024    Supermarkt Albert Heijn    €48,73
16-01-2024    Salaris werkgever    €2.500,00"""

transactions = extract_transactions_from_text(text2)
print(f"Found {len(transactions)} transactions")
for t in transactions:
    print(f"  {t['date_string']} - {t['description']} - €{t['amount']}")