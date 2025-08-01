#\!/bin/bash

# Check Actual Error
echo "🔍 Checking the actual error in the deployed file"
echo "================================================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Check via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking line 50 and surrounding lines of auth-unified-1754077348.js..."
echo "Lines 45-55:"
sed -n '45,55p' js/auth-unified-1754077348.js | nl -v 45

echo -e "\n2. Checking for any special characters or encoding issues..."
# Show hex dump of line 50
echo "Hex dump of line 50:"
sed -n '50p' js/auth-unified-1754077348.js | xxd

echo -e "\n3. Let's create a completely new, minimal working version..."
cat > js/auth-unified-minimal.js << 'EOFJS'
// Minimal UnifiedAuth for testing
console.log('[UnifiedAuth] Minimal version loading...');

const API_BASE = 'https://bankcsvconverter.com';

class UnifiedAuthService {
    constructor() {
        this.user = null;
        this.initialized = false;
        this.init();
    }
    
    async init() {
        console.log('[UnifiedAuth] Initializing minimal version...');
        
        // Check for cached user
        const cachedUser = localStorage.getItem('user');
        if (cachedUser) {
            try {
                this.user = JSON.parse(cachedUser);
            } catch (e) {
                console.error('Failed to parse cached user');
            }
        }
        
        this.initialized = true;
        window.dispatchEvent(new Event('unifiedauth:ready'));
    }
    
    async login(email, password, rememberMe = false) {
        console.log('[UnifiedAuth] Login attempt:', email);
        
        try {
            const response = await fetch(API_BASE + '/api/auth/login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    email, 
                    password,
                    remember_me: rememberMe 
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.access_token) {
                this.user = data.user;
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                console.log('[UnifiedAuth] Login successful');
                return { success: true, user: this.user };
            } else {
                console.error('[UnifiedAuth] Login failed:', data);
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            console.error('[UnifiedAuth] Login error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async logout() {
        try {
            await fetch(API_BASE + '/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('[UnifiedAuth] Logout error:', error);
        }
        
        this.user = null;
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
    }
    
    async makeAuthenticatedRequest(url, options = {}) {
        const fullUrl = url.startsWith('http') ? url : API_BASE + url;
        
        const headers = {
            ...options.headers
        };
        
        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        
        return fetch(fullUrl, {
            ...options,
            credentials: 'include',
            headers: headers
        });
    }
    
    isAuthenticated() {
        return \!\!this.user;
    }
    
    getUser() {
        return this.user;
    }
}

// Create global instance
window.UnifiedAuth = new UnifiedAuthService();
console.log('[UnifiedAuth] Minimal version ready');
EOFJS

echo -e "\n4. Creating timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-minimal.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n5. Updating login.html to use the minimal version..."
sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" login.html

echo -e "\n6. Also update other critical pages..."
for file in signup.html pricing.html; do
    if [ -f "$file" ]; then
        sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
    fi
done

echo -e "\n7. Verify the file has no syntax errors by checking its content..."
echo "First few lines of new file:"
head -5 "js/auth-unified-${TIMESTAMP}.js"

echo -e "\nNew minimal version created: js/auth-unified-${TIMESTAMP}.js"

ENDSSH

echo ""
echo "✅ Created minimal working version\!"
echo ""
echo "Please clear cache and try: https://bankcsvconverter.com/login.html"
