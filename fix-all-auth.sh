#!/bin/bash
# Fix authentication across all pages

# List of all HTML pages that need auth
pages=(
    "index.html"
    "pricing.html"
    "dashboard.html"
    "login.html"
    "signup.html"
    "convert-pdf.html"
    "merge-statements.html"
    "split-by-date.html"
    "analyze-transactions.html"
    "about.html"
    "contact.html"
    "blog.html"
    "business.html"
    "personal.html"
    "accountants.html"
    "bookkeepers.html"
)

for page in "${pages[@]}"; do
    if [ -f "/home/ubuntu/bank-statement-converter/frontend/$page" ]; then
        echo "Processing $page..."
        
        # Check if auth.js is already included
        if ! grep -q "auth.js" "/home/ubuntu/bank-statement-converter/frontend/$page"; then
            # Add auth scripts before </body>
            sudo sed -i '/<\/body>/i\    <script src="/js/api-config.js"></script>' "/home/ubuntu/bank-statement-converter/frontend/$page"
            sudo sed -i '/<\/body>/i\    <script src="/js/auth.js"></script>' "/home/ubuntu/bank-statement-converter/frontend/$page"
            sudo sed -i '/<\/body>/i\    <script src="/js/auth-navigation.js"></script>' "/home/ubuntu/bank-statement-converter/frontend/$page"
        fi
        
        # Ensure api-config.js comes before auth.js
        if ! grep -q "api-config.js" "/home/ubuntu/bank-statement-converter/frontend/$page"; then
            sudo sed -i '/auth.js/i\    <script src="/js/api-config.js"></script>' "/home/ubuntu/bank-statement-converter/frontend/$page"
        fi
        
        # Ensure auth-navigation.js comes after auth.js
        if ! grep -q "auth-navigation.js" "/home/ubuntu/bank-statement-converter/frontend/$page"; then
            sudo sed -i '/auth.js/a\    <script src="/js/auth-navigation.js"></script>' "/home/ubuntu/bank-statement-converter/frontend/$page"
        fi
    fi
done

echo "Auth integration complete!"