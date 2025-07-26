#!/usr/bin/env python3
"""Check page 2 in detail - it has a 22-row table"""

import pdfplumber

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

with pdfplumber.open(pdf_path) as pdf:
    if len(pdf.pages) >= 2:
        page = pdf.pages[1]  # Page 2 (0-indexed)
        
        print("Page 2 Analysis:")
        print("-" * 60)
        
        # Extract all tables
        tables = page.extract_tables()
        
        print(f"Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            print(f"\n--- Table {i+1} ({len(table)} rows) ---")
            
            # Show all rows
            for row_idx, row in enumerate(table):
                # Convert None to empty string for display
                row_display = [str(cell) if cell is not None else "" for cell in row]
                print(f"Row {row_idx}: {row_display}")
                
                # Check if this row has transaction-like data
                row_str = ' '.join(row_display)
                if any(char.isdigit() for char in row_str) and len(row_str.strip()) > 5:
                    print(f"  → Contains numeric data")
        
        # Also extract raw text
        print("\n\nRaw text from page 2:")
        print("-" * 60)
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"{i:3}: {line}")
        
        # Check for images
        print(f"\n\nPage contains images: {len(page.images) if hasattr(page, 'images') else 'Unknown'}")
        if hasattr(page, 'images') and page.images:
            for img in page.images:
                print(f"  Image: {img}")