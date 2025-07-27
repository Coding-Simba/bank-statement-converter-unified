#!/usr/bin/env python3
"""Test Discover statement parser"""

from backend.discover_parser import parse_discover

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf'

print("Testing Discover statement...")
print("=" * 60)

transactions = parse_discover(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
credits = [t for t in transactions if t.get('amount', 0) > 0]
debits = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Credits (payments): {len(credits)}")
print(f"Debits (purchases): {len(debits)}")

# Show first few of each type
if transactions:
    print("\nFirst 5 debits (purchases):")
    debits_shown = 0
    for trans in transactions:
        if trans.get('amount', 0) < 0 and debits_shown < 5:
            print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:50]}... ${trans['amount']:.2f}")
            debits_shown += 1
    
    print("\nFirst 5 credits (payments):")
    credits_shown = 0
    for trans in transactions:
        if trans.get('amount', 0) > 0 and credits_shown < 5:
            print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:50]}... ${trans['amount']:.2f}")
            credits_shown += 1

# Show transactions by category
print("\n\nTransactions by category:")
categories = {}
for trans in transactions:
    cat = trans.get('category', 'Uncategorized')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(trans)

for cat, trans_list in categories.items():
    print(f"\n{cat}: {len(trans_list)} transactions")