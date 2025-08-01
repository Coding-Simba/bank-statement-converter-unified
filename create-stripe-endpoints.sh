#!/bin/bash

# Create Stripe Endpoints
echo "💳 Creating Stripe Endpoints"
echo "==========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Create Stripe endpoints via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Creating Stripe API endpoints..."
cat > api/stripe.py << 'EOF'
"""Stripe payment integration endpoints."""

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from models.database import get_db, User
from middleware.auth_middleware import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str = "https://bankcsvconverter.com/dashboard.html?session_id={CHECKOUT_SESSION_ID}"
    cancel_url: str = "https://bankcsvconverter.com/pricing.html"

class SubscriptionStatusResponse(BaseModel):
    has_subscription: bool
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    current_period_end: Optional[int] = None

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription."""
    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": str(current_user.id)}
            )
            current_user.stripe_customer_id = customer.id
            db.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                'user_id': str(current_user.id)
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription status."""
    try:
        if not current_user.stripe_customer_id:
            return SubscriptionStatusResponse(has_subscription=False)
        
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status='active',
            limit=1
        )
        
        if not subscriptions.data:
            return SubscriptionStatusResponse(has_subscription=False)
        
        subscription = subscriptions.data[0]
        
        # Determine plan name from price ID
        price_id = subscription.items.data[0].price.id
        plan_name = "unknown"
        
        # Map price IDs to plan names
        price_to_plan = {
            os.getenv('STRIPE_STARTER_MONTHLY_PRICE_ID'): 'starter',
            os.getenv('STRIPE_STARTER_YEARLY_PRICE_ID'): 'starter',
            os.getenv('STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID'): 'professional',
            os.getenv('STRIPE_PROFESSIONAL_YEARLY_PRICE_ID'): 'professional',
            os.getenv('STRIPE_BUSINESS_MONTHLY_PRICE_ID'): 'business',
            os.getenv('STRIPE_BUSINESS_YEARLY_PRICE_ID'): 'business',
        }
        
        plan_name = price_to_plan.get(price_id, 'unknown')
        
        return SubscriptionStatusResponse(
            has_subscription=True,
            subscription_status=subscription.status,
            subscription_plan=plan_name,
            current_period_end=subscription.current_period_end
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return SubscriptionStatusResponse(has_subscription=False)
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return SubscriptionStatusResponse(has_subscription=False)

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel the current user's subscription."""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        # Get active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status='active',
            limit=1
        )
        
        if not subscriptions.data:
            raise HTTPException(status_code=400, detail="No active subscription found")
        
        # Cancel the subscription at period end
        subscription = stripe.Subscription.modify(
            subscriptions.data[0].id,
            cancel_at_period_end=True
        )
        
        return {
            "message": "Subscription will be cancelled at the end of the billing period",
            "cancel_at": subscription.cancel_at
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                # Update user's subscription status
                user.subscription_status = 'active'
                user.stripe_customer_id = session['customer']
                db.commit()
                
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = 'cancelled'
            db.commit()
    
    return {"status": "success"}
EOF

echo -e "\n2. Updating main.py to include Stripe router..."
# Check if stripe router is already included
if ! grep -q "from api import stripe" main.py; then
    # Add import
    sed -i '/from api import.*analyze_transactions/a from api import stripe' main.py
    
    # Add router
    sed -i '/app.include_router(analyze_transactions.router)/a app.include_router(stripe.router)' main.py
    
    echo "✓ Added Stripe router to main.py"
else
    echo "✓ Stripe router already in main.py"
fi

echo -e "\n3. Installing stripe package if not already installed..."
pip3 install stripe

echo -e "\n4. Restarting backend..."
pkill -f "uvicorn main:app" || true
sleep 2
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_stripe.log 2>&1 &

sleep 5

echo -e "\n5. Testing new Stripe endpoints..."
# Test subscription status endpoint
echo "Testing subscription status endpoint:"
curl -X GET http://localhost:5000/api/stripe/subscription-status \
  -H "Authorization: Bearer test-token" \
  -w "\nStatus: %{http_code}\n" -s | head -5

echo -e "\n6. Checking if endpoints are now available..."
curl -s http://localhost:5000/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Stripe endpoints:')
for path in data.get('paths', {}):
    if 'stripe' in path:
        methods = list(data['paths'][path].keys())
        print(f'  {methods} {path}')
" 2>/dev/null || echo "Could not parse OpenAPI spec"

ENDSSH

echo ""
echo -e "${GREEN}✓ Stripe endpoints created!${NC}"
echo ""
echo "The Stripe checkout should now work on the pricing page."
echo "Make sure you're logged in before trying to purchase a subscription."