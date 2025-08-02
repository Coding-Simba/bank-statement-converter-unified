#!/bin/bash

# Deploy settings page updates to production
# This script deploys all settings-related files to the production server

set -e

echo "🚀 Deploying settings page updates to production..."

# Server details
SERVER="ubuntu@3.235.19.83"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Copy frontend files
echo "📦 Copying frontend files..."
scp -i "$SSH_KEY" js/settings-integrated.js "$SERVER:/home/ubuntu/bank-statement-converter/frontend/js/"

# Copy backend files
echo "📦 Copying backend files..."
scp -i "$SSH_KEY" backend/api/user_settings_simple.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/api/"
scp -i "$SSH_KEY" backend/api/login_sessions.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/api/"
scp -i "$SSH_KEY" backend/models/login_session.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/models/"
scp -i "$SSH_KEY" backend/utils/two_factor_simple.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/utils/"

# Copy migration files
echo "📦 Copying migration files..."
scp -i "$SSH_KEY" backend/migrations/add_user_preferences.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/migrations/"
scp -i "$SSH_KEY" backend/migrations/create_login_sessions_table.py "$SERVER:/home/ubuntu/bank-statement-converter/backend/migrations/"

# Run migrations and restart service on server
echo "🔧 Running migrations and restarting service..."
ssh -i "$SSH_KEY" "$SERVER" << 'EOF'
    cd /home/ubuntu/bank-statement-converter/backend
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
    fi
    
    # Run migrations
    echo "Running database migrations..."
    python migrations/add_user_preferences.py
    python migrations/create_login_sessions_table.py
    
    # Restart backend service
    echo "Restarting backend service..."
    sudo systemctl restart bankcsv-backend
    
    # Wait and check status
    sleep 5
    if sudo systemctl is-active --quiet bankcsv-backend; then
        echo "✅ Backend service restarted successfully"
    else
        echo "❌ Backend service failed to start"
        sudo systemctl status bankcsv-backend
        exit 1
    fi
    
    # Test health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")
    if [ "$response" = "200" ]; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed with status: $response"
    fi
EOF

echo "✅ Deployment complete!"
echo "🌐 Settings page should now be fully functional at https://bankcsvconverter.com/settings.html"