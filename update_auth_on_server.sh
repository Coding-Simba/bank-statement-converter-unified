#!/bin/bash
cd /home/ubuntu/bank-statement-converter/frontend

echo "Updating dashboard.html..."
sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' dashboard.html
if ! grep -q "auth-fixed.js" dashboard.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' dashboard.html
fi

echo "Checking other important pages..."
for file in login.html signup.html; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        sed -i '/<script src="\/js\/auth-global\.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-persistent\.js"><\/script>/d' "$file"
        sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' "$file"
        if ! grep -q "auth-fixed.js" "$file"; then
            sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' "$file"
        fi
    fi
done

echo "Done! Auth-fixed.js has been added to all pages."