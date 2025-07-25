#!/usr/bin/env python3
"""
Fix duplicate headers in blog pages
"""

import os
import re

def fix_blog_duplicate_headers(filepath):
    """Remove duplicate header sections in blog pages"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find duplicate headers (after the first one we just added)
    # Look for header tags that come after our standard header
    pattern = r'(</header>\s*<header>.*?</header>)'
    
    # Remove duplicate headers
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Also remove old nav sections with class="navbar" or similar
    old_nav_pattern = r'<nav class="navbar">.*?</nav>\s*'
    content = re.sub(old_nav_pattern, '', content, flags=re.DOTALL)
    
    # Remove duplicate header content blocks
    duplicate_header_pattern = r'<header>\s*<nav[^>]*>\s*<div[^>]*>\s*<a[^>]*>Bank Statement Converter</a>.*?</nav>\s*</header>'
    # Count how many headers exist
    headers = re.findall(r'<header>', content)
    if len(headers) > 1:
        # Keep only the first header by removing subsequent ones
        parts = content.split('</header>')
        if len(parts) > 2:
            # Reconstruct keeping only first header
            new_content = parts[0] + '</header>'
            # Add the rest of the content after removing any additional header tags
            remaining = '</header>'.join(parts[1:])
            remaining = re.sub(r'<header>.*?</nav>\s*', '', remaining, flags=re.DOTALL)
            content = new_content + remaining
    
    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed duplicate headers in: {filepath}")

def main():
    # Process all blog HTML files
    blog_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/blog'
    
    for filename in os.listdir(blog_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(blog_dir, filename)
            fix_blog_duplicate_headers(filepath)

if __name__ == '__main__':
    main()