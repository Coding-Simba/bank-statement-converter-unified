#!/usr/bin/env python3
"""Debug transaction extraction to understand the amount parsing issue"""

from backend.universal_parser import parse_universal_pdf, extract_amount
import os

# Test PDFs with issues
test_pdfs = [
    './uploads/11a56e83-e80a-4725-adf3-e33f19ee8f36.pdf',  # merged_statements_2025-07-26.pdf
    './failed_pdfs/20250727_005210_a17b26f9_Bank Statement Example Final.pdf',
    './uploads/ce491615-a3b4-444e-a079-4dfdb82819bd.pdf',  # dummy_statement.pdf
]

def debug_extract_amount():
    """Test the extract_amount function with various formats"""
    print("=== TESTING extract_amount FUNCTION ===")
    test_amounts = [
        "24.50",
        "-24.50",
        "(24.50)",
        "$24.50",
        "$-24.50",
        "($24.50)",
        "39975.50",
        "$39,975.50",
        "Card payment - High St Petrol Station 24.50",
        "24.50 DR",
        "24.50 CR",
        "1,234.56",
        "-1,234.56",
        "(1,234.56)",
    ]
    
    for amount_str in test_amounts:
        result = extract_amount(amount_str)
        print(f"'{amount_str}' -> {result}")
    print()

def debug_pdf_extraction(pdf_path):
    """Debug extraction from a specific PDF"""
    print(f"\n=== DEBUGGING PDF: {pdf_path} ===")
    
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return
    
    # Try to extract raw text first to see the actual content
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Number of pages: {len(pdf_reader.pages)}")
            
            # Show first page text
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                print("\n--- FIRST PAGE RAW TEXT (first 1000 chars) ---")
                print(first_page_text[:1000])
                print("...")
    except Exception as e:
        print(f"Error reading PDF: {e}")
    
    # Now try parsing
    try:
        transactions = parse_universal_pdf(pdf_path)
        print(f"\nTotal transactions extracted: {len(transactions)}")
        
        # Analyze transactions
        deposits = [t for t in transactions if t.get('amount', 0) > 0]
        withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
        
        print(f"Deposits: {len(deposits)}, Withdrawals: {len(withdrawals)}")
        
        # Show first few transactions with full details
        print("\n--- FIRST 5 TRANSACTIONS (DETAILED) ---")
        for i, trans in enumerate(transactions[:5]):
            print(f"\nTransaction {i+1}:")
            print(f"  Date: {trans.get('date_string', 'N/A')}")
            print(f"  Description: {trans.get('description', 'N/A')}")
            print(f"  Amount String: {trans.get('amount_string', 'N/A')}")
            print(f"  Amount Parsed: {trans.get('amount', 'N/A')}")
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()

# Run debug tests
debug_extract_amount()

for pdf_path in test_pdfs:
    debug_pdf_extraction(pdf_path)