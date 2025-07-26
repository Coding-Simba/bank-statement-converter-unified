#!/usr/bin/env python3
"""
Fix all layout issues by adding missing sections to index.html
"""

import os
from bs4 import BeautifulSoup

def add_faq_section(soup):
    """Add FAQ section to index page"""
    faq_html = '''
    <!-- FAQ Section -->
    <section class="content-section" id="faq">
        <div class="container">
            <div class="section-header">
                <h2>Frequently Asked Questions</h2>
                <p>Everything you need to know about our bank statement converter</p>
            </div>
            <div class="faq-section">
                <div class="faq-item">
                    <h3 class="faq-question">What file formats can I upload?</h3>
                    <p class="faq-answer">Currently, we support PDF bank statements. This covers 99% of digital bank statements. If your bank provides statements in a different format, please contact us.</p>
                </div>
                <div class="faq-item">
                    <h3 class="faq-question">How accurate is the conversion?</h3>
                    <p class="faq-answer">Our AI achieves 99.9% accuracy for digital PDF statements. For scanned statements, accuracy depends on scan quality but typically exceeds 98%.</p>
                </div>
                <div class="faq-item">
                    <h3 class="faq-question">Is my data secure?</h3>
                    <p class="faq-answer">Yes! We use 256-bit SSL encryption for all transfers. Your files are automatically deleted immediately after conversion. We never store your financial data.</p>
                </div>
                <div class="faq-item">
                    <h3 class="faq-question">Can I convert multiple statements at once?</h3>
                    <p class="faq-answer">Yes! Pro and Business plans support batch processing. You can upload multiple PDFs and receive a single consolidated CSV or separate files for each statement.</p>
                </div>
                <div class="faq-item">
                    <h3 class="faq-question">What accounting software is supported?</h3>
                    <p class="faq-answer">Our CSV format works with all major accounting software including QuickBooks, Xero, FreshBooks, Wave, and Excel. We also offer custom formatting for specific software needs.</p>
                </div>
            </div>
        </div>
    </section>
    '''
    return faq_html

def add_supported_banks_section(soup):
    """Add supported banks section to index page"""
    banks_html = '''
    <!-- Supported Banks Section -->
    <section class="content-section" id="supported-banks">
        <div class="container">
            <div class="section-header">
                <h2>1000+ Banks Supported</h2>
                <p>Works with statements from banks worldwide</p>
            </div>
            <div class="bank-grid">
                <div class="bank-logo">Chase</div>
                <div class="bank-logo">Bank of America</div>
                <div class="bank-logo">Wells Fargo</div>
                <div class="bank-logo">Citi</div>
                <div class="bank-logo">US Bank</div>
                <div class="bank-logo">PNC</div>
                <div class="bank-logo">Capital One</div>
                <div class="bank-logo">TD Bank</div>
                <div class="bank-logo">Truist</div>
                <div class="bank-logo">Regions</div>
                <div class="bank-logo">Fifth Third</div>
                <div class="bank-logo">KeyBank</div>
                <div class="bank-logo">Huntington</div>
                <div class="bank-logo">Citizens</div>
                <div class="bank-logo">M&T Bank</div>
                <div class="bank-logo">Ally Bank</div>
                <div class="bank-logo">Navy Federal</div>
                <div class="bank-logo">USAA</div>
                <div class="bank-logo">Comerica</div>
                <div class="bank-logo">Zions</div>
            </div>
            <div style="text-align: center; margin-top: 2rem;">
                <p style="color: var(--text-secondary);">And many more including credit unions and international banks</p>
            </div>
        </div>
    </section>
    '''
    return banks_html

