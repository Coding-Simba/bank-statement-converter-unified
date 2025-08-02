#!/usr/bin/env python3
"""Test script for the results overview feature"""

import os
import sys
import time
import requests
from pathlib import Path

# Add backend to path
sys.path.append('backend')

def test_single_pdf_conversion():
    """Test single PDF conversion and results display"""
    print("\n=== Testing Single PDF Conversion ===")
    
    # Find a test PDF
    test_pdf = None
    test_files = [
        "/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "test_files/standard.pdf"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            test_pdf = file
            break
    
    if not test_pdf:
        print("❌ No test PDF found")
        return False
    
    print(f"✓ Using test PDF: {test_pdf}")
    
    # Start local backend if not running
    try:
        response = requests.get("http://localhost:5000/health")
        print("✓ Backend is running")
    except:
        print("❌ Backend not running. Please start it with: cd backend && python main.py")
        return False
    
    # Test conversion endpoint
    print("\n1. Testing /api/convert endpoint...")
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        response = requests.post(
            "http://localhost:5000/api/convert",
            files=files
        )
    
    if response.status_code != 200:
        print(f"❌ Conversion failed: {response.status_code}")
        print(response.json())
        return False
    
    result = response.json()
    print(f"✓ Conversion successful")
    print(f"  Statement ID: {result['id']}")
    print(f"  Results URL: {result.get('results_url', 'NOT FOUND')}")
    
    if 'results_url' not in result:
        print("❌ results_url not in response")
        return False
    
    # Test transactions endpoint
    statement_id = result['id']
    print(f"\n2. Testing /api/statement/{statement_id}/transactions endpoint...")
    
    response = requests.get(
        f"http://localhost:5000/api/statement/{statement_id}/transactions",
        params={'page': 1, 'per_page': 50}
    )
    
    if response.status_code != 200:
        print(f"❌ Transactions fetch failed: {response.status_code}")
        print(response.json())
        return False
    
    data = response.json()
    print(f"✓ Transactions fetched successfully")
    print(f"  Total transactions: {data['total_count']}")
    print(f"  Bank detected: {data['statistics']['bank_name']}")
    print(f"  Date range: {data['statistics']['date_range']['start']} to {data['statistics']['date_range']['end']}")
    print(f"  Total pages: {data['pagination']['total_pages']}")
    
    # Show first few transactions
    if data['transactions']:
        print("\n  First 3 transactions:")
        for i, trans in enumerate(data['transactions'][:3]):
            print(f"    {i+1}. {trans['date']} | {trans['description'][:50]} | ${trans['amount']}")
    
    # Test markdown download
    print(f"\n3. Testing /api/statement/{statement_id}/download/markdown endpoint...")
    
    response = requests.get(
        f"http://localhost:5000/api/statement/{statement_id}/download/markdown"
    )
    
    if response.status_code != 200:
        print(f"❌ Markdown download failed: {response.status_code}")
        return False
    
    print(f"✓ Markdown download successful")
    print(f"  Content type: {response.headers.get('Content-Type')}")
    print(f"  File size: {len(response.content)} bytes")
    
    # Save markdown for inspection
    with open('test_output.md', 'wb') as f:
        f.write(response.content)
    print(f"  Saved to: test_output.md")
    
    print("\n✅ All single PDF tests passed!")
    print(f"\nTo view results in browser, open: http://localhost:8000{result['results_url']}")
    
    return True


def test_multiple_pdf_handling():
    """Test multiple PDF upload and results"""
    print("\n=== Testing Multiple PDF Handling ===")
    
    # Find multiple test PDFs
    test_pdfs = []
    possible_files = [
        "/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "test_files/standard.pdf",
        "test_files/multipage.pdf"
    ]
    
    for file in possible_files:
        if os.path.exists(file) and len(test_pdfs) < 3:
            test_pdfs.append(file)
    
    if len(test_pdfs) < 2:
        print("❌ Not enough test PDFs found for multi-file test")
        return False
    
    print(f"✓ Using {len(test_pdfs)} test PDFs")
    
    # Convert each PDF
    statement_ids = []
    for pdf in test_pdfs:
        print(f"\nConverting: {os.path.basename(pdf)}")
        with open(pdf, 'rb') as f:
            files = {'file': (os.path.basename(pdf), f, 'application/pdf')}
            response = requests.post(
                "http://localhost:5000/api/convert",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            statement_ids.append(result['id'])
            print(f"  ✓ Statement ID: {result['id']}")
        else:
            print(f"  ❌ Failed: {response.status_code}")
    
    if statement_ids:
        ids_param = ','.join(map(str, statement_ids))
        print(f"\n✅ Multiple PDF test completed!")
        print(f"\nTo view results in browser, open: http://localhost:8000/results?ids={ids_param}")
    
    return len(statement_ids) > 0


def test_frontend_integration():
    """Test that frontend files are accessible"""
    print("\n=== Testing Frontend Integration ===")
    
    frontend_files = [
        "results-overview.html",
        "js/results-overview.js",
        "css/results-overview.css"
    ]
    
    all_exist = True
    for file in frontend_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests"""
    print("PDF Results Overview - Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("backend/main.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_frontend_integration():
        tests_passed += 1
    
    if test_single_pdf_conversion():
        tests_passed += 1
    
    if test_multiple_pdf_handling():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✅ All tests passed! The results overview feature is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    # Cleanup
    if os.path.exists('test_output.md'):
        os.remove('test_output.md')


if __name__ == "__main__":
    main()