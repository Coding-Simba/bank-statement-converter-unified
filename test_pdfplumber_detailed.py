#!/usr/bin/env python3
"""Detailed analysis with pdfplumber to find hidden content"""

import pdfplumber
import re

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print(f"Analyzing PDF with pdfplumber...")
print("-" * 60)

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    print(f"Metadata: {pdf.metadata}")
    
    # Analyze each page
    for page_num, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*60}")
        
        # Get page dimensions
        print(f"Page size: {page.width} x {page.height}")
        
        # Extract all text
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print(f"\nTotal lines: {len(lines)}")
            
            # Show all non-empty lines
            print("\nAll text content:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"{i:3}: {line}")
        
        # Extract tables with different settings
        print("\n--- Tables with default settings ---")
        tables = page.extract_tables()
        if tables:
            for i, table in enumerate(tables):
                print(f"\nTable {i+1} ({len(table)} rows):")
                for row in table:
                    # Show rows that have any numeric content
                    if any(cell and any(c.isdigit() for c in str(cell)) for cell in row):
                        print(f"  {row}")
        
        # Try with different table settings
        print("\n--- Tables with explicit settings ---")
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "explicit_vertical_lines": [],
            "explicit_horizontal_lines": [],
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
            "text_tolerance": 3,
            "text_x_tolerance": None,
            "text_y_tolerance": None,
            "intersection_tolerance": 3,
            "intersection_x_tolerance": None,
            "intersection_y_tolerance": None,
        }
        
        tables2 = page.extract_tables(table_settings)
        if tables2 and tables2 != tables:
            for i, table in enumerate(tables2):
                print(f"\nTable {i+1} with custom settings ({len(table)} rows):")
                for row in table[:10]:  # First 10 rows
                    if any(cell for cell in row):
                        print(f"  {row}")
        
        # Check for any numeric patterns in the raw text
        if text:
            print("\n--- Looking for numeric patterns ---")
            # Find all sequences of numbers
            numbers = re.findall(r'\d+[.,]?\d*', text)
            if numbers:
                print(f"Found {len(numbers)} numeric values:")
                # Group and show unique patterns
                unique_nums = list(set(numbers))
                for num in sorted(unique_nums)[:20]:  # Show first 20 unique
                    if len(num) > 2:  # Skip single digits
                        count = numbers.count(num)
                        print(f"  '{num}' (appears {count} times)")
        
        # Check page objects
        print(f"\n--- Page objects ---")
        print(f"Total chars: {len(page.chars) if hasattr(page, 'chars') else 'N/A'}")
        print(f"Total words: {len(page.extract_words()) if hasattr(page, 'extract_words') else 'N/A'}")
        
        # Sample some words
        words = page.extract_words()
        if words:
            print("\nSample words with positions:")
            for word in words[:20]:
                print(f"  '{word['text']}' at ({word['x0']:.1f}, {word['top']:.1f})")