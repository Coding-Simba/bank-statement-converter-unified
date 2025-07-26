#!/usr/bin/env python3
"""
Update all HTML files to use production CSS and JS
"""
import os
import re
from bs4 import BeautifulSoup
import glob

def update_html_file(file_path):
    """Update a single HTML file to use production assets"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove all existing CSS links except critical ones
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if 'css/' in href and 'production.css' not in href:
                link.decompose()
        
        # Add production CSS if not already present
        head = soup.find('head')
        if head and not soup.find('link', href=re.compile(r'production\.css')):
            # Add production CSS
            production_css = soup.new_tag('link', rel='stylesheet', href='/css/production.css')
            
            # Find the best place to insert
            last_meta = None
            for meta in head.find_all('meta'):
                last_meta = meta
            
            if last_meta:
                last_meta.insert_after(production_css)
            else:
                head.insert(0, production_css)
        
        # Remove all existing JS scripts except essential ones
        for script in soup.find_all('script'):
            src = script.get('src', '')
            if 'js/' in src and 'production.js' not in src and 'fontawesome' not in src:
                script.decompose()
        
        # Add production JS if not already present
        body = soup.find('body')
        if body and not soup.find('script', src=re.compile(r'production\.js')):
            # Add production JS at the end of body
            production_js = soup.new_tag('script', src='/js/production.js')
            body.append(production_js)
        
        # Ensure mobile menu toggle exists in navigation
        nav = soup.find('nav')
        if nav and not nav.find(id='menuToggle'):
            nav_container = nav.find(class_='nav-container') or nav.find(class_='container')
            if nav_container:
                # Add menu toggle button
                menu_toggle = soup.new_tag('button', id='menuToggle', **{'class': 'menu-toggle', 'aria-label': 'Toggle menu'})
                for _ in range(3):
                    span = soup.new_tag('span')
                    menu_toggle.append(span)
                
                # Insert after logo
                logo = nav_container.find(class_='nav-logo') or nav_container.find('a')
                if logo:
                    logo.insert_after(menu_toggle)
        
        # Add nav overlay if missing
        if nav and not soup.find(class_='nav-overlay'):
            overlay = soup.new_tag('div', **{'class': 'nav-overlay'})
            nav.insert_after(overlay)
        
        # Update form actions to use proper endpoints
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action', '')
            if 'upload' in action and not action.startswith('/api/'):
                form['action'] = '/api/upload'
            elif 'convert' in action and not action.startswith('/api/'):
                form['action'] = '/api/convert'
        
        # Add scroll to top button if missing
        if not soup.find(id='scrollToTop'):
            scroll_btn = soup.new_tag('button', id='scrollToTop', **{'class': 'scroll-to-top', 'aria-label': 'Scroll to top'})
            icon = soup.new_tag('i', **{'class': 'fas fa-arrow-up'})
            scroll_btn.append(icon)
            if body:
                body.append(scroll_btn)
        
        # Ensure viewport meta tag
        if head:
            viewport = head.find('meta', attrs={'name': 'viewport'})
            if not viewport:
                viewport = soup.new_tag('meta', name='viewport', content='width=device-width, initial-scale=1.0')
                charset = head.find('meta', charset=True)
                if charset:
                    charset.insert_after(viewport)
                else:
                    head.insert(0, viewport)
        
        # Update any broken image paths
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith(('http', '/', 'data:')):
                img['src'] = '/' + src
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"✅ Updated: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {str(e)}")
        return False

def main():
    """Update all HTML files in the project"""
    # Get all HTML files
    html_files = []
    
    # Root directory HTML files
    html_files.extend(glob.glob('*.html'))
    
    # Pages directory
    html_files.extend(glob.glob('pages/*.html'))
    
    # Blog directory
    html_files.extend(glob.glob('blog/*.html'))
    
    # Filter out backup files
    html_files = [f for f in html_files if not f.endswith('.backup') and 'backup' not in f]
    
    print(f"Found {len(html_files)} HTML files to update")
    
    success_count = 0
    for file_path in html_files:
        if update_html_file(file_path):
            success_count += 1
    
    print(f"\n✅ Successfully updated {success_count}/{len(html_files)} files")

if __name__ == '__main__':
    main()