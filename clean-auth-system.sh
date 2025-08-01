#\!/bin/bash

# Clean Auth System
echo "🧹 Cleaning up authentication system"
echo "===================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Clean via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Remove all conflicting auth scripts from dashboard-modern.html..."
# Remove all auth-related script tags except our new one
sed -i '/auth-check-fix\.js/d' dashboard-modern.html
sed -i '/auth-unified.*\.js/d' dashboard-modern.html
sed -i '/auth-working\.js/d' dashboard-modern.html
sed -i '/auth-navigation\.js/d' dashboard-modern.html

echo -e "\n2. Add only the necessary scripts to dashboard-modern.html..."
# Add our working auth check before </body>
sed -i '/<\/body>/i <script>\n// Simple auth check\nif (\!localStorage.getItem("access_token") || \!localStorage.getItem("user")) {\n    window.location.href = "/login.html";\n}\n</script>' dashboard-modern.html

echo -e "\n3. Do the same for settings.html..."
sed -i '/auth-.*\.js/d' settings.html
sed -i '/UnifiedAuth/d' settings.html
sed -i '/<\/body>/i <script>\n// Simple auth check\nif (\!localStorage.getItem("access_token") || \!localStorage.getItem("user")) {\n    window.location.href = "/login.html";\n}\n</script>' settings.html

echo -e "\n4. Update pricing.html to use simple auth..."
sed -i '/auth-unified.*\.js/d' pricing.html
sed -i '/stripe-integration\.js/d' pricing.html

# Re-add stripe integration with proper auth
sed -i '/<\/body>/i <script src="/js/stripe-integration.js"></script>' pricing.html

echo -e "\n5. Create a simple global auth utility..."
cat > js/auth-simple.js << 'EOFJS'
// Simple Auth Utility
window.auth = {
    isAuthenticated: function() {
        return \!\!(localStorage.getItem('access_token') && localStorage.getItem('user'));
    },
    
    getToken: function() {
        return localStorage.getItem('access_token');
    },
    
    getUser: function() {
        try {
            return JSON.parse(localStorage.getItem('user') || 'null');
        } catch (e) {
            return null;
        }
    },
    
    logout: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
        window.location.href = '/login.html';
    },
    
    requireAuth: function() {
        if (\!this.isAuthenticated()) {
            window.location.href = '/login.html';
        }
    }
};

// Auto-check on protected pages
if (window.location.pathname.includes('dashboard') || 
    window.location.pathname.includes('settings')) {
    auth.requireAuth();
}
EOFJS

echo -e "\n6. Add the simple auth to all pages that need it..."
for file in dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Add simple auth script
        sed -i "/<\/body>/i <script src=\"/js/auth-simple.js\"></script>" "$file"
        echo "Added auth-simple.js to $file"
    fi
done

echo -e "\n7. Fix stripe integration to use simple auth..."
cat > js/stripe-integration-fixed.js << 'EOFJS'
// Stripe Integration with Simple Auth
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Stripe] Initializing...');
    
    // Price IDs mapping
    const PRICE_IDS = {
        starter: {
            monthly: 'price_1RqZtaKwQLBjGTW9w20V3Hst',
            yearly: 'price_1RqZubKwQLBjGTW9deSoEAWV'
        },
        professional: {
            monthly: 'price_1RqZuNKwQLBjGTW9VJ9gJaie',
            yearly: 'price_1RqZv6KwQLBjGTW9iONZoqRU'
        },
        enterprise: {
            monthly: 'price_1RqZvRKwQLBjGTW9TlzBSdaL',
            yearly: 'price_1RqZvqKwQLBjGTW92E0Ef1Id'
        }
    };
    
    // Handle buy button clicks
    document.querySelectorAll('.buy-btn, .btn-primary').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Check if user is authenticated
            if (\!localStorage.getItem('access_token')) {
                alert('Please login to purchase a subscription');
                window.location.href = '/login.html';
                return;
            }
            
            const plan = this.getAttribute('data-plan') || 'starter';
            const period = this.getAttribute('data-period') || 'monthly';
            const priceId = PRICE_IDS[plan]?.[period];
            
            if (\!priceId) {
                alert('Invalid plan selected');
                return;
            }
            
            // Disable button
            this.disabled = true;
            this.textContent = 'Processing...';
            
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/stripe/create-checkout-session', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ price_id: priceId })
                });
                
                const data = await response.json();
                
                if (response.ok && data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    alert(data.detail || 'Failed to start checkout');
                    this.disabled = false;
                    this.textContent = 'Get Started';
                }
            } catch (error) {
                alert('Network error: ' + error.message);
                this.disabled = false;
                this.textContent = 'Get Started';
            }
        });
    });
});
EOFJS

echo -e "\n8. Replace stripe integration with fixed version..."
cp js/stripe-integration-fixed.js js/stripe-integration.js

echo -e "\n✅ Authentication system cleaned up\!"
echo ""
echo "What I did:"
echo "1. Removed all conflicting auth scripts"
echo "2. Added simple auth checks to protected pages"
echo "3. Created auth-simple.js for basic auth utilities"
echo "4. Fixed Stripe integration to use simple auth"
echo ""
echo "Now try logging in again at:"
echo "https://bankcsvconverter.com/login.html"

ENDSSH
