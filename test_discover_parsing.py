#!/usr/bin/env python3
"""Test Discover parsing logic"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.discover_parser import DiscoverParser

# Test the pattern matching
parser = DiscoverParser()
year = 2022

test_lines = [
    "Oct 13 Oct 13 INTERNET PAYMENT - THANK YOU -80.00",
    "Oct 23 Oct 23 INTERNET PAYMENT - THANK YOU -164.35",
    "Sep 23 Sep 23 NUMARK TOBACCO PRODUCT 855-MARKTEN 6.35",
    "Oct 3 Oct 3 WAL-MART SC - #0571 GEORGETOWN KY 82.95",
    "Sep 20 Sep 20 WENDY'S 810 GEORGETOWN KY 2.00"
]

print("Testing Discover transaction parsing:")
for line in test_lines:
    print(f"\nLine: {line}")
    
    # Test pattern matching
    import re
    pattern = r'^([A-Za-z]{3}\s+\d{1,2})\s+[A-Za-z]{3}\s+\d{1,2}\s+(.+?)\s+([-]?[\d,]+\.?\d*)\s*$'
    match = re.match(pattern, line)
    
    if match:
        date_str = match.group(1)
        description = match.group(2)
        amount_str = match.group(3)
        
        print(f"  Date: '{date_str}'")
        print(f"  Description: '{description}'")
        print(f"  Amount: '{amount_str}'")
        
        # Try parsing date
        date = parser.parse_date(date_str, year)
        print(f"  Parsed date: {date}")
        
        # Try parsing amount
        amount = parser.extract_amount(amount_str)
        print(f"  Parsed amount: {amount}")
    else:
        print("  No match!")