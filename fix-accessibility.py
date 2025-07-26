#!/usr/bin/env python3
"""
Fix accessibility issues across all HTML pages
"""

import os
import re
from bs4 import BeautifulSoup, Comment

def add_skip_navigation(soup):
    """Add skip navigation link after body tag"""
    body = soup.find('body')
    if body and not soup.find('a', class_='skip-link'):
        # Create skip link
        skip_link = soup.new_tag('a', href='#main', class_='skip-link')
        skip_link.string = 'Skip to main content'
        
        # Insert as first element in body
        if body.contents and not isinstance(body.contents[0], str) or (isinstance(body.contents[0], str) and body.contents[0].strip()):
            body.insert(0, skip_link)
        else:
            body.insert(1, skip_link)
        
        # Add CSS if not present
        style_tag = soup.find('style')
        if style_tag and '.skip-link' not in str(style_tag):
            skip_css = """
/* Skip Navigation Link */
.skip-link {
    position: absolute;
    left: -9999px;
    z-index: 999999;
    padding: 8px 16px;
    background: #000;
    color: white;
    text-decoration: none;
    border-radius: 4px;
}
.skip-link:focus {
    position: absolute;
    left: 6px;
    top: 7px;
}"""
            style_tag.string = str(style_tag.string or '') + skip_css
        
        return True
    return False

def fix_file_input_labels(soup):
    """Add aria-label to all file inputs"""
    fixed = False
    file_inputs = soup.find_all('input', type='file')
    for file_input in file_inputs:
        if not file_input.get('aria-label') and not file_input.get('id'):
            file_input['aria-label'] = 'Upload PDF bank statement'
            fixed = True
        elif file_input.get('id') and not soup.find('label', {'for': file_input['id']}):
            # If it has an ID but no label, add aria-label
            file_input['aria-label'] = 'Upload PDF bank statement'
            fixed = True
    return fixed

def fix_heading_hierarchy(soup):
    """Fix heading hierarchy issues"""
    fixed = False
    
    # Find all headings
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    # Check for multiple H1s
    h1_tags = soup.find_all('h1')
    if len(h1_tags) > 1:
        # Keep the first H1, convert others to H2
        for i, h1 in enumerate(h1_tags[1:], 1):
            h1.name = 'h2'
            fixed = True
    
    # Fix heading jumps (e.g., H1 to H3)
    prev_level = 0
    for heading in headings:
        current_level = int(heading.name[1])
        
        # If we skip more than one level
        if prev_level > 0 and current_level > prev_level + 1:
            # Adjust to be one level below previous
            new_level = prev_level + 1
            if new_level <= 6:
                heading.name = f'h{new_level}'
                fixed = True
                current_level = new_level
        
        prev_level = current_level
    
    return fixed

def add_lang_attribute(soup):
    """Add lang='en' to html tag if missing"""
    html_tag = soup.find('html')
    if html_tag and not html_tag.get('lang'):
        html_tag['lang'] = 'en'
        return True
    return False

def ensure_main_id(soup):
    """Ensure there's a main element or element with id='main'"""
    if not soup.find(id='main') and not soup.find('main'):
        # Find the main content area
        content_area = (soup.find('div', class_='container') or 
                       soup.find('div', class_='content') or
                       soup.find('div', class_='main-content'))
        
        if content_area:
            content_area['id'] = 'main'
            return True
    return False

def process_file(filepath):
    """Process a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        changes = []
        
        # Apply fixes
        if add_skip_navigation(soup):
            changes.append("Added skip navigation")
        
        if fix_file_input_labels(soup):
            changes.append("Fixed file input labels")
        
        if fix_heading_hierarchy(soup):
            changes.append("Fixed heading hierarchy")
        
        if add_lang_attribute(soup):
            changes.append("Added lang attribute")
        
        if ensure_main_id(soup):
            changes.append("Added main content ID")
        
        # Save if changes were made
        if changes:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            print(f"✓ {os.path.basename(filepath)}: {', '.join(changes)}")
            return True
        else:
            print(f"- {os.path.basename(filepath)}: No changes needed")
            return False
    
    except Exception as e:
        print(f"✗ Error processing {filepath}: {str(e)}")
        return False

def main():
    """Process all HTML files"""
    base_dir = '/Users/MAC/chrome/bank-statement-converter-unified'
    
    total_files = 0
    fixed_files = 0
    
    # Process all HTML files
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories and node_modules
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                total_files += 1
                
                if process_file(filepath):
                    fixed_files += 1
    
    print(f"\n{'='*50}")
    print(f"Accessibility fixes complete!")
    print(f"Total files processed: {total_files}")
    print(f"Files updated: {fixed_files}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()