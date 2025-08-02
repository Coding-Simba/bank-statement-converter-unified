#!/usr/bin/env python3
"""Add blog-page class to blog pages for proper CSS scoping"""

import os
import re

def add_blog_page_class(filepath):
    """Add blog-page class to body tag if it's a blog page"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has blog-page class
        if 'class="blog-page"' in content or "class='blog-page'" in content:
            return False
        
        # Add blog-page class to body tag
        patterns = [
            (r'<body>', '<body class="blog-page">'),
            (r'<body\s+([^>]*)>', r'<body class="blog-page" \1>')
        ]
        
        updated = False
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content, count=1)
            if new_content != content:
                content = new_content
                updated = True
                break
        
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Added blog-page class to: {filepath}")
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False

def main():
    """Process blog pages"""
    updated_files = 0
    
    # Process blog.html
    if os.path.exists('blog.html'):
        if add_blog_page_class('blog.html'):
            updated_files += 1
    
    # Process blog directory
    if os.path.exists('blog'):
        for filename in os.listdir('blog'):
            if filename.endswith('.html'):
                filepath = os.path.join('blog', filename)
                if add_blog_page_class(filepath):
                    updated_files += 1
    
    print(f"\n📊 Summary: Updated {updated_files} blog pages")

if __name__ == "__main__":
    main()