#!/usr/bin/env python3
import os
import re
from bs4 import BeautifulSoup, Comment
import sys

def add_accessibility_features(file_path):
    """Add accessibility features to an HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Track if we made changes
        changes_made = False
        
        # 1. Add lang="en" to html tag if missing
        html_tag = soup.find('html')
        if html_tag and not html_tag.get('lang'):
            html_tag['lang'] = 'en'
            changes_made = True
            print(f"  - Added lang='en' to html tag")
        
        # 2. Add skip navigation link after body tag
        body_tag = soup.find('body')
        if body_tag:
            # Check if skip link already exists
            skip_link = soup.find('a', class_='skip-link')
            if not skip_link:
                # Create skip link
                skip_link = soup.new_tag('a', href='#main', attrs={'class': 'skip-link'})
                skip_link.string = 'Skip to main content'
                
                # Insert as first child of body
                if body_tag.contents and not isinstance(body_tag.contents[0], str):
                    body_tag.insert(0, '\n')
                body_tag.insert(0, skip_link)
                body_tag.insert(1, '\n')
                changes_made = True
                print(f"  - Added skip navigation link")
        
        # 3. Add aria-label to all file inputs
        file_inputs = soup.find_all('input', type='file')
        for file_input in file_inputs:
            if not file_input.get('aria-label'):
                file_input['aria-label'] = 'Upload PDF bank statement'
                changes_made = True
                print(f"  - Added aria-label to file input")
        
        # 4. Fix heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        h1_count = len(soup.find_all('h1'))
        
        if h1_count == 0:
            print(f"  - WARNING: No H1 found in the page")
        elif h1_count > 1:
            print(f"  - WARNING: Multiple H1 tags found ({h1_count})")
        
        # Check heading hierarchy
        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if prev_level > 0 and level > prev_level + 1:
                print(f"  - WARNING: Heading hierarchy issue - {heading.name} follows H{prev_level}")
            prev_level = level
        
        # 5. Check form elements for labels
        form_elements = soup.find_all(['input', 'select', 'textarea'])
        for elem in form_elements:
            if elem.name == 'input' and elem.get('type') in ['submit', 'button', 'hidden']:
                continue
                
            elem_id = elem.get('id')
            elem_name = elem.get('name')
            
            # Check if element has associated label
            has_label = False
            
            # Check for label with 'for' attribute
            if elem_id:
                label = soup.find('label', attrs={'for': elem_id})
                if label:
                    has_label = True
            
            # Check if element is wrapped in label
            if not has_label and elem.parent and elem.parent.name == 'label':
                has_label = True
            
            # Check for aria-label
            if not has_label and elem.get('aria-label'):
                has_label = True
            
            if not has_label:
                print(f"  - WARNING: Form element without label: {elem.name} with name='{elem_name}' id='{elem_id}'")
        
        # 6. Add CSS for skip links if not already present
        style_tag = soup.find('style')
        skip_link_css = """
.skip-link {
  position: absolute;
  left: -9999px;
}
.skip-link:focus {
  position: absolute;
  left: 6px;
  top: 7px;
  z-index: 999999;
  padding: 8px 16px;
  background: #000;
  color: white;
  text-decoration: none;
}"""
        
        # Check if skip-link CSS already exists
        has_skip_css = False
        for style in soup.find_all('style'):
            if '.skip-link' in style.string if style.string else '':
                has_skip_css = True
                break
        
        # Also check in linked CSS files (just notify, don't modify external files)
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if 'styles.css' in href or 'main.css' in href:
                print(f"  - Note: Check if skip-link CSS is in external stylesheet: {href}")
        
        if not has_skip_css:
            if not style_tag:
                # Create new style tag in head
                head_tag = soup.find('head')
                if head_tag:
                    style_tag = soup.new_tag('style')
                    style_tag.string = skip_link_css
                    head_tag.append('\n')
                    head_tag.append(style_tag)
                    head_tag.append('\n')
                    changes_made = True
                    print(f"  - Added skip-link CSS styles")
            else:
                # Append to existing style tag
                if style_tag.string:
                    style_tag.string = style_tag.string + '\n' + skip_link_css
                else:
                    style_tag.string = skip_link_css
                changes_made = True
                print(f"  - Added skip-link CSS to existing style tag")
        
        # Save the file if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            return True
        
        return False
        
    except Exception as e:
        print(f"  - ERROR: {str(e)}")
        return False

def main():
    # Directory containing HTML files
    base_dir = '/Users/MAC/chrome/bank-statement-converter-unified'
    
    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files to process\n")
    
    # Process each file
    updated_count = 0
    for file_path in sorted(html_files):
        relative_path = os.path.relpath(file_path, base_dir)
        print(f"Processing: {relative_path}")
        
        if add_accessibility_features(file_path):
            updated_count += 1
        
        print()  # Empty line between files
    
    print(f"\nSummary: Updated {updated_count} out of {len(html_files)} files")

if __name__ == "__main__":
    main()