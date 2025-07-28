#!/usr/bin/env python3
"""Test Westpac date parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.westpac_parser import WestpacParser

parser = WestpacParser()

# Test date parsing
test_dates = ['2/11/2022', '2/14/2022', '2/17/2022', '14/2/2022', '20/2/2022']

print('Testing Westpac custom date parser:')
for date_str in test_dates:
    result = parser.parse_westpac_date(date_str, 2022)
    print(f'{date_str} -> {result}')