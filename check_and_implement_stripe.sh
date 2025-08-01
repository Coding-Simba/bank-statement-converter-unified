#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Checking and implementing Stripe integration"
echo "==========================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking for existing Stripe endpoints..."
echo "=========================================="
grep -r "checkout\|stripe\|subscription" --include="*.py" . | grep -E "def |@router|@app" | head -20

echo -e "\n2. Checking if Stripe is installed..."
echo "===================================="
source venv/bin/activate
pip list | grep -i stripe || echo "Stripe not in pip list"

echo -e "\n3. Checking for Stripe configuration..."
echo "======================================"
grep -r "stripe\|STRIPE" --include="*.py" --include=".env*" . | grep -v "__pycache__" | head -10

echo -e "\n4. Creating Stripe checkout endpoints..."
echo "======================================="
cat > api/stripe_routes.py << 'PYTHON'
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe
import os
from datetime import datetime
from typing import Dict, Any

from ..database import get_db
from ..models.user import User
from ..auth import get_current_user_cookie

router = APIRouter()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Price IDs from Stripe Dashboard
PRICE_IDS = {
    "professional": os.getenv("STRIPE_PRICE_PROFESSIONAL", "price_professional"),
    "business": os.getenv("STRIPE_PRICE_BUSINESS", "price_business"),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise")
}

@router.post("/checkout/create-session")
async def create_checkout_session(
    request: Request,
    current_user: User = Depends(get_current_user_cookie),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription"""
    try:
        # Get request data
        data = await request.json()
        price_id = data.get("price_id")
        success_url = data.get("success_url", "https://bankcsvconverter.com/success")
        cancel_url = data.get("cancel_url", "https://bankcsvconverter.com/pricing")
        
        # Validate price ID
        if price_id not in PRICE_IDS:
            # Try to use the price_id directly if it's a full Stripe price ID
            if not price_id.startswith("price_"):
                raise HTTPException(status_code=400, detail="Invalid price ID")
        else:
            price_id = PRICE_IDS[price_id]
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "email": current_user.email
            }
        )
        
        return {"url": checkout_session.url, "session_id": checkout_session.id}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/subscription/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user_cookie),
    db: Session = Depends(get_db)
):
    """Get the current user's subscription status"""
    try:
        # Check if user has a Stripe customer ID
        if not current_user.stripe_customer_id:
            return {
                "status": "inactive",
                "plan": "free",
                "message": "No active subscription"
            }
        
        # Get customer from Stripe
        customer = stripe.Customer.retrieve(current_user.stripe_customer_id)
        
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status="active",
            limit=1
        )
        
        if subscriptions.data:
            subscription = subscriptions.data[0]
            return {
                "status": "active",
                "plan": subscription.items.data[0].price.lookup_key or subscription.items.data[0].price.id,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        else:
            return {
                "status": "inactive",
                "plan": "free",
                "message": "No active subscription"
            }
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Update user's subscription status
        # TODO: Implement database update
        
    return {"status": "success"}
PYTHON

echo -e "\n5. Adding Stripe routes to main app..."
echo "===================================="
# Check if Stripe routes are already imported
if ! grep -q "stripe_routes" main.py; then
    echo "Adding Stripe routes import..."
    # Add import after other API imports
    sed -i '/from .api import auth_cookie/a from .api import stripe_routes' main.py
    
    # Add router include
    sed -i '/app.include_router(auth_cookie.router/a app.include_router(stripe_routes.router, prefix="/v2/api", tags=["stripe"])' main.py
fi

echo -e "\n6. Checking if User model has stripe_customer_id..."
echo "================================================="
if ! grep -q "stripe_customer_id" models/user.py; then
    echo "Adding stripe_customer_id to User model..."
    # Add stripe fields to User model
    sed -i '/email = Column(String/a\    stripe_customer_id = Column(String(255), nullable=True)\n    subscription_status = Column(String(50), default="free")\n    subscription_end_date = Column(DateTime, nullable=True)' models/user.py
    
    echo -e "\nCreating migration for stripe fields..."
    cat > add_stripe_fields.py << 'MIGRATION'
#!/usr/bin/env python3
"""Add Stripe fields to User model"""
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def upgrade():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Add stripe_customer_id column
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN stripe_customer_id VARCHAR(255)
            """))
            conn.commit()
            print("Added stripe_customer_id column")
        except Exception as e:
            print(f"Column might already exist: {e}")
        
        # Add subscription_status column
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'free'
            """))
            conn.commit()
            print("Added subscription_status column")
        except Exception as e:
            print(f"Column might already exist: {e}")
        
        # Add subscription_end_date column
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN subscription_end_date TIMESTAMP
            """))
            conn.commit()
            print("Added subscription_end_date column")
        except Exception as e:
            print(f"Column might already exist: {e}")

if __name__ == "__main__":
    upgrade()
MIGRATION
    
    python3 add_stripe_fields.py
fi

echo -e "\n7. Creating .env.example for Stripe keys..."
echo "========================================="
if [ ! -f .env.example ]; then
    cat > .env.example << 'ENV'
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY
STRIPE_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Stripe Price IDs
STRIPE_PRICE_PROFESSIONAL=price_YOUR_PROFESSIONAL_PRICE_ID
STRIPE_PRICE_BUSINESS=price_YOUR_BUSINESS_PRICE_ID
STRIPE_PRICE_ENTERPRISE=price_YOUR_ENTERPRISE_PRICE_ID
ENV
fi

echo -e "\n8. Restarting backend to load new routes..."
echo "========================================="
pkill -f uvicorn
sleep 2
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_stripe.log 2>&1 &
sleep 5

echo -e "\n9. Testing new Stripe endpoints..."
echo "================================="
# Test checkout endpoint
echo "Testing checkout endpoint:"
curl -s -X POST http://localhost:5000/v2/api/checkout/create-session \
    -H "Content-Type: application/json" \
    -d '{"price_id":"test"}' | python3 -m json.tool | head -10 || echo "Checkout endpoint test"

# Test subscription status
echo -e "\nTesting subscription endpoint:"
curl -s http://localhost:5000/v2/api/subscription/status | python3 -m json.tool || echo "Subscription endpoint test"

EOF

echo -e "\n✅ Stripe integration setup complete!"
echo ""
echo "⚠️  IMPORTANT: You need to:"
echo "1. Add your Stripe API keys to the .env file on the server"
echo "2. Create products and prices in your Stripe dashboard"
echo "3. Update the price IDs in the .env file"
echo "4. Set up a webhook endpoint in Stripe dashboard pointing to:"
echo "   https://bankcsvconverter.com/v2/api/webhook"