def add_pricing_section(soup):
    """Add pricing section to index page"""
    pricing_html = '''
    <!-- Pricing Section -->
    <section class="content-section" id="pricing" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="section-header">
                <h2>Simple, Transparent Pricing</h2>
                <p>Choose the plan that fits your needs</p>
            </div>
            <div class="feature-grid" style="max-width: 1000px; margin: 0 auto;">
                <div class="feature-card" style="text-align: center;">
                    <h3>Free</h3>
                    <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">$0</div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">Perfect for individuals</p>
                    <ul style="list-style: none; text-align: left; margin-bottom: 2rem;">
                        <li style="padding: 0.5rem 0;">✓ 5 conversions per month</li>
                        <li style="padding: 0.5rem 0;">✓ 50+ banks supported</li>
                        <li style="padding: 0.5rem 0;">✓ CSV export</li>
                        <li style="padding: 0.5rem 0;">✓ Basic support</li>
                    </ul>
                    <a href="/pricing.html" class="btn" style="display: block;">Get Started</a>
                </div>
                <div class="feature-card" style="text-align: center; border: 2px solid var(--primary);">
                    <h3>Pro</h3>
                    <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">$19<span style="font-size: 1rem;">/month</span></div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">For professionals</p>
                    <ul style="list-style: none; text-align: left; margin-bottom: 2rem;">
                        <li style="padding: 0.5rem 0;">✓ Unlimited conversions</li>
                        <li style="padding: 0.5rem 0;">✓ 1000+ banks supported</li>
                        <li style="padding: 0.5rem 0;">✓ CSV & Excel export</li>
                        <li style="padding: 0.5rem 0;">✓ Batch processing</li>
                        <li style="padding: 0.5rem 0;">✓ Priority support</li>
                    </ul>
                    <a href="/pricing.html" class="btn" style="display: block;">Start Free Trial</a>
                </div>
                <div class="feature-card" style="text-align: center;">
                    <h3>Business</h3>
                    <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">$49<span style="font-size: 1rem;">/month</span></div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">For teams & businesses</p>
                    <ul style="list-style: none; text-align: left; margin-bottom: 2rem;">
                        <li style="padding: 0.5rem 0;">✓ Everything in Pro</li>
                        <li style="padding: 0.5rem 0;">✓ API access</li>
                        <li style="padding: 0.5rem 0;">✓ Team collaboration</li>
                        <li style="padding: 0.5rem 0;">✓ Custom formats</li>
                        <li style="padding: 0.5rem 0;">✓ Dedicated support</li>
                    </ul>
                    <a href="/pricing.html" class="btn" style="display: block;">Contact Sales</a>
                </div>
            </div>
        </div>
    </section>
    '''
    return pricing_html

def fix_index_layout():
    """Fix the index.html layout by adding missing sections"""
    index_path = '/Users/MAC/chrome/bank-statement-converter-unified/index.html'
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the main content area
    main = soup.find('main') or soup.find('div', id='main')
    
    if not main:
        print("Could not find main content area")
        return
    
    # Check if sections already exist
    has_faq = soup.find(id='faq') is not None
    has_banks = soup.find(id='supported-banks') is not None
    has_pricing = soup.find(id='pricing') is not None
    
    # Find a good insertion point (before footer or at end of main)
    footer = soup.find('footer')
    
    if not has_banks:
        banks_soup = BeautifulSoup(add_supported_banks_section(soup), 'html.parser')
        if footer:
            footer.insert_before(banks_soup)
        else:
            main.append(banks_soup)
    
    if not has_pricing:
        pricing_soup = BeautifulSoup(add_pricing_section(soup), 'html.parser')
        if footer:
            footer.insert_before(pricing_soup)
        else:
            main.append(pricing_soup)
    
    if not has_faq:
        faq_soup = BeautifulSoup(add_faq_section(soup), 'html.parser')
        if footer:
            footer.insert_before(faq_soup)
        else:
            main.append(faq_soup)
    
    # Write the updated content
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"✅ Updated index.html with missing sections")
    print(f"   - FAQ section: {'already exists' if has_faq else 'added'}")
    print(f"   - Supported Banks section: {'already exists' if has_banks else 'added'}")
    print(f"   - Pricing section: {'already exists' if has_pricing else 'added'}")

if __name__ == "__main__":
    fix_index_layout()