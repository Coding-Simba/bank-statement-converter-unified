#!/usr/bin/env python3
"""Test pdfplumber directly on all PDFs to assess its capability"""
import sys
sys.path.insert(0, '.')
from backend.pdfplumber_parser import parse_with_pdfplumber
import os

def test_pdf(pdf_path):
    """Test a single PDF with pdfplumber"""
    print(f"\nTesting: {os.path.basename(pdf_path)}")
    print("="*60)
    
    if not os.path.exists(pdf_path):
        print("❌ File not found!")
        return
    
    try:
        transactions = parse_with_pdfplumber(pdf_path)
        print(f"✓ Found {len(transactions)} transactions")
        
        if transactions:
            print("\nFirst 5 transactions:")
            print(f"{'Date':<15} {'Description':<40} {'Amount':>12}")
            print("-" * 70)
            for trans in transactions[:5]:
                date = trans.get('date_string', 'No date')[:15]
                desc = (trans.get('description', 'No description') or 'No description')[:40]
                amount = trans.get('amount', 0) or 0
                print(f"{date:<15} {desc:<40} ${amount:>11.2f}")
        
        # Analyze quality
        issues = []
        for trans in transactions:
            # Check for phone numbers as dates
            date_str = trans.get('date_string', '')
            if date_str and '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    if int(parts[0]) == 1 and 70 <= int(parts[1]) <= 99:
                        issues.append(f"Phone number as date: {date_str}")
                        break
            
            # Check for unrealistic amounts
            amount = trans.get('amount', 0)
            if abs(amount) > 10000000:
                issues.append(f"Unrealistic amount: ${amount:,.2f}")
                break
        
        if issues:
            print("\n⚠️  Quality Issues:")
            for issue in issues:
                print(f"   - {issue}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test all PDFs"""
    pdf_files = [
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf",
        "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
        "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC (1).pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Bendigo Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf"
    ]
    
    success_count = 0
    total_trans = 0
    
    for pdf_path in pdf_files:
        try:
            trans = parse_with_pdfplumber(pdf_path)
            if trans:
                success_count += 1
                total_trans += len(trans)
        except:
            pass
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"PDFs with transactions: {success_count}/{len(pdf_files)}")
    print(f"Total transactions: {total_trans}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_pdf(sys.argv[1])
    else:
        main()