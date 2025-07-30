#!/bin/bash

# Deploy Validation Feature to Production

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Validation Feature"
echo "============================"

# 1. Copy validation API
echo "1. Copying validation API..."
scp -i "$KEY_PATH" backend/api/validation.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"

# 2. Copy frontend files
echo -e "\n2. Copying frontend files..."
scp -i "$KEY_PATH" frontend/validation.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"
scp -i "$KEY_PATH" frontend/js/validation-integration.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# 3. Run database migration
echo -e "\n3. Running database migration..."
scp -i "$KEY_PATH" backend/migrations/add_validation_fields.py "$SERVER_USER@$SERVER_IP:/tmp/"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "Running migration..."
python3 /tmp/add_validation_fields.py

echo -e "\n4. Updating Statement model..."
# Add validation fields to Statement model
cat >> models.py << 'MODEL'

# Validation fields (added for transaction validation feature)
Statement.validated = Column(Boolean, default=False)
Statement.validation_date = Column(DateTime, nullable=True)
Statement.validated_data = Column(Text, nullable=True)
MODEL

echo -e "\n5. Updating main.py to include validation routes..."
# Add validation router to main.py
sed -i '/from .api import statements/a from .api import validation' main.py
sed -i '/app.include_router(statements.router/a app.include_router(validation.router, prefix="/api", tags=["validation"])' main.py

echo -e "\n6. Adding validation link to main page..."
# Update the main page to include validation integration script
if ! grep -q "validation-integration.js" /home/ubuntu/bank-statement-converter/frontend/index.html; then
    sed -i '/<\/body>/i <script src="/js/validation-integration.js"></script>' /home/ubuntu/bank-statement-converter/frontend/index.html
fi

echo -e "\n7. Setting up Nginx route for validation page..."
# Add Nginx route for validation.html
sudo tee /etc/nginx/sites-available/bank-converter-validation > /dev/null << 'NGINX'
# Add this location block to the existing server configuration
location /validation.html {
    alias /home/ubuntu/bank-statement-converter/frontend/validation.html;
    try_files $uri =404;
}
NGINX

# Update main Nginx config to include validation routes
sudo sed -i '/location \/ {/i \    location /validation.html {\n        alias /home/ubuntu/bank-statement-converter/frontend/validation.html;\n        try_files $uri =404;\n    }\n' /etc/nginx/sites-available/bank-converter

echo -e "\n8. Restarting services..."
sudo systemctl restart bankconverter
sudo systemctl reload nginx

echo -e "\n✅ Validation feature deployed!"

EOF

echo -e "\n9. Testing deployment..."
# Test if validation page is accessible
VALIDATION_TEST=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/validation.html)

if [ "$VALIDATION_TEST" == "200" ]; then
    echo "✅ Validation page is accessible!"
else
    echo "❌ Validation page returned HTTP $VALIDATION_TEST"
fi

echo -e "\nDeployment complete!"
echo "===================="
echo "Validation feature is now available at:"
echo "https://bankcsvconverter.com/validation.html"
echo ""
echo "Users will see a 'Validate Transactions' button after uploading PDFs"