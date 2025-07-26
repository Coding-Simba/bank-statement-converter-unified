#!/usr/bin/env python3
"""Test with the split-by-date parser which should be the original working version"""

import sys
import os

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

# Now we can import rabobank_parser which split-by-date needs
try:
    # Import split-by-date module directly
    import importlib.util
    split_file = os.path.join(backend_path, 'split-by-date.py')
    spec = importlib.util.spec_from_file_location("split_by_date", split_file)
    split_module = importlib.util.module_from_spec(spec)
    sys.modules['split_by_date'] = split_module
    spec.loader.exec_module(split_module)
    
    extract_transactions_from_pdf = split_module.extract_transactions_from_pdf
except Exception as e:
    print(f"Error loading split-by-date module: {e}")
    sys.exit(1)

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print(f"Testing PDF with original parser from split-by-date.py")
print("-" * 60)

transactions = extract_transactions_from_pdf(pdf_path)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    print("\nFirst 10 transactions:")
    for i, trans in enumerate(transactions[:10]):
        print(f"\n{i+1}. Date: {trans.get('date')}")
        print(f"   Date string: {trans.get('date_string')}")
        print(f"   Description: {trans.get('description')}")
        print(f"   Amount: {trans.get('amount')}")
        print(f"   Amount string: {trans.get('amount_string')}")
else:
    print("\nNo transactions found!")
    print("\nLet's check what tabula sees in detail...")
    
    import tabula
    import pandas as pd
    
    # Read all tables with stream mode
    tables = tabula.read_pdf(pdf_path, pages='all', stream=True, pandas_options={'header': None})
    
    print(f"\nTabula found {len(tables)} tables total")
    
    for i, table in enumerate(tables):
        print(f"\n--- Table {i+1} ---")
        print(f"Shape: {table.shape}")
        print("\nFull content:")
        print(table)
        
        # Check each cell for potential transaction data
        for row_idx, row in table.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            # Look for rows that might have dates or amounts
            if any(char.isdigit() for char in row_str) and len(row_str) > 10:
                print(f"\nPotential data row {row_idx}: {row_str}")