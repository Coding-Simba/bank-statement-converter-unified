#!/usr/bin/env python3
"""Test all pages to ensure they're working correctly"""

import os
import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "http://localhost:8080"
FRONTEND_DIR = "/Users/MAC/chrome/bank-statement-converter/frontend"

def test_page(path):
    """Test a single page for common issues"""
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {
                "path": path,
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for key elements
        issues = []
        
        # Check for title
        title = soup.find('title')
        if not title:
            issues.append("Missing title tag")
        
        # Check for h1
        h1 = soup.find('h1')
        if not h1:
            issues.append("Missing h1 tag")
        
        # Check for navigation
        nav = soup.find('nav')
        if not nav:
            issues.append("Missing navigation")
        
        # Check for upload button
        upload_btn = soup.find(id='uploadBtn')
        if '/pages/' in path and 'converter' in path and not upload_btn:
            issues.append("Missing upload button")
        
        # Check for CSS
        css_link = soup.find('link', {'href': lambda x: x and 'modern-style.css' in x})
        if not css_link:
            issues.append("Missing modern-style.css")
        
        # Check for broken images
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if 'logo.svg' in src and 'generic-bank-logo' not in src and '/assets/logo.svg' not in src:
                issues.append(f"Potential broken image: {src}")
        
        return {
            "path": path,
            "status": "ok" if not issues else "warning",
            "title": title.text if title else "No title",
            "h1": h1.text if h1 else "No h1",
            "issues": issues
        }
        
    except Exception as e:
        return {
            "path": path,
            "status": "error",
            "error": str(e)
        }

def get_all_html_files():
    """Get all HTML files in the frontend directory"""
    html_files = []
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith('.html'):
                full_path = os.path.join(root, file)
                relative_path = full_path.replace(FRONTEND_DIR, '')
                html_files.append(relative_path)
    return html_files

def main():
    print("Testing all pages in the frontend...")
    print(f"Base URL: {BASE_URL}")
    print("-" * 80)
    
    html_files = get_all_html_files()
    results = []
    
    for path in sorted(html_files):
        result = test_page(path)
        results.append(result)
        
        status_icon = "✅" if result['status'] == 'ok' else "⚠️" if result['status'] == 'warning' else "❌"
        print(f"{status_icon} {path}")
        
        if result['status'] == 'warning' and result.get('issues'):
            for issue in result['issues']:
                print(f"   - {issue}")
        elif result['status'] == 'error':
            print(f"   - Error: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    ok_count = sum(1 for r in results if r['status'] == 'ok')
    warning_count = sum(1 for r in results if r['status'] == 'warning')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Total pages tested: {len(results)}")
    print(f"✅ OK: {ok_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    
    # Save detailed results
    with open('/Users/MAC/chrome/bank-statement-converter/frontend/test-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to test-results.json")

if __name__ == "__main__":
    main()