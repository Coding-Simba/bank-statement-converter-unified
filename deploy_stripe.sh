#\!/bin/bash

# Server details
SERVER="ubuntu@3.235.19.83"
KEY_PATH="/Users/MAC/Desktop/bank-statement-converter.pem"

echo "Deploying Stripe integration to server..."

# Copy the new files to server
echo "1. Copying backend files..."
scp -i "$KEY_PATH" backend/api/stripe_payments.py "$SERVER:/home/ubuntu/backend/api/"
scp -i "$KEY_PATH" backend/models/database.py "$SERVER:/home/ubuntu/backend/models/"
scp -i "$KEY_PATH" backend/api/statements.py "$SERVER:/home/ubuntu/backend/api/"
scp -i "$KEY_PATH" backend/init_subscription_plans.py "$SERVER:/home/ubuntu/backend/"
scp -i "$KEY_PATH" backend/config/oauth.py "$SERVER:/home/ubuntu/backend/config/"

echo "2. Copying frontend files..."
scp -i "$KEY_PATH" js/stripe-integration.js "$SERVER:/var/www/html/js/"
scp -i "$KEY_PATH" js/dashboard.js "$SERVER:/var/www/html/js/"
scp -i "$KEY_PATH" pricing.html "$SERVER:/var/www/html/"
scp -i "$KEY_PATH" dashboard.html "$SERVER:/var/www/html/"

echo "3. Creating .env file on server..."
ssh -i "$KEY_PATH" "$SERVER" << 'ENDSSH'
cd /home/ubuntu/backend

# Backup existing .env if it exists
if [ -f .env ]; then
    cp .env .env.backup
fi

# Create new .env with Stripe configuration
cat > .env << 'ENVFILE'
# JWT Secret for authentication
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# Stripe Configuration (LIVE mode - BE CAREFUL\!)
# IMPORTANT: These are LIVE keys - they will charge real money\!
STRIPE_SECRET_KEY=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
STRIPE_PUBLISHABLE_KEY=pk_live_51RqLYuKwQLBjGTW9E8PxpLOB5gsgRfGdX3p9YfF45umG8iIVo398Xv4lMnkT7ZEGIr2cDJn7vz2eVF7eAiQl3twv00QS6FFBDm
# Stripe Webhook Secret
STRIPE_WEBHOOK_SECRET=whsec_UechMeK1RWlUvBKHjfeyL8sHnBSuAsYY

# Stripe Price IDs (LIVE)
# Starter Plan
STRIPE_STARTER_MONTHLY_PRICE_ID=price_1RqZubKwQLBjGTW9deSoEAWV
STRIPE_STARTER_YEARLY_PRICE_ID=price_1RqZtaKwQLBjGTW9w20V3Hst

# Professional Plan  
STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID=price_1RqZvXKwQLBjGTW9jqS3dhr8
STRIPE_PROFESSIONAL_YEARLY_PRICE_ID=price_1RqZv9KwQLBjGTW9tE0aY9R9

# Business Plan
STRIPE_BUSINESS_MONTHLY_PRICE_ID=price_1RqZwFKwQLBjGTW9JIuiSSm5
STRIPE_BUSINESS_YEARLY_PRICE_ID=price_1RqZvrKwQLBjGTW9s0sfMhFN

# Frontend URL
FRONTEND_URL=https://bankcsvconverter.com

# OAuth Configuration (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
ENVFILE

echo "4. Installing Stripe package..."
source venv/bin/activate
pip install stripe
pip install python-dotenv

echo "5. Running database migrations..."
python init_subscription_plans.py

echo "6. Restarting backend service..."
sudo systemctl restart bank-backend

echo "7. Checking service status..."
sudo systemctl status bank-backend
ENDSSH

echo "Deployment complete\!"
