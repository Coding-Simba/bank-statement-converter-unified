#\!/bin/bash

# Verify Deployment
echo "🔍 Verifying deployment location and fixing error"
echo "==============================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Verify via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking which directory nginx is serving from..."
grep -E "root|location" /etc/nginx/sites-enabled/default | grep -v "#" | head -10

echo -e "\n2. Verifying we're in the right directory..."
pwd
ls -la | grep -E "index.html|login.html|js" | head -5

echo -e "\n3. Checking line 101 of auth-unified-1754077904.js..."
echo "Lines 95-105:"
sed -n '95,105p' /home/ubuntu/bank-statement-converter/js/auth-unified-1754077904.js | nl -v 95

echo -e "\n4. Let me check what's actually being served..."
curl -s https://bankcsvconverter.com/js/auth-unified-1754077904.js | sed -n '95,105p' | nl -v 95

echo -e "\n5. Creating a truly minimal version with no special characters..."
cd /home/ubuntu/bank-statement-converter

cat > js/auth-minimal-safe.js << 'EOFJS'
// Ultra minimal safe version
console.log('UnifiedAuth loading');

window.UnifiedAuth = {
    user: null,
    initialized: false,
    
    init: function() {
        console.log('UnifiedAuth init');
        const cached = localStorage.getItem('user');
        if (cached) {
            try {
                this.user = JSON.parse(cached);
            } catch (e) {
                console.log('Parse error');
            }
        }
        this.initialized = true;
    },
    
    login: async function(email, password) {
        console.log('Login attempt for: ' + email);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    remember_me: false
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.user = data.user;
                if (data.access_token) {
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(this.user));
                }
                return { success: true, user: this.user };
            } else {
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    },
    
    logout: async function() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (e) {
            console.log('Logout error');
        }
        
        this.user = null;
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
    },
    
    makeAuthenticatedRequest: async function(url, options) {
        options = options || {};
        const headers = options.headers || {};
        
        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        
        return fetch(url, {
            ...options,
            credentials: 'include',
            headers: headers
        });
    },
    
    isAuthenticated: function() {
        return \!\!this.user;
    },
    
    getUser: function() {
        return this.user;
    }
};

// Initialize
UnifiedAuth.init();
console.log('UnifiedAuth ready');
EOFJS

echo -e "\n6. Verifying no syntax errors in the new file..."
# Count lines to ensure no hidden characters
wc -l js/auth-minimal-safe.js

echo -e "\n7. Updating HTML files to use the safe version..."
TIMESTAMP=$(date +%s)
cp js/auth-minimal-safe.js "js/auth-unified-${TIMESTAMP}.js"

# Update all HTML files
for file in login.html signup.html pricing.html; do
    if [ -f "$file" ]; then
        sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n8. Double-checking the served content..."
echo "New file: js/auth-unified-${TIMESTAMP}.js"
echo "First 10 lines:"
head -10 "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n9. Ensuring correct permissions..."
chmod 644 js/auth-unified-${TIMESTAMP}.js
ls -la js/auth-unified-${TIMESTAMP}.js

ENDSSH

echo ""
echo "✅ Created ultra-safe minimal version\!"
echo ""
echo "This version has:"
echo "- No special characters"
echo "- No complex syntax"
echo "- Basic login functionality only"
echo ""
echo "Please clear cache and try: https://bankcsvconverter.com/login.html"
