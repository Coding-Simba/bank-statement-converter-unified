#!/usr/bin/env python3
"""
Update all HTML files to use the consolidated main.css file
"""

import os
import re
from bs4 import BeautifulSoup

def update_css_references(directory):
    """Update CSS references in all HTML files"""
    updated_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common non-project directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all link tags for CSS
                    css_links = soup.find_all('link', rel='stylesheet')
                    
                    # Track if we made changes
                    changed = False
                    
                    for link in css_links:
                        href = link.get('href', '')
                        
                        # Skip external CSS (CDNs, etc.)
                        if href.startswith('http://') or href.startswith('https://'):
                            continue
                        
                        # Update any local CSS references to main.css
                        if 'css/' in href and href.endswith('.css'):
                            # Calculate the correct relative path to css/main.css
                            depth = filepath.count(os.sep) - directory.count(os.sep) - 1
                            
                            if depth == 0:
                                new_href = 'css/main.css'
                            else:
                                new_href = '../' * depth + 'css/main.css'
                            
                            if href != new_href:
                                link['href'] = new_href
                                changed = True
                    
                    if changed:
                        # Write the updated content
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        
                        updated_files.append(filepath)
                
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return updated_files

def main():
    """Main function"""
    # Get the project root directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Updating CSS references in all HTML files...")
    
    # Update all HTML files
    updated_files = update_css_references(project_dir)
    
    print(f"\nUpdated {len(updated_files)} HTML files:")
    for file in sorted(updated_files):
        print(f"  - {os.path.relpath(file, project_dir)}")
    
    # Create a summary report
    with open('css-update-report.md', 'w') as f:
        f.write("# CSS Reference Update Report\n\n")
        f.write(f"Total files updated: {len(updated_files)}\n\n")
        f.write("## Updated Files:\n\n")
        for file in sorted(updated_files):
            f.write(f"- {os.path.relpath(file, project_dir)}\n")
        f.write("\n## Next Steps:\n\n")
        f.write("1. Test all pages to ensure CSS is loading correctly\n")
        f.write("2. Remove old CSS files after confirming everything works\n")
        f.write("3. Update any build processes or documentation\n")
    
    print("\n✅ CSS references updated successfully!")
    print("📄 Report saved to: css-update-report.md")

if __name__ == "__main__":
    main()