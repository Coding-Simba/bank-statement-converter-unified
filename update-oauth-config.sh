#!/bin/bash

# Script to update OAuth configuration on server
echo "📝 Updating OAuth Configuration..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Please enter your OAuth credentials:${NC}"
echo ""

# Get Google credentials
read -p "Enter Google Client ID: " GOOGLE_CLIENT_ID
read -sp "Enter Google Client Secret: " GOOGLE_CLIENT_SECRET
echo ""

# Get Microsoft credentials
read -p "Enter Microsoft Client ID: " MICROSOFT_CLIENT_ID
read -sp "Enter Microsoft Client Secret: " MICROSOFT_CLIENT_SECRET
echo ""

# Create updated .env content
cat > /tmp/oauth-env-update.txt << EOF
# Update these lines in your .env file:
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET
MICROSOFT_CLIENT_ID=$MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET=$MICROSOFT_CLIENT_SECRET
EOF

echo ""
echo -e "${GREEN}✅ OAuth configuration prepared!${NC}"
echo ""
echo "Now SSH into your server and update the .env file:"
echo ""
echo -e "${YELLOW}ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83${NC}"
echo ""
echo "Then edit the .env file:"
echo -e "${YELLOW}cd /home/ubuntu/bank-statement-converter-unified/backend${NC}"
echo -e "${YELLOW}nano .env${NC}"
echo ""
echo "Update these values in the file:"
cat /tmp/oauth-env-update.txt
echo ""
echo "After updating, restart the backend:"
echo -e "${YELLOW}sudo systemctl restart bank-converter-backend${NC}"
echo ""
echo "To verify it's working:"
echo -e "${YELLOW}sudo systemctl status bank-converter-backend${NC}"