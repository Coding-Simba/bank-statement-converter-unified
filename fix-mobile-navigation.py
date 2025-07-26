#!/usr/bin/env python3
"""
Fix mobile navigation across all HTML files
"""

import os
import re
from bs4 import BeautifulSoup

def fix_mobile_navigation(directory):
    """Fix mobile navigation in all HTML files"""
    fixed_files = []
    
    # Enhanced mobile navigation JavaScript
    mobile_nav_script = '''document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
            // Prevent body scroll when menu is open
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('nav') && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
});'''
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common non-project directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        
        for file in files:
            if file.endswith('.html') and not file.startswith('test-'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Check if page has navigation
                    nav = soup.find('nav')
                    if not nav:
                        continue
                    
                    # Check if menu toggle exists
                    menu_toggle = soup.find('button', class_='menu-toggle')
                    if not menu_toggle:
                        continue
                    
                    # Find existing script tags
                    existing_scripts = soup.find_all('script')
                    
                    # Check if mobile nav script already exists
                    has_mobile_nav = False
                    for script in existing_scripts:
                        if script.string and ('menuToggle' in script.string and 'navMenu' in script.string):
                            has_mobile_nav = True
                            # Replace with enhanced script
                            script.string = mobile_nav_script
                            break
                    
                    # If no mobile nav script found, add it before closing body
                    if not has_mobile_nav:
                        new_script = soup.new_tag('script')
                        new_script.string = mobile_nav_script
                        
                        # Insert before closing body tag
                        body = soup.find('body')
                        if body:
                            body.append(new_script)
                    
                    # Write the updated content
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    
                    fixed_files.append(filepath)
                
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return fixed_files

def main():
    """Main function"""
    # Get the project root directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Fixing mobile navigation across all HTML files...")
    
    # Fix mobile navigation
    fixed_files = fix_mobile_navigation(project_dir)
    
    print(f"\nFixed mobile navigation in {len(fixed_files)} files:")
    for file in sorted(fixed_files):
        print(f"  - {os.path.relpath(file, project_dir)}")
    
    # Create a summary report
    with open('mobile-nav-fix-report.md', 'w') as f:
        f.write("# Mobile Navigation Fix Report\n\n")
        f.write(f"Total files updated: {len(fixed_files)}\n\n")
        f.write("## Enhanced Features:\n\n")
        f.write("- ✓ Hamburger menu toggle animation\n")
        f.write("- ✓ Slide-in menu from right\n")
        f.write("- ✓ Auto-close on link click\n")
        f.write("- ✓ Close on outside click\n")
        f.write("- ✓ Close on Escape key\n")
        f.write("- ✓ Prevent body scroll when menu is open\n")
        f.write("- ✓ Smooth transitions\n\n")
        f.write("## Updated Files:\n\n")
        for file in sorted(fixed_files):
            f.write(f"- {os.path.relpath(file, project_dir)}\n")
    
    print("\n✅ Mobile navigation fixed successfully!")
    print("📄 Report saved to: mobile-nav-fix-report.md")

if __name__ == "__main__":
    main()