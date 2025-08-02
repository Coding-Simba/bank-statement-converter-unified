#!/usr/bin/env python3
"""
Test PDF Parser through Web API
===============================
"""

import requests
import os
import json
import time
from datetime import datetime

# Server URL
BASE_URL = "http://localhost:5001"

# Test PDFs
TEST_PDFS = [
    "/Users/MAC/Desktop/pdfs/1/Canada Scotiabank.pdf",
    "/Users/MAC/Desktop/pdfs/1/Australia NAB.pdf",
    "/Users/MAC/Desktop/pdfs/1/UK Santander.pdf",
    "/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf",
    "/Users/MAC/Desktop/pdfs/1/UK Monese Bank Statement.pdf",
    "/Users/MAC/Desktop/pdfs/1/UK Lloyds Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
    "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
    "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
    "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
    "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
    "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf"
]

def test_pdf_upload(pdf_path):
    """Test uploading a single PDF"""
    if not os.path.exists(pdf_path):
        return {
            'pdf': os.path.basename(pdf_path),
            'status': 'FILE_NOT_FOUND',
            'error': 'File does not exist'
        }
    
    try:
        # Prepare the file
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            
            # Make the request
            response = requests.post(f"{BASE_URL}/api/parse", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                transactions = data.get('data', [])
                return {
                    'pdf': os.path.basename(pdf_path),
                    'status': 'SUCCESS',
                    'transactions': len(transactions),
                    'sample': transactions[:3] if transactions else []
                }
            else:
                return {
                    'pdf': os.path.basename(pdf_path),
                    'status': 'API_ERROR',
                    'error': data.get('message', 'Unknown error')
                }
        else:
            return {
                'pdf': os.path.basename(pdf_path),
                'status': 'HTTP_ERROR',
                'error': f'HTTP {response.status_code}: {response.text[:200]}'
            }
    
    except Exception as e:
        return {
            'pdf': os.path.basename(pdf_path),
            'status': 'EXCEPTION',
            'error': str(e)
        }

def main():
    """Test all PDFs through the web API"""
    print("=" * 80)
    print("WEB API PDF PARSER TEST")
    print("=" * 80)
    print(f"Testing {len(TEST_PDFS)} PDFs through {BASE_URL}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding at", BASE_URL)
            print("Please start the server with: python server.py")
            return
    except:
        print("❌ Cannot connect to server at", BASE_URL)
        print("Please start the server with: python server.py")
        return
    
    results = []
    total_transactions = 0
    
    for pdf_path in TEST_PDFS:
        print(f"Testing: {os.path.basename(pdf_path)}")
        start_time = time.time()
        
        result = test_pdf_upload(pdf_path)
        elapsed = time.time() - start_time
        result['time'] = elapsed
        
        if result['status'] == 'SUCCESS':
            trans_count = result['transactions']
            total_transactions += trans_count
            print(f"✅ SUCCESS: {trans_count} transactions in {elapsed:.2f}s")
            
            # Show sample transactions
            if result['sample']:
                print("   Sample transactions:")
                for tx in result['sample']:
                    print(f"   - {tx.get('date_string', 'N/A')}: {tx.get('description', '')[:50]} ${tx.get('amount', 0)}")
        elif result['status'] == 'FILE_NOT_FOUND':
            print(f"❌ FILE NOT FOUND")
        else:
            print(f"❌ {result['status']}: {result.get('error', 'Unknown error')}")
        
        results.append(result)
        print()
        
        # Small delay to not overwhelm server
        time.sleep(0.1)
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    not_found = sum(1 for r in results if r['status'] == 'FILE_NOT_FOUND')
    errors = sum(1 for r in results if r['status'] in ['API_ERROR', 'HTTP_ERROR', 'EXCEPTION'])
    
    print(f"Total PDFs tested: {len(TEST_PDFS)}")
    print(f"Successful: {successful}")
    print(f"File not found: {not_found}")
    print(f"Errors: {errors}")
    print(f"Total transactions extracted: {total_transactions}")
    
    valid_tests = len(TEST_PDFS) - not_found
    if valid_tests > 0:
        success_rate = (successful / valid_tests) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
    
    # Save report
    report = {
        'test_date': datetime.now().isoformat(),
        'server_url': BASE_URL,
        'summary': {
            'total_pdfs': len(TEST_PDFS),
            'successful': successful,
            'not_found': not_found,
            'errors': errors,
            'total_transactions': total_transactions
        },
        'results': results
    }
    
    report_path = f'web_parser_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()