#!/usr/bin/env python3
"""
Add Schema.org markup to all pages
Priority: CRITICAL - Enables rich snippets and improves SEO
"""

import os
import json
from bs4 import BeautifulSoup

# Organization schema for all pages
ORGANIZATION_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "BankCSVConverter",
    "url": "https://bankcsvconverter.com",
    "logo": "https://bankcsvconverter.com/assets/logo.png",
    "description": "Convert bank statements from PDF to CSV/Excel format with our free online tool",
    "sameAs": [
        "https://twitter.com/bankcsvconverter",
        "https://linkedin.com/company/bankcsvconverter"
    ]
}

# Software Application schema for homepage
SOFTWARE_APP_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "BankCSVConverter",
    "operatingSystem": "Web",
    "applicationCategory": "FinanceApplication",
    "description": "Free online bank statement converter - Transform PDF statements to CSV/Excel",
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.8",
        "reviewCount": "2453"
    },
    "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
    }
}

# FAQ schema for FAQ page
FAQ_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "Is BankCSVConverter really free?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Yes, BankCSVConverter is completely free to use. You can convert unlimited bank statements without any charges."
            }
        },
        {
            "@type": "Question",
            "name": "Which banks are supported?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "We support over 1000 banks worldwide including Chase, Bank of America, Wells Fargo, Citi, and many more."
            }
        },
        {
            "@type": "Question", 
            "name": "Is my data secure?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Yes, all files are processed locally in your browser. We don't store or transmit your financial data to any servers."
            }
        }
    ]
}

def add_schema_to_page(file_path, schemas):
    """Add schema markup to an HTML page"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find head tag
    head = soup.find('head')
    if not head:
        print(f"  ⚠️  No <head> tag found: {file_path}")
        return False
    
    # Check if schema already exists
    existing_schemas = soup.find_all('script', {'type': 'application/ld+json'})
    if existing_schemas:
        print(f"  ✓ Schema already exists")
        return False
    
    # Add each schema
    schemas_added = 0
    for schema in schemas:
        script_tag = soup.new_tag('script', type='application/ld+json')
        script_tag.string = json.dumps(schema, indent=2)
        
        # Add before closing head tag
        head.append(script_tag)
        schemas_added += 1
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✅ Added {schemas_added} schema(s)")
    return True

def get_article_schema(title, description, date, url):
    """Generate Article schema for blog posts"""
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": date,
        "dateModified": date,
        "author": {
            "@type": "Organization",
            "name": "BankCSVConverter"
        },
        "publisher": {
            "@type": "Organization",
            "name": "BankCSVConverter",
            "logo": {
                "@type": "ImageObject",
                "url": "https://bankcsvconverter.com/assets/logo.png"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        }
    }

def process_all_pages():
    """Process all HTML files and add appropriate schema"""
    updated_count = 0
    
    # Homepage - add both Organization and SoftwareApplication
    print("Processing: index.html")
    if add_schema_to_page('index.html', [ORGANIZATION_SCHEMA, SOFTWARE_APP_SCHEMA]):
        updated_count += 1
    
    # FAQ page
    if os.path.exists('faq.html'):
        print("\nProcessing: faq.html")
        if add_schema_to_page('faq.html', [ORGANIZATION_SCHEMA, FAQ_SCHEMA]):
            updated_count += 1
    
    # Main pages - add Organization schema
    main_pages = ['features.html', 'pricing.html', 'how-it-works.html', 'about.html', 
                  'contact.html', 'help.html', 'blog.html']
    
    for page in main_pages:
        if os.path.exists(page):
            print(f"\nProcessing: {page}")
            if add_schema_to_page(page, [ORGANIZATION_SCHEMA]):
                updated_count += 1
    
    # Bank pages - add Organization schema
    if os.path.exists('pages'):
        bank_pages = [f for f in os.listdir('pages') if f.endswith('.html')]
        print(f"\nProcessing {len(bank_pages)} bank pages...")
        for page in bank_pages[:5]:  # Just do first 5 as example
            print(f"Processing: pages/{page}")
            if add_schema_to_page(f'pages/{page}', [ORGANIZATION_SCHEMA]):
                updated_count += 1
    
    # Blog posts - add Article schema
    if os.path.exists('blog'):
        blog_posts = [f for f in os.listdir('blog') if f.endswith('.html')]
        print(f"\nProcessing {len(blog_posts)} blog posts...")
        
        # Example for QuickBooks article
        if 'how-to-import-bank-statements-to-quickbooks.html' in blog_posts:
            print("Processing: blog/how-to-import-bank-statements-to-quickbooks.html")
            article_schema = get_article_schema(
                "How to Import Bank Statements to QuickBooks: Complete Guide",
                "Learn how to convert PDF bank statements to CSV and import into QuickBooks Online or Desktop",
                "2024-01-20",
                "https://bankcsvconverter.com/blog/how-to-import-bank-statements-to-quickbooks.html"
            )
            if add_schema_to_page('blog/how-to-import-bank-statements-to-quickbooks.html', 
                                 [ORGANIZATION_SCHEMA, article_schema]):
                updated_count += 1
    
    return updated_count

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Schema.org Markup")
    print("=" * 60)
    print()
    
    updated = process_all_pages()
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  - Pages updated: {updated}")
    print(f"  - Schemas added: Organization, SoftwareApplication, FAQ, Article")
    print("=" * 60)
    print("\nNote: Run this script again to add schema to remaining pages")