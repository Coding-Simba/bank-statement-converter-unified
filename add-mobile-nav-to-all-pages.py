#!/usr/bin/env python3
"""
Add mobile navigation script to all HTML pages
"""
import os
from bs4 import BeautifulSoup

def add_mobile_nav_script(file_path):
    """Add mobile navigation script to an HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check if mobile-nav.js is already included
        mobile_nav_script = soup.find('script', {'src': lambda x: x and 'mobile-nav.js' in x})
        
        if not mobile_nav_script:
            # Find the body tag
            body = soup.find('body')
            if body:
                # Create new script tag
                new_script = soup.new_tag('script', src='js/mobile-nav.js')
                
                # Try to find the best place to insert it
                # Look for other script tags at the end of body
                last_script = None
                for script in body.find_all('script'):
                    if script.get('src') or script.string:
                        last_script = script
                
                if last_script:
                    # Insert after the last script
                    last_script.insert_after(new_script)
                else:
                    # Append to body
                    body.append(new_script)
                
                # Adjust path for pages in subdirectories
                if 'pages/' in file_path:
                    new_script['src'] = '../js/mobile-nav.js'
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                print(f"✅ Updated: {file_path}")
                return True
            else:
                print(f"⚠️  No body tag found in: {file_path}")
                return False
        else:
            print(f"ℹ️  Already has mobile nav: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Process all HTML files"""
    updated_count = 0
    
    # Process root HTML files
    for filename in os.listdir('.'):
        if filename.endswith('.html') and not filename.startswith('test'):
            if add_mobile_nav_script(filename):
                updated_count += 1
    
    # Process pages directory
    if os.path.exists('pages'):
        for filename in os.listdir('pages'):
            if filename.endswith('.html'):
                file_path = os.path.join('pages', filename)
                if add_mobile_nav_script(file_path):
                    updated_count += 1
    
    print(f"\n✨ Updated {updated_count} files with mobile navigation script")

if __name__ == "__main__":
    main()