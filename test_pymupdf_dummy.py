#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.pymupdf_column_parser import parse_with_pymupdf

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print(f"Testing PyMuPDF parser on {pdf}")
print("="*80)

try:
    transactions = parse_with_pymupdf(pdf)
    print(f"\n✓ Found {len(transactions)} transactions\n")
    
    if transactions:
        print(f"{'Date':<12} {'Description':<50} {'Amount':>12}")
        print("-" * 75)
        
        credits = []
        debits = []
        
        for t in transactions:
            date = t.get('date_string', 'No date')[:12]
            desc = (t.get('description', 'No description') or 'No description')[:50]
            amount = t.get('amount', 0) or 0
            print(f"{date:<12} {desc:<50} ${amount:>11.2f}")
            
            if amount > 0:
                credits.append(amount)
            else:
                debits.append(amount)
        
        print("-" * 75)
        total_credits = sum(credits)
        total_debits = sum(debits)
        net = total_credits + total_debits
        
        print(f"{'Total Credits':<63} ${total_credits:>11.2f}")
        print(f"{'Total Debits':<63} ${total_debits:>11.2f}")
        print(f"{'Net Total':<63} ${net:>11.2f}")
        
        print(f"\nExpected from actual PDF:")
        print(f"- 21 transactions")
        print(f"- Credits: $1,876.28")
        print(f"- Debits: $1,289.57")
        print(f"- Net: $586.71")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()