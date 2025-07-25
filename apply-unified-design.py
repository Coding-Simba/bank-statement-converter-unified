#!/usr/bin/env python3
"""Apply unified design to all bank statement converter pages"""

import os
import re
from bs4 import BeautifulSoup
import shutil
from datetime import datetime

# Bank information for customization
BANKS = {
    'chase-bank': 'Chase Bank',
    'bank-of-america': 'Bank of America',
    'wells-fargo': 'Wells Fargo',
    'citi-bank': 'Citi Bank',
    'capital-one': 'Capital One',
    'us-bank': 'US Bank',
    'pnc-bank': 'PNC Bank',
    'td-bank': 'TD Bank',
    'regions-bank': 'Regions Bank',
    'truist-bank': 'Truist Bank',
    'fifth-third-bank': 'Fifth Third Bank',
    'keybank': 'KeyBank',
    'suntrust-bank': 'SunTrust Bank',
    'mt-bank': 'M&T Bank',
    'huntington-bank': 'Huntington Bank',
    'comerica-bank': 'Comerica Bank',
    'zions-bank': 'Zions Bank',
    'usaa-bank': 'USAA Bank',
    'navy-federal': 'Navy Federal Credit Union',
    'citizens-bank': 'Citizens Bank',
    'ally-bank': 'Ally Bank'
}

def backup_file(filepath):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    return backup_path

def read_template():
    """Read the unified template"""
    template_path = '/Users/MAC/chrome/bank-statement-converter/frontend/templates/bank-page-template.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def customize_template(template, bank_slug, bank_name):
    """Replace placeholders in template with bank-specific information"""
    # Replace placeholders
    customized = template.replace('[BANK_NAME]', bank_name)
    customized = customized.replace('[BANK_NAME_LOWER]', bank_name.lower())
    customized = customized.replace('[BANK_SLUG]', bank_slug)
    
    return customized

def update_bank_page(filepath, bank_slug, bank_name):
    """Update a bank page to use unified design"""
    try:
        # Read template
        template = read_template()
        
        # Customize template
        new_content = customize_template(template, bank_slug, bank_name)
        
        # Read existing file to preserve any unique content
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Parse existing content
        existing_soup = BeautifulSoup(existing_content, 'html.parser')
        
        # Extract any unique FAQ content if exists
        existing_faqs = existing_soup.find_all(class_='faq-item')
        if existing_faqs and len(existing_faqs) > 4:
            # Page has custom FAQs, preserve them
            new_soup = BeautifulSoup(new_content, 'html.parser')
            faq_section = new_soup.find(class_='faq-section')
            if faq_section:
                # Clear default FAQs
                faq_section.clear()
                # Add existing FAQs
                for faq in existing_faqs:
                    # Standardize FAQ structure
                    question = faq.find(['h3', 'h4', 'div'], class_=re.compile('question|title'))
                    answer = faq.find(['p', 'div'], class_=re.compile('answer|content'))
                    
                    if question and answer:
                        new_faq = new_soup.new_tag('div', class_='faq-item')
                        new_q = new_soup.new_tag('h3', class_='faq-question')
                        new_q.string = question.get_text(strip=True)
                        new_a = new_soup.new_tag('p', class_='faq-answer')
                        new_a.string = answer.get_text(strip=True)
                        new_faq.append(new_q)
                        new_faq.append(new_a)
                        faq_section.append(new_faq)
                
                new_content = str(new_soup.prettify())
        
        # Backup original file
        backup_path = backup_file(filepath)
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Updated: {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {filepath}: {str(e)}")
        return False

def update_css_references():
    """Update all pages to use unified-styles.css"""
    pages_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/pages'
    
    for filename in os.listdir(pages_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(pages_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update CSS references
                content = re.sub(
                    r'<link\s+rel="stylesheet"\s+href="[^"]*(?:modern-style|style-seo|styles|main)\.css"[^>]*>',
                    '<link rel="stylesheet" href="../css/unified-styles.css">',
                    content,
                    flags=re.IGNORECASE
                )
                
                # Remove inline styles
                content = re.sub(
                    r'<style[^>]*>[\s\S]*?</style>',
                    '',
                    content,
                    flags=re.IGNORECASE
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"Error updating CSS in {filename}: {e}")

def main():
    print("🎨 Applying Unified Design to All Bank Pages")
    print("=" * 60)
    
    # First update CSS references
    print("\n📝 Updating CSS references...")
    update_css_references()
    
    # Then apply template to bank pages
    print("\n🏦 Updating bank pages with unified template...")
    pages_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/pages'
    
    success_count = 0
    total_count = 0
    
    for filename in os.listdir(pages_dir):
        if filename.endswith('-statement-converter.html') or filename.endswith('-converter.html'):
            # Extract bank slug from filename
            bank_slug = filename.replace('-statement-converter.html', '').replace('-converter.html', '')
            
            if bank_slug in BANKS:
                total_count += 1
                filepath = os.path.join(pages_dir, filename)
                
                if update_bank_page(filepath, bank_slug, BANKS[bank_slug]):
                    success_count += 1
    
    # Update city pages to use unified styles
    print("\n🏙️ Updating city pages...")
    city_pages = [
        'new-york', 'los-angeles', 'chicago', 'houston', 'dallas',
        'phoenix', 'philadelphia', 'san-antonio', 'san-diego', 'boston', 'seattle'
    ]
    
    for city in city_pages:
        filepath = os.path.join(pages_dir, f'{city}-bank-statement-converter.html')
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update CSS reference
                content = re.sub(
                    r'<link\s+rel="stylesheet"\s+href="[^"]*\.css"[^>]*>',
                    '<link rel="stylesheet" href="../css/unified-styles.css">',
                    content
                )
                
                # Remove inline styles
                content = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Updated city page: {city}")
                
            except Exception as e:
                print(f"❌ Error updating {city}: {e}")
    
    # Update blog pages
    print("\n📚 Updating blog pages...")
    blog_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/blog'
    
    for filename in os.listdir(blog_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(blog_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Update CSS reference
                content = re.sub(
                    r'<link\s+rel="stylesheet"\s+href="[^"]*\.css"[^>]*>',
                    '<link rel="stylesheet" href="../css/unified-styles.css">',
                    content
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Updated blog: {filename}")
                
            except Exception as e:
                print(f"❌ Error updating {filename}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Successfully updated {success_count}/{total_count} bank pages")
    print("✅ Updated all city pages to use unified styles")
    print("✅ Updated all blog pages to use unified styles")
    print("\n🎉 Unified design applied successfully!")
    print("\nNext steps:")
    print("1. Test the updated pages in your browser")
    print("2. Check that all functionality works correctly")
    print("3. Original files have been backed up with timestamps")

if __name__ == "__main__":
    main()