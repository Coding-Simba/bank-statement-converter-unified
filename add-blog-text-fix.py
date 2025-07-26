#!/usr/bin/env python3
"""
Add blog-text-size-fix.css to all blog HTML files
"""

import os
import re

# CSS link to add
css_link = '    <link href="/css/blog-text-size-fix.css" rel="stylesheet"/>\n'

# Directory containing blog files
blog_dir = './blog'

# Pattern to find where to insert the CSS (after blog-fix.css)
insert_pattern = r'(.*<link href="/css/blog-fix.css" rel="stylesheet"/>.*\n)'

def update_blog_file(filepath):
    """Add the CSS link to a blog file if not already present"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the CSS is already included
        if 'blog-text-size-fix.css' in content:
            print(f"Skipped (already has fix): {filepath}")
            return False
        
        # Find the blog-fix.css line and insert after it
        if re.search(insert_pattern, content):
            content = re.sub(insert_pattern, r'\1' + css_link, content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
            return True
        else:
            # If blog-fix.css not found, look for any CSS link in head
            head_pattern = r'(.*<link rel="stylesheet".*\n)'
            if re.search(head_pattern, content):
                # Find the last CSS link
                matches = list(re.finditer(head_pattern, content))
                if matches:
                    last_match = matches[-1]
                    insert_pos = last_match.end()
                    content = content[:insert_pos] + css_link + content[insert_pos:]
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated: {filepath}")
                    return True
        
        print(f"Warning: Could not find insertion point in {filepath}")
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

# Process all blog HTML files
if __name__ == "__main__":
    print("Adding blog-text-size-fix.css to all blog pages...")
    print("-" * 50)
    
    updated_count = 0
    
    for filename in os.listdir(blog_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(blog_dir, filename)
            if update_blog_file(filepath):
                updated_count += 1
    
    print("-" * 50)
    print(f"Total files updated: {updated_count}")
    print("\nDone! The blog text sizes have been reduced for better readability.")