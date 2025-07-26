#!/usr/bin/env python3
"""
Fix broken footer links across all pages
Priority: CRITICAL - Broken links damage SEO and user trust
"""

import os
import re
from bs4 import BeautifulSoup

# Broken links to remove
BROKEN_LINKS = [
    '/integrations.html',
    '/accountants.html', 
    '/bookkeepers.html',
    '/personal.html',
    '/tutorials.html',
    '/press.html'
]

def fix_footer_links(file_path):
    """Remove broken links from footer"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all footer links
    footer = soup.find('footer')
    if not footer:
        return False
    
    links_removed = 0
    
    # Find all anchor tags in footer
    for link in footer.find_all('a'):
        href = link.get('href', '')
        # Check if it's a broken link
        for broken_link in BROKEN_LINKS:
            if href.endswith(broken_link) or href == broken_link.lstrip('/'):
                # Remove the entire list item containing the link
                parent_li = link.find_parent('li')
                if parent_li:
                    parent_li.decompose()
                    links_removed += 1
                else:
                    # If not in a list item, just remove the link
                    link.decompose()
                    links_removed += 1
                break
    
    if links_removed > 0:
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"  ✅ Removed {links_removed} broken links")
        return True
    else:
        print(f"  ✓ No broken links found")
        return False

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
    
    print(f"Found {len(html_files)} HTML files to process")
    print(f"Removing broken links: {', '.join(BROKEN_LINKS)}\n")
    
    for file_path in sorted(html_files):
        print(f"Processing: {file_path}")
        if fix_footer_links(file_path):
            updated_count += 1
        else:
            skipped_count += 1
    
    return updated_count, skipped_count

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing Broken Footer Links")
    print("=" * 60)
    print()
    
    updated, skipped = process_all_html_files()
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  - Files updated: {updated}")
    print(f"  - Files skipped: {skipped}")
    print(f"  - Total processed: {updated + skipped}")
    print("=" * 60)