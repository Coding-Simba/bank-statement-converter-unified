#!/bin/bash

# Fix escaped operators in JavaScript and Python files
echo "🔍 Checking for escaped operators..."

# Check local files
echo "Checking local files..."
find . -name "*.js" -o -name "*.py" | while read file; do
    if grep -q '\\!' "$file" 2>/dev/null; then
        echo "Fixing: $file"
        sed -i.bak 's/\\!/!/g' "$file"
        rm "${file}.bak"
    fi
done

# Fix on server
echo -e "\nFixing server files..."
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 << 'EOF'
    # Fix backend Python files
    find /home/ubuntu/backend -name "*.py" -exec grep -l '\\!' {} \; | while read file; do
        echo "Fixing: $file"
        sed -i 's/\\!/!/g' "$file"
    done
    
    # Fix frontend JS files
    find /home/ubuntu/bank-statement-converter/frontend -name "*.js" -exec grep -l '\\!' {} \; | while read file; do
        echo "Fixing: $file"
        sed -i 's/\\!/!/g' "$file"
    done
EOF

echo "✅ Done! All escaped operators fixed."