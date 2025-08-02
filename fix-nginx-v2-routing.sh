#!/bin/bash

# Fix nginx to route v2 API endpoints
echo "🔧 Fixing nginx v2 API routing..."

ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 << 'EOF'
    # Backup current config
    sudo cp /etc/nginx/sites-enabled/bank-converter /etc/nginx/sites-enabled/bank-converter.backup.$(date +%s)
    
    # Create fixed config
    sudo tee /tmp/nginx-fix.conf << 'NGINX_CONFIG'
    location /v2/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /health {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
NGINX_CONFIG
    
    # Check if v2 location already exists
    if ! grep -q "location /v2/" /etc/nginx/sites-enabled/bank-converter; then
        # Find the line with "location /api/" and add v2 config after its closing brace
        sudo sed -i '/location \/api\/ {/,/^    }/!b; /^    }/a\\n    # Cookie auth v2 API endpoints' /etc/nginx/sites-enabled/bank-converter
        
        # Insert the v2 location block
        sudo sed -i '/# Cookie auth v2 API endpoints/r /tmp/nginx-fix.conf' /etc/nginx/sites-enabled/bank-converter
    fi
    
    # Test configuration
    sudo nginx -t
    
    # If test passes, reload nginx
    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        echo "✅ Nginx reloaded successfully"
    else
        echo "❌ Nginx config test failed"
        exit 1
    fi
EOF

echo "🧪 Testing v2 endpoints..."
sleep 2

# Test v2 login endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://bankcsvconverter.com/v2/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}')

if [ "$STATUS" = "401" ]; then
    echo "✅ V2 login endpoint working (Status: $STATUS)"
else
    echo "❌ V2 login endpoint not working (Status: $STATUS)"
fi

# Test health endpoint
HEALTH=$(curl -s https://bankcsvconverter.com/health | grep -o '"status":"healthy"' || echo "")
if [ -n "$HEALTH" ]; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint not returning JSON"
fi