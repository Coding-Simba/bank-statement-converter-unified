#!/usr/bin/env python3
"""
Consolidate and minify CSS files
Priority: CRITICAL - Improves page load speed
"""

import os
import re
from pathlib import Path

# CSS files to consolidate (in order of importance)
CSS_FILES_TO_CONSOLIDATE = [
    'css/modern-homepage.css',
    'css/nav-fix.css', 
    'css/dropdown-fix.css',
    'css/blog-fix.css',
    'css/blog-text-size-fix.css',
    'css/production.css',
    'css/ui-components.css',
    'css/mobile-navigation.css'
]

def read_css_file(file_path):
    """Read CSS file and return content"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def minify_css(css_content):
    """Basic CSS minification"""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Remove unnecessary whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    css_content = re.sub(r'\s*{\s*', '{', css_content)
    css_content = re.sub(r'\s*}\s*', '}', css_content)
    css_content = re.sub(r'\s*:\s*', ':', css_content)
    css_content = re.sub(r'\s*;\s*', ';', css_content)
    css_content = re.sub(r';\s*}', '}', css_content)
    
    # Remove last semicolon before closing brace
    css_content = re.sub(r';}', '}', css_content)
    
    # Trim
    return css_content.strip()

def consolidate_css():
    """Consolidate all CSS files into one"""
    print("Consolidating CSS files...")
    
    all_css = []
    
    # Add header comment
    all_css.append("/* BankCSVConverter - Production CSS Bundle */")
    all_css.append("/* Generated: 2025 */\n")
    
    # Read and combine all CSS files
    for css_file in CSS_FILES_TO_CONSOLIDATE:
        if os.path.exists(css_file):
            print(f"  ✓ Adding {css_file}")
            content = read_css_file(css_file)
            if content:
                all_css.append(f"\n/* === {css_file} === */")
                all_css.append(content)
        else:
            print(f"  ⚠️  Not found: {css_file}")
    
    # Combine all CSS
    combined_css = '\n'.join(all_css)
    
    # Write unminified version (for debugging)
    with open('css/production-bundle.css', 'w', encoding='utf-8') as f:
        f.write(combined_css)
    print("\n✅ Created: css/production-bundle.css")
    
    # Create minified version
    minified_css = minify_css(combined_css)
    with open('css/production.min.css', 'w', encoding='utf-8') as f:
        f.write(minified_css)
    print("✅ Created: css/production.min.css")
    
    # Calculate savings
    original_size = len(combined_css)
    minified_size = len(minified_css)
    savings = (original_size - minified_size) / original_size * 100
    
    print(f"\n📊 Size reduction: {savings:.1f}%")
    print(f"   Original: {original_size:,} bytes")
    print(f"   Minified: {minified_size:,} bytes")
    
    return minified_size

def update_html_files():
    """Update HTML files to use minified CSS"""
    print("\n\nUpdating HTML files to use minified CSS...")
    
    updated_count = 0
    
    # Pattern to find CSS links
    css_pattern = r'<link[^>]*href="[^"]*\.css"[^>]*>'
    
    # Replacement link
    replacement = '<link href="/css/production.min.css" rel="stylesheet">'
    
    # Get all HTML files
    html_files = []
    
    # Root level
    for file in os.listdir('.'):
        if file.endswith('.html') and not file.startswith('test') and not file.startswith('demo'):
            html_files.append(file)
    
    # Process first 10 files as example
    for file_path in html_files[:10]:
        print(f"\nProcessing: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all CSS links
        css_links = re.findall(css_pattern, content)
        
        if css_links:
            # Remove all CSS links except Font Awesome
            new_content = content
            for link in css_links:
                if 'font-awesome' not in link and 'fontawesome' not in link:
                    new_content = new_content.replace(link, '')
            
            # Add single minified CSS link after charset meta tag
            if replacement not in new_content:
                charset_match = re.search(r'<meta[^>]*charset[^>]*>', new_content)
                if charset_match:
                    insert_pos = charset_match.end()
                    new_content = new_content[:insert_pos] + '\n' + replacement + new_content[insert_pos:]
                
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  ✅ Updated - removed {len(css_links)} CSS links, added minified version")
            updated_count += 1
        else:
            print(f"  ✓ No CSS links found")
    
    return updated_count

if __name__ == "__main__":
    print("=" * 60)
    print("CSS Consolidation and Minification")
    print("=" * 60)
    
    # Consolidate and minify
    minified_size = consolidate_css()
    
    # Update HTML files
    updated_files = update_html_files()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  - CSS files consolidated: {len(CSS_FILES_TO_CONSOLIDATE)}")
    print(f"  - Minified CSS size: {minified_size:,} bytes")
    print(f"  - HTML files updated: {updated_files}")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Test the website to ensure CSS is loading correctly")
    print("2. Run this script again with more HTML files")
    print("3. Set up automated build process for future CSS changes")