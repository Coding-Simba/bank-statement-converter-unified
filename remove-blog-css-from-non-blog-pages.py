#!/usr/bin/env python3
"""Remove blog-fix.css from non-blog pages"""

import os
import re

def should_have_blog_css(filepath):
    """Determine if a page should have blog-fix.css"""
    # Only blog pages should have blog-fix.css
    return '/blog/' in filepath or 'blog.html' in filepath

def remove_blog_css_from_file(filepath):
    """Remove blog-fix.css link from a file if it shouldn't have it"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has blog-fix.css
        if 'blog-fix.css' not in content:
            return False
        
        # Check if this page should have blog CSS
        if should_have_blog_css(filepath):
            print(f"✓ Keeping blog-fix.css in: {filepath}")
            return False
        
        # Remove the blog-fix.css link
        patterns = [
            r'<link[^>]*href=["\'][^"\']*blog-fix\.css["\'][^>]*>\s*\n?',
            r'<link[^>]*href=["\'][^"\']*blog-fix\.css["\'][^>]*/>\s*\n?'
        ]
        
        original_content = content
        for pattern in patterns:
            content = re.sub(pattern, '', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✗ Removed blog-fix.css from: {filepath}")
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False

def main():
    """Process all HTML files"""
    updated_files = 0
    
    # Process root HTML files
    for filename in os.listdir('.'):
        if filename.endswith('.html'):
            if remove_blog_css_from_file(filename):
                updated_files += 1
    
    # Process pages directory
    if os.path.exists('pages'):
        for filename in os.listdir('pages'):
            if filename.endswith('.html'):
                filepath = os.path.join('pages', filename)
                if remove_blog_css_from_file(filepath):
                    updated_files += 1
    
    print(f"\n📊 Summary: Updated {updated_files} files")

if __name__ == "__main__":
    main()