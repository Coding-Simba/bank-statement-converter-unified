#!/usr/bin/env python3
"""Check SunTrust transaction count"""

# Count the actual transaction lines from the debug output
transactions = [
    '04/04/2022 Petron - C5 Station 223.26',
    '04/09/2022 South Star Drug 313.39',
    '04/11/2022 Rosewood Condominum 582.96',
    '04/14/2022 Grab 125.00',
    '04/16/2022 Amazon 215.00',
    '04/20/2022 Alba International 656.86',
    '04/25/2022 Adobe Sales 246.00',
    '04/26/2022 St. Luke Medical Center 571.10',
    '04/29/2022 Hotel Sheraton (Las Vegas) 965.00'
]

print(f'Number of actual transactions: {len(transactions)}')
print('\nTransaction amounts:')
total = 0
for t in transactions:
    parts = t.split()
    amount = float(parts[-1])
    total += amount
    print(f'{t} -> ${amount}')
    
print(f'\nSum of transactions: ${total:.2f}')
print(f'Expected total: $3,898.57')
print(f'Match: {abs(total - 3898.57) < 0.01}')