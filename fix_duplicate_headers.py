#!/usr/bin/env python3
"""
Fix duplicate headers in pages that have both old and new navigation
"""

import os
import re

def fix_duplicate_headers(filepath):
    """Remove old header sections that duplicate the new navigation"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove old site-header sections
    # Pattern to match old header with class="site-header"
    old_header_pattern = r'<header class="site-header">.*?</header>\s*'
    content = re.sub(old_header_pattern, '', content, flags=re.DOTALL)
    
    # Remove duplicate nav sections with class="main-nav"
    duplicate_nav_pattern = r'<nav class="main-nav">.*?</nav>\s*'
    content = re.sub(duplicate_nav_pattern, '', content, flags=re.DOTALL)
    
    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed duplicate headers in: {filepath}")

def main():
    # Process all HTML files
    pages_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/pages'
    
    # Pages that likely have duplicate headers based on the updates
    files_to_check = [
        'san-diego-bank-statement-converter.html',
        'bank-statement-converter-comparison.html',
        'chicago-bank-statement-converter.html'
    ]
    
    # Actually, let's check all files
    for filename in os.listdir(pages_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(pages_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if file has duplicate headers
            if 'class="site-header"' in content or ('class="main-nav"' in content and content.count('<header') > 1):
                fix_duplicate_headers(filepath)

if __name__ == '__main__':
    main()