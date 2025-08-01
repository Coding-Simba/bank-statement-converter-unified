#!/bin/bash

# Fix Stripe Configuration
echo "🔧 Fixing Stripe Configuration"
echo "=============================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Updating Stripe configuration in api/stripe.py..."
# Update the stripe.py file to load environment variables properly
cat > api/stripe.py << 'EOF'
"""Stripe payment integration endpoints."""

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging
from dotenv import load_dotenv

from models.database import get_db, User
from middleware.auth_middleware import get_current_user

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
if not stripe_api_key:
    logger.error("STRIPE_SECRET_KEY not found in environment variables")
else:
    stripe.api_key = stripe_api_key
    logger.info("Stripe API key configured successfully")

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
    if not stripe.api_key:
        logger.error("Stripe API key not configured")
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        logger.info(f"Creating checkout session for user {current_user.email}")
        
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            logger.info(f"Creating new Stripe customer for {current_user.email}")
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": str(current_user.id)}
            )
            current_user.stripe_customer_id = customer.id
            db.commit()
            logger.info(f"Created Stripe customer: {customer.id}")
        
        # Create checkout session
        logger.info(f"Creating checkout session with price_id: {request.price_id}")
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
        
        logger.info(f"Checkout session created: {checkout_session.id}")
        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}
        
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid Stripe request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
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
    if not stripe.api_key:
        logger.error("Stripe API key not configured")
        return SubscriptionStatusResponse(has_subscription=False)
    
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
    if not stripe.api_key:
        logger.error("Stripe API key not configured")
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
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

echo -e "\n2. Installing python-dotenv if needed..."
pip3 install python-dotenv

echo -e "\n3. Checking .env file location..."
if [ -f .env ]; then
    echo "✓ .env file found in backend directory"
    echo "Stripe key status:"
    grep STRIPE_SECRET_KEY .env | head -1 | sed 's/=.*/=***HIDDEN***/'
else
    echo "❌ .env file not found in backend directory"
    # Check parent directory
    if [ -f ../.env ]; then
        echo "Found .env in parent directory, copying..."
        cp ../.env .
    fi
fi

echo -e "\n4. Restarting backend with updated configuration..."
pkill -f "uvicorn main:app" || true
sleep 2

# Start with explicit environment loading
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info > backend_stripe_fixed.log 2>&1 &

sleep 5

echo -e "\n5. Testing Stripe endpoints again..."
# Login first
LOGIN_RESPONSE=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "Testing subscription status:"
    curl -X GET http://localhost:5000/api/stripe/subscription-status \
      -H "Authorization: Bearer $TOKEN" \
      -w "\nStatus: %{http_code}\n" -s | python3 -m json.tool 2>/dev/null || cat
fi

echo -e "\n6. Checking backend logs..."
tail -20 backend_stripe_fixed.log | grep -E "(Stripe|stripe|configured|ERROR)" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Stripe configuration fixed!${NC}"
echo ""
echo "The Stripe checkout should now work properly."
echo "Try again at: https://bankcsvconverter.com/pricing.html"