#!/usr/bin/env python3
"""
Fix common deadlinks and loading errors in the website
"""

import os
import re
from pathlib import Path

def fix_social_media_links(content):
    """Replace placeholder social media links with actual ones"""
    replacements = {
        '<a href="#" aria-label="Twitter">': '<a href="https://twitter.com/bankcsvconverter" aria-label="Twitter" target="_blank" rel="noopener">',
        '<a href="#" aria-label="LinkedIn">': '<a href="https://linkedin.com/company/bankcsvconverter" aria-label="LinkedIn" target="_blank" rel="noopener">',
        '<a href="#" aria-label="Facebook">': '<a href="https://facebook.com/bankcsvconverter" aria-label="Facebook" target="_blank" rel="noopener">',
        '<a aria-label="Twitter" href="#">': '<a aria-label="Twitter" href="https://twitter.com/bankcsvconverter" target="_blank" rel="noopener">',
        '<a aria-label="LinkedIn" href="#">': '<a aria-label="LinkedIn" href="https://linkedin.com/company/bankcsvconverter" target="_blank" rel="noopener">',
        '<a aria-label="Facebook" href="#">': '<a aria-label="Facebook" href="https://facebook.com/bankcsvconverter" target="_blank" rel="noopener">'
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    return content

def fix_missing_pages(content):
    """Fix links to pages that might not exist"""
    # Check if features.html exists, if not link to index.html#features
    if not os.path.exists('features.html'):
        content = content.replace('href="/features.html"', 'href="/#features"')
    
    # Add other missing page fixes here
    return content

def fix_css_references(content):
    """Ensure CSS files are properly referenced"""
    # Fix any duplicate or incorrect CSS references
    css_files = [
        '/css/modern-homepage.css',
        '/css/nav-fix.css',
        '/css/dropdown-fix.css',
        '/css/blog-fix.css'
    ]
    
    # Remove duplicates
    for css in css_files:
        pattern = f'<link[^>]*href="{css}"[^>]*>'
        matches = re.findall(pattern, content)
        if len(matches) > 1:
            # Keep only the first occurrence
            first_occurrence = True
            def replace_duplicate(match):
                nonlocal first_occurrence
                if first_occurrence:
                    first_occurrence = False
                    return match.group(0)
                return ''
            content = re.sub(pattern, replace_duplicate, content)
    
    return content

def process_file(filepath):
    """Process a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_social_media_links(content)
        content = fix_missing_pages(content)
        content = fix_css_references(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function"""
    fixed_count = 0
    
    # Process all HTML files
    for filepath in Path('.').glob('*.html'):
        if process_file(filepath):
            fixed_count += 1
    
    # Process HTML files in subdirectories
    for subdir in ['pages', 'blog']:
        if os.path.exists(subdir):
            for filepath in Path(subdir).glob('*.html'):
                if process_file(filepath):
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")
    
    # Check for missing critical files
    print("\nChecking for missing critical files...")
    critical_files = [
        'css/modern-homepage.css',
        'css/nav-fix.css',
        'css/dropdown-fix.css',
        'js/api-config.js',
        'js/auth.js',
        'js/stripe-integration.js',
        'assets/pdf-icon.svg'
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("\nWARNING: Missing critical files:")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("All critical files are present.")

if __name__ == "__main__":
    main()