#!/usr/bin/env python3
"""
Add canonical URLs to all HTML pages
Priority: CRITICAL - Prevents duplicate content penalties
"""

import os
import re
from bs4 import BeautifulSoup

# Base URL for the website
BASE_URL = "https://bankcsvconverter.com"

def add_canonical_url(file_path):
    """Add canonical URL to an HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check if canonical already exists
    existing_canonical = soup.find('link', {'rel': 'canonical'})
    if existing_canonical:
        print(f"  ✓ Canonical already exists: {file_path}")
        return False
    
    # Generate canonical URL based on file path
    relative_path = os.path.relpath(file_path, '.')
    if relative_path.endswith('index.html'):
        canonical_path = relative_path.replace('index.html', '')
    else:
        canonical_path = relative_path
    
    # Clean up the path
    canonical_path = canonical_path.replace('\\', '/')
    if canonical_path.startswith('./'):
        canonical_path = canonical_path[2:]
    
    # Special case for root index.html
    if canonical_path == '' or canonical_path == '.':
        canonical_url = BASE_URL + '/'
    else:
        canonical_url = BASE_URL + '/' + canonical_path
    
    # Create canonical link element
    canonical_tag = soup.new_tag('link', rel='canonical', href=canonical_url)
    
    # Find the head tag
    head = soup.find('head')
    if not head:
        print(f"  ⚠️  No <head> tag found: {file_path}")
        return False
    
    # Add canonical after meta tags but before title
    title_tag = head.find('title')
    if title_tag:
        title_tag.insert_before(canonical_tag)
    else:
        # Add at the end of head
        head.append(canonical_tag)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✅ Added canonical URL: {canonical_url}")
    return True

def process_all_html_files():
    """Process all HTML files in the project"""
    updated_count = 0
    skipped_count = 0
    
    # HTML files to process
    html_files = []
    
    # Root level HTML files
    for file in os.listdir('.'):
        if file.endswith('.html') and not file.startswith('test') and not file.startswith('demo'):
            html_files.append(file)
    
    # Pages directory
    if os.path.exists('pages'):
        for file in os.listdir('pages'):
            if file.endswith('.html'):
                html_files.append(os.path.join('pages', file))
    
    # Blog directory
    if os.path.exists('blog'):
        for file in os.listdir('blog'):
            if file.endswith('.html'):
                html_files.append(os.path.join('blog', file))
    
    print(f"Found {len(html_files)} HTML files to process\n")
    
    for file_path in sorted(html_files):
        print(f"Processing: {file_path}")
        if add_canonical_url(file_path):
            updated_count += 1
        else:
            skipped_count += 1
        print()
    
    return updated_count, skipped_count

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Canonical URLs to All Pages")
    print("=" * 60)
    print()
    
    updated, skipped = process_all_html_files()
    
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Files updated: {updated}")
    print(f"  - Files skipped: {skipped}")
    print(f"  - Total processed: {updated + skipped}")
    print("=" * 60)