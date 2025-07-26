#!/usr/bin/env python3
"""
Add Open Graph and Twitter meta tags to all pages
Priority: MEDIUM - Improves social sharing and CTR
"""

import os
from bs4 import BeautifulSoup

def get_meta_tags(title, description, url, image_url=None):
    """Generate Open Graph and Twitter meta tags"""
    if not image_url:
        image_url = "https://bankcsvconverter.com/assets/og-image.png"
    
    return [
        # Open Graph tags
        {"property": "og:title", "content": title},
        {"property": "og:description", "content": description},
        {"property": "og:url", "content": url},
        {"property": "og:type", "content": "website"},
        {"property": "og:image", "content": image_url},
        {"property": "og:site_name", "content": "BankCSVConverter"},
        
        # Twitter Card tags
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:title", "content": title},
        {"name": "twitter:description", "content": description},
        {"name": "twitter:image", "content": image_url},
        {"name": "twitter:site", "content": "@bankcsvconverter"}
    ]

def add_meta_tags_to_page(file_path):
    """Add meta tags to an HTML page"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check if OG tags already exist
    existing_og = soup.find('meta', {'property': 'og:title'})
    if existing_og:
        print(f"  ✓ Meta tags already exist")
        return False
    
    # Get page info
    title_tag = soup.find('title')
    title = title_tag.text if title_tag else "BankCSVConverter - PDF to CSV/Excel"
    
    desc_tag = soup.find('meta', {'name': 'description'})
    description = desc_tag.get('content', '') if desc_tag else "Convert bank statements from PDF to CSV/Excel instantly. Free online converter for 1000+ banks."
    
    # Generate URL based on file path
    if file_path == 'index.html':
        url = "https://bankcsvconverter.com/"
    else:
        url = f"https://bankcsvconverter.com/{file_path}"
    
    # Get meta tags
    meta_tags = get_meta_tags(title, description, url)
    
    # Find head tag
    head = soup.find('head')
    if not head:
        print(f"  ⚠️  No <head> tag found")
        return False
    
    # Add after existing meta tags
    last_meta = None
    for existing_meta in head.find_all('meta'):
        last_meta = existing_meta
    
    # Insert new meta tags
    for tag_data in meta_tags:
        new_tag = soup.new_tag('meta')
        for key, value in tag_data.items():
            new_tag[key] = value
        
        if last_meta:
            last_meta.insert_after(new_tag)
            last_meta = new_tag
        else:
            head.append(new_tag)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✅ Added {len(meta_tags)} meta tags")
    return True

def process_key_pages():
    """Process key pages first"""
    updated_count = 0
    
    key_pages = [
        'index.html',
        'pricing.html',
        'features.html',
        'how-it-works.html',
        'blog.html',
        'about.html',
        'contact.html'
    ]
    
    print("Processing key pages...")
    for page in key_pages:
        if os.path.exists(page):
            print(f"\nProcessing: {page}")
            if add_meta_tags_to_page(page):
                updated_count += 1
    
    # Process a few bank pages as examples
    if os.path.exists('pages'):
        bank_pages = ['pages/chase-bank-statement-converter.html',
                      'pages/bank-of-america-statement-converter.html',
                      'pages/wells-fargo-statement-converter.html']
        
        print("\n\nProcessing bank pages...")
        for page in bank_pages:
            if os.path.exists(page):
                print(f"\nProcessing: {page}")
                if add_meta_tags_to_page(page):
                    updated_count += 1
    
    # Process a blog post
    if os.path.exists('blog/how-to-import-bank-statements-to-quickbooks.html'):
        print("\n\nProcessing blog post...")
        print("Processing: blog/how-to-import-bank-statements-to-quickbooks.html")
        if add_meta_tags_to_page('blog/how-to-import-bank-statements-to-quickbooks.html'):
            updated_count += 1
    
    return updated_count

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Open Graph and Twitter Meta Tags")
    print("=" * 60)
    print()
    
    updated = process_key_pages()
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  - Pages updated: {updated}")
    print(f"  - Meta tags added per page: 11")
    print("=" * 60)
    print("\nBenefits:")
    print("  ✓ Better social media sharing appearance")
    print("  ✓ Improved click-through rates from social")
    print("  ✓ Enhanced SEO signals")
    print("  ✓ Professional appearance in link previews")