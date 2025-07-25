#!/usr/bin/env python3
"""
Apply performance optimizations to all HTML files
Updates references to use minified CSS and JS files
"""

import os
import re
from pathlib import Path

def update_html_file(filepath):
    """Update a single HTML file with optimizations"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Update CSS references to minified versions
    css_patterns = [
        (r'<link rel="stylesheet" href="(\.\./)?css/modern-style\.css">', 
         r'<link rel="stylesheet" href="\1css/modern-style.min.css">'),
        (r'<link rel="stylesheet" href="(\.\./)?css/style\.css">', 
         r'<link rel="stylesheet" href="\1css/style.min.css">'),
        (r'<link rel="stylesheet" href="(\.\./)?css/style-seo\.css">', 
         r'<link rel="stylesheet" href="\1css/style-seo.min.css">')
    ]
    
    for pattern, replacement in css_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made.append(f"Updated CSS: {pattern}")
    
    # Update JS references to minified versions with defer
    js_patterns = [
        (r'<script src="(\.\./)?js/main\.js"></script>', 
         r'<script src="\1js/main.min.js" defer></script>'),
        (r'<script src="(\.\./)?js/main-seo\.js"></script>', 
         r'<script src="\1js/main-seo.min.js" defer></script>')
    ]
    
    for pattern, replacement in js_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made.append(f"Updated JS: {pattern}")
    
    # Add resource hints if not present
    if 'dns-prefetch' not in content and '<head>' in content:
        resource_hints = '''    <!-- Resource Hints for Performance -->
    <link rel="dns-prefetch" href="//localhost:5000">
    <link rel="preconnect" href="//localhost:5000">
    
'''
        content = content.replace('<head>\n', '<head>\n' + resource_hints)
        changes_made.append("Added resource hints")
    
    # Only save if changes were made
    if content != original_content:
        # Create backup
        backup_path = filepath.with_suffix(filepath.suffix + '.backup')
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        # Save updated file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return True, changes_made
    
    return False, []

def main():
    """Apply optimizations to all HTML files"""
    print("🚀 Applying Performance Optimizations to HTML Files")
    print("=" * 50)
    
    # Check if minified files exist
    required_files = [
        'css/modern-style.min.css',
        'css/style.min.css',
        'js/main.min.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing minified files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n⚠️  Run optimize_performance.py first to create minified files")
        return
    
    # Find all HTML files
    html_files = []
    
    # Root directory HTML files
    for file in Path('.').glob('*.html'):
        if not file.name.endswith('.backup'):
            html_files.append(file)
    
    # Pages directory HTML files
    pages_dir = Path('pages')
    if pages_dir.exists():
        for file in pages_dir.glob('*.html'):
            if not file.name.endswith('.backup'):
                html_files.append(file)
    
    # Blog directory HTML files
    blog_dir = Path('blog')
    if blog_dir.exists():
        for file in blog_dir.glob('*.html'):
            if not file.name.endswith('.backup'):
                html_files.append(file)
    
    print(f"\nFound {len(html_files)} HTML files to process")
    
    # Process each file
    updated_count = 0
    for html_file in html_files:
        print(f"\nProcessing: {html_file}")
        updated, changes = update_html_file(html_file)
        
        if updated:
            updated_count += 1
            print(f"  ✅ Updated with {len(changes)} changes:")
            for change in changes:
                print(f"     - {change}")
        else:
            print("  ℹ️  No changes needed")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Optimization Complete!")
    print(f"   Files processed: {len(html_files)}")
    print(f"   Files updated: {updated_count}")
    print(f"   Backups created: {updated_count}")
    
    if updated_count > 0:
        print("\n💡 Next Steps:")
        print("   1. Test the updated pages in your browser")
        print("   2. Run lighthouse audits on key pages")
        print("   3. Deploy to production when ready")
        print("\n⚠️  Note: Original files backed up with .backup extension")

if __name__ == "__main__":
    main()