#!/bin/bash

cd /home/ubuntu/bank-statement-converter-unified/backend

# Create .env file
cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./production.db

# JWT Settings
JWT_SECRET_KEY=5ho6Z9uqZcfmQiD6vhZAajKYiKBk5hKRBvNgQYjvvjQ

# OAuth Settings (to be configured)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# URLs
FRONTEND_URL=https://bankcsvconverter.com
API_URL=https://bankcsvconverter.com

# OAuth Redirect URIs
GOOGLE_REDIRECT_URI=https://bankcsvconverter.com/api/auth/google/callback
MICROSOFT_REDIRECT_URI=https://bankcsvconverter.com/api/auth/microsoft/callback
EOF

echo "✅ .env file created"

# Restart the backend
sudo systemctl restart bank-converter-backend
echo "✅ Backend restarted"

sleep 3
sudo systemctl status bank-converter-backend --no-pager | head -20