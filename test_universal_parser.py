#!/usr/bin/env python3
"""Test the universal PDF parser with different bank formats"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.universal_parser import parse_universal_pdf, extract_transactions_from_text

# Test with different bank statement formats
test_texts = [
    # US Bank format (MM/DD/YYYY)
    """
    01/15/2024    STARBUCKS STORE #123    -5.75
    01/16/2024    DEPOSIT FROM EMPLOYER    +2500.00
    01/17/2024    AMAZON.COM PURCHASE    -125.50
    01/18/2024    GAS STATION #456    -45.00
    """,
    
    # European format with comma decimals
    """
    15-01-2024    Supermarkt Albert Heijn    -48,73
    16-01-2024    Salaris werkgever    +2.500,00
    17-01-2024    Online aankoop Amazon    -125,50
    18-01-2024    Tankstation Shell    -45,00
    """,
    
    # UK format with month names
    """
    15 Jan 2024    Tesco Superstore    £48.73 DR
    16 Jan 2024    Salary Payment    £2,500.00 CR
    17 Jan 2024    Amazon Purchase    £125.50 DR
    18 Jan 2024    BP Petrol Station    £45.00 DR
    """,
    
    # Chase Bank format
    """
    Transaction Date    Description    Amount
    01/15/2024    WALMART #1234    ($48.73)
    01/16/2024    DIRECT DEPOSIT    $2,500.00
    01/17/2024    AMAZON MARKETPLACE    ($125.50)
    01/18/2024    SHELL OIL    ($45.00)
    """
]

print("Testing Universal PDF Parser with different bank formats")
print("=" * 60)

for i, text in enumerate(test_texts):
    print(f"\nTest {i+1}:")
    print("-" * 40)
    
    transactions = extract_transactions_from_text(text)
    
    if transactions:
        print(f"Found {len(transactions)} transactions:")
        for trans in transactions:
            date = trans['date'].strftime('%Y-%m-%d')
            desc = trans['description'][:30] + "..." if len(trans['description']) > 30 else trans['description']
            amount = trans['amount']
            print(f"  {date} | {desc:<33} | {amount:>10.2f}")
    else:
        print("No transactions found")

# Test with the Rabobank PDF
print("\n\nTesting with actual Rabobank PDF:")
print("=" * 60)

pdf_path = "/Users/MAC/Downloads/RA_A_NL13RABO0122118650_EUR_202506.pdf"
if os.path.exists(pdf_path):
    transactions = parse_universal_pdf(pdf_path)
    print(f"Found {len(transactions)} transactions")
    if transactions:
        print("\nFirst 5 transactions:")
        for trans in transactions[:5]:
            date = trans['date'].strftime('%Y-%m-%d')
            desc = trans['description'][:40] + "..." if len(trans['description']) > 40 else trans['description']
            amount = trans['amount']
            print(f"  {date} | {desc:<43} | {amount:>10.2f}")
else:
    print(f"PDF not found at {pdf_path}")