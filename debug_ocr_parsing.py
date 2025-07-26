#!/usr/bin/env python3
"""Debug OCR parsing to understand why deposits aren't captured"""

import re

# Sample deposit line from OCR
test_lines = [
    "01/05/19 Deposit 50.00",
    "11/05/19 Counter credit 50.00",
    "19/05/19 SEVEN ELEVEN SALARY MAY 50.00",
    "29/05/2019 Deposit 50.00"
]

print("=== DEBUGGING DEPOSIT PARSING ===")
print("=" * 60)

# Test date regex
date_pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)'

for line in test_lines:
    print(f"\nTesting line: '{line}'")
    
    # Test date match
    date_match = re.match(date_pattern, line)
    if date_match:
        print(f"  Date match: '{date_match.group(1)}'")
        print(f"  Rest of line: '{date_match.group(2)}'")
        
        # Test amount patterns
        rest = date_match.group(2)
        
        # Pattern 1: Current pattern
        pattern1 = r'([-]?\$?[\d,]+\.?\d+)\s*$'
        match1 = re.search(pattern1, rest)
        print(f"  Pattern 1 match: {match1.group(1) if match1 else 'NO MATCH'}")
        
        # Pattern 2: More flexible
        pattern2 = r'(\d+\.?\d*)\s*$'
        match2 = re.search(pattern2, rest)
        print(f"  Pattern 2 match: {match2.group(1) if match2 else 'NO MATCH'}")
        
        # Pattern 3: Look for space then number
        pattern3 = r'\s+([\d,]+\.?\d*)\s*$'
        match3 = re.search(pattern3, rest)
        print(f"  Pattern 3 match: {match3.group(1) if match3 else 'NO MATCH'}")
        
        if match3:
            desc = rest[:match3.start()].strip()
            print(f"  Description would be: '{desc}'")