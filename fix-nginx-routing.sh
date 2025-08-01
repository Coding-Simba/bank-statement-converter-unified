#!/bin/bash

echo "🔧 Fixing nginx routing and authentication..."

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
KEY_PATH="$HOME/Downloads/bank-statement-converter.pem"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    echo "📝 Adding dashboard routing to nginx..."
    
    # Create nginx configuration update
    sudo tee /tmp/nginx-routes.conf << 'NGINX'
    # Redirect /dashboard to modern dashboard
    location = /dashboard {
        return 301 /dashboard-modern.html;
    }
    
    # Redirect /dashboard/ to modern dashboard
    location = /dashboard/ {
        return 301 /dashboard-modern.html;
    }
    
    # Handle common routes without .html
    location = /login {
        return 301 /login.html;
    }
    
    location = /signup {
        return 301 /signup.html;
    }
    
    location = /settings {
        return 301 /settings.html;
    }
    
    location = /pricing {
        return 301 /pricing.html;
    }
    
    location = /convert-pdf {
        return 301 /convert-pdf.html;
    }
NGINX
    
    # Backup current nginx config
    sudo cp /etc/nginx/sites-available/bank-converter /etc/nginx/sites-available/bank-converter.backup
    
    # Insert routes into nginx config (before the last closing brace)
    sudo sed -i '/location \/ {/i\
    # User-friendly URL redirects\
    location = /dashboard {\
        return 301 /dashboard-modern.html;\
    }\
    \
    location = /dashboard/ {\
        return 301 /dashboard-modern.html;\
    }\
    \
    location = /login {\
        return 301 /login.html;\
    }\
    \
    location = /signup {\
        return 301 /signup.html;\
    }\
    \
    location = /settings {\
        return 301 /settings.html;\
    }\
    \
    location = /pricing {\
        return 301 /pricing.html;\
    }\
    ' /etc/nginx/sites-available/bank-converter
    
    # Test nginx configuration
    sudo nginx -t
    
    # Reload nginx
    sudo nginx -s reload
    
    echo "✅ Nginx routing fixed!"
    
    # Also check if auth persistence issue is cookie-related
    echo ""
    echo "🍪 Checking cookie configuration..."
    grep "COOKIE_DOMAIN" /home/ubuntu/backend/api/auth_cookie.py
    
ENDSSH

echo ""
echo "🎉 Routing fixed! Now:"
echo "- /dashboard → dashboard-modern.html"
echo "- /login → login.html"
echo "- /signup → signup.html"
echo "- etc."
echo ""
echo "Test: https://bankcsvconverter.com/dashboard"