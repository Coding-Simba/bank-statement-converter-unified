"""Stripe payment integration with robust error handling."""
import os
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from models.database import get_db, User
from middleware.auth_middleware import decode_token
from config.jwt_config import JWT_SECRET_KEY as SECRET_KEY, JWT_ALGORITHM as ALGORITHM
from jose import jwt, JWTError

# Configure logging
logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable not set")

# Plan configuration
PLANS = {
    "starter": {
        "name": "Starter",
        "monthly_price_id": os.getenv("STRIPE_STARTER_MONTHLY_PRICE_ID", "price_1Q5UtXRu96XFzW0MPNWJnkJH"),
        "yearly_price_id": os.getenv("STRIPE_STARTER_YEARLY_PRICE_ID", "price_1Q5UtXRu96XFzW0MjzJgx8HV"),
        "monthly_price": 9,
        "yearly_price": 90,
        "conversions_per_day": 10
    },
    "professional": {
        "name": "Professional", 
        "monthly_price_id": os.getenv("STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID", "price_1Q5UtYRu96XFzW0MINa49vTr"),
        "yearly_price_id": os.getenv("STRIPE_PROFESSIONAL_YEARLY_PRICE_ID", "price_1Q5UtYRu96XFzW0MrhXHOc6Y"),
        "monthly_price": 29,
        "yearly_price": 290,
        "conversions_per_day": 100
    },
    "business": {
        "name": "Business",
        "monthly_price_id": os.getenv("STRIPE_BUSINESS_MONTHLY_PRICE_ID", "price_1Q5UtYRu96XFzW0MDGhQD3BL"),
        "yearly_price_id": os.getenv("STRIPE_BUSINESS_YEARLY_PRICE_ID", "price_1Q5UtYRu96XFzW0M6Fuw1t1X"),
        "monthly_price": 99,
        "yearly_price": 990,
        "conversions_per_day": -1  # Unlimited
    }
}

router = APIRouter(prefix="/api/stripe", tags=["payments"])

class CreateCheckoutSessionRequest(BaseModel):
    plan: str
    billing_period: str = "monthly"

async def get_current_user_safe(request: Request, db: Session) -> User:
    """Safely get current user from auth token."""
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/create-checkout-session")
async def create_checkout_session(
    checkout_request: CreateCheckoutSessionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription."""
    try:
        # Get current user
        current_user = await get_current_user_safe(request, db)
        
        # Validate plan
        if checkout_request.plan not in PLANS or checkout_request.plan == "free":
            raise HTTPException(status_code=400, detail="Invalid plan selected")
        
        plan_info = PLANS[checkout_request.plan]
        
        # Select price based on billing period
        if checkout_request.billing_period == "yearly":
            price_id = plan_info["yearly_price_id"]
        else:
            price_id = plan_info["monthly_price_id"]
        
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            try:
                customer = stripe.Customer.create(
                    email=current_user.email,
                    metadata={"user_id": str(current_user.id)}
                )
                current_user.stripe_customer_id = customer.id
                db.commit()
            except stripe.error.StripeError as e:
                logger.error(f"Stripe customer creation error: {e}")
                raise HTTPException(status_code=500, detail="Failed to create customer")
        
        # Create checkout session
        try:
            session = stripe.checkout.Session.create(
                customer=current_user.stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url="https://bankcsvconverter.com/dashboard.html?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://bankcsvconverter.com/pricing.html",
                metadata={
                    "user_id": str(current_user.id),
                    "plan": checkout_request.plan,
                    "billing_period": checkout_request.billing_period
                }
            )
            
            return {"url": session.url}
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe session creation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.get("/success")
async def payment_success(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle successful payment."""
    try:
        # Verify the session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        # Get user from metadata
        user_id = int(session.metadata.get("user_id"))
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user subscription
        user.account_type = session.metadata.get("plan")
        user.stripe_subscription_id = session.subscription
        user.subscription_status = "active"
        user.subscription_updated_at = datetime.now(timezone.utc)
        
        # Update conversion limits based on plan
        plan_info = PLANS.get(user.account_type, PLANS["starter"])
        user.daily_conversion_limit = plan_info["conversions_per_day"]
        
        db.commit()
        
        return {
            "success": True,
            "plan": user.account_type,
            "message": "Subscription activated successfully!"
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in payment_success: {e}")
        raise HTTPException(status_code=400, detail="Invalid session")
    except Exception as e:
        logger.error(f"Error in payment_success: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate subscription")

@router.post("/customer-portal")
async def create_customer_portal_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session."""
    try:
        # Get current user
        current_user = await get_current_user_safe(request, db)
        
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail="No subscription found. Please subscribe first."
            )
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="https://bankcsvconverter.com/settings.html",
        )
        
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in customer_portal: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        user = db.query(User).filter(
            User.stripe_subscription_id == subscription["id"]
        ).first()
        
        if user:
            user.subscription_status = subscription["status"]
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user = db.query(User).filter(
            User.stripe_subscription_id == subscription["id"]
        ).first()
        
        if user:
            user.account_type = "free"
            user.subscription_status = "cancelled"
            user.daily_conversion_limit = 5
            db.commit()
    
    return {"status": "success"}