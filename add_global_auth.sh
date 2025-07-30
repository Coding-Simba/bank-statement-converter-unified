#!/bin/bash

# Add global authentication script to all HTML pages

echo "Adding global authentication to all pages..."

# Find all HTML files and add auth-global.js before production.js
find . -name "*.html" -type f ! -path "./node_modules/*" ! -path "./.git/*" | while read file; do
    # Check if auth-global.js is already included
    if ! grep -q "auth-global.js" "$file"; then
        # Check if the file has production.js
        if grep -q "production.js" "$file"; then
            # Add auth-global.js before production.js
            sed -i '' '/<script src="\/js\/production.js"><\/script>/i\
    <script src="/js/auth-global.js"></script>' "$file"
            echo "✓ Added to: $file"
        elif grep -q "</body>" "$file"; then
            # If no production.js, add before </body>
            sed -i '' '/<\/body>/i\
    <script src="/js/auth-global.js"></script>' "$file"
            echo "✓ Added to: $file"
        fi
    else
        echo "- Already has auth: $file"
    fi
done

echo -e "\nDone! Global authentication added to all pages."