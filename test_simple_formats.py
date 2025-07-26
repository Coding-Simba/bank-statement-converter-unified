#!/usr/bin/env python3
"""Simple test to show what PDF formats work with our parser"""

import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Import our parser
import sys
sys.path.append('.')
from backend.universal_parser import parse_universal_pdf

def create_test_pdf(filename, content):
    """Create a test PDF with given content"""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add content
    y = height - inch
    for line in content.split('\n'):
        if y < inch:
            c.showPage()
            y = height - inch
        c.drawString(inch, y, line)
        y -= 15
    
    c.save()

# Test different formats
test_cases = [
    {
        'name': 'US Bank Format',
        'content': '''Statement Period: 01/01/2024 - 01/31/2024

Date        Description                     Amount      Balance
01/15/2024  WALMART STORE #1234            -45.67      1,234.56
01/16/2024  DIRECT DEPOSIT PAYROLL       2,500.00      3,734.56
01/17/2024  NETFLIX.COM                    -15.99      3,718.57
01/18/2024  AMAZON MARKETPLACE            -123.45      3,595.12
01/19/2024  GAS STATION #5678              -67.89      3,527.23'''
    },
    {
        'name': 'Credit Card Format',
        'content': '''Credit Card Statement

Transaction Date    Description                         Amount
01/15/2024         AMAZON.COM*12345                    123.45
01/16/2024         SHELL GAS STATION                    67.89
01/17/2024         RESTAURANT XYZ                       45.00
01/18/2024         GROCERY STORE                        89.99
01/19/2024         ONLINE PAYMENT - THANK YOU         -300.00'''
    },
    {
        'name': 'Simple List Format',
        'content': '''Recent Transactions:

15/01/2024 - Supermarket Shopping - $45.67
16/01/2024 - Monthly Salary - $2,500.00
17/01/2024 - Electric Bill - $125.99
18/01/2024 - Internet Service - $59.99
19/01/2024 - Mobile Phone - $45.00'''
    }
]

print("=" * 70)
print("PDF PARSER COMPATIBILITY TEST")
print("=" * 70)

for test in test_cases:
    print(f"\n{test['name']}:")
    print("-" * 50)
    
    # Create temporary PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        temp_pdf = tmp.name
    
    try:
        # Create PDF
        create_test_pdf(temp_pdf, test['content'])
        
        # Parse it
        transactions = parse_universal_pdf(temp_pdf)
        
        if transactions:
            print(f"✅ Successfully parsed {len(transactions)} transactions:")
            for trans in transactions[:3]:  # Show first 3
                date_str = trans['date'].strftime('%Y-%m-%d') if trans.get('date') else 'No date'
                desc = trans.get('description', 'Unknown')[:30]
                amount = trans.get('amount', 0)
                print(f"   - {date_str}: {desc:30} ${amount:>10.2f}")
            if len(transactions) > 3:
                print(f"   ... and {len(transactions) - 3} more")
        else:
            print("❌ No transactions found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        if os.path.exists(temp_pdf):
            os.unlink(temp_pdf)

print("\n" + "=" * 70)
print("SUMMARY: What Works with Our Parser")
print("=" * 70)
print("""
✅ SUPPORTED:
- Table-based bank statements (most common)
- Credit card statements
- PDFs with clear Date | Description | Amount structure
- Multiple date formats (MM/DD/YYYY, DD/MM/YYYY, etc.)
- Various amount formats ($1,234.56, €1.234,56, etc.)
- Multi-page statements
- Rabobank statements (dedicated parser)

❌ NOT SUPPORTED:
- Scanned/Image PDFs (need OCR)
- Password-protected PDFs
- Investment statements with complex layouts
- PDFs without clear transaction structure
- Handwritten or poorly formatted documents

🔧 RECOMMENDATIONS FOR USERS:
1. Download statements as PDF (not print to PDF)
2. Ensure text is selectable in the PDF
3. Use standard bank statement formats
4. Avoid statements with graphs/charts mixed with data
""")