"""Simplified Stripe payment integration that works with existing auth."""
import os
import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from models.database import get_db, User

# Configure logging
logger = logging.getLogger(__name__)

# Stripe configuration
# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY not set - using test mode")
    # This will be set on the server via environment variable

# Plan configuration
PLANS = {
    "starter": {
        "name": "Starter",
        "monthly_price_id": "price_1Q5UtXRu96XFzW0MPNWJnkJH",
        "yearly_price_id": "price_1Q5UtXRu96XFzW0MjzJgx8HV",
        "monthly_price": 9,
        "yearly_price": 90,
        "conversions_per_day": 10
    },
    "professional": {
        "name": "Professional", 
        "monthly_price_id": "price_1Q5UtYRu96XFzW0MINa49vTr",
        "yearly_price_id": "price_1Q5UtYRu96XFzW0MrhXHOc6Y",
        "monthly_price": 29,
        "yearly_price": 290,
        "conversions_per_day": 100
    },
    "business": {
        "name": "Business",
        "monthly_price_id": "price_1Q5UtYRu96XFzW0MDGhQD3BL",
        "yearly_price_id": "price_1Q5UtYRu96XFzW0M6Fuw1t1X",
        "monthly_price": 99,
        "yearly_price": 990,
        "conversions_per_day": -1  # Unlimited
    }
}

router = APIRouter(prefix="/api/stripe", tags=["payments"])

class CreateCheckoutSessionRequest(BaseModel):
    plan: str
    billing_period: str = "monthly"

@router.post("/create-checkout-session")
async def create_checkout_session(
    checkout_request: CreateCheckoutSessionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription."""
    try:
        # For now, just get user ID from auth header or use a test user
        # This avoids the complex auth middleware issues
        user = None
        
        # Try to get Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Try to decode the token manually
            try:
                from jose import jwt
                token = auth_header.split(" ")[1]
                # Use the correct secret key
                from config.jwt_config import JWT_SECRET_KEY, JWT_ALGORITHM
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    user = db.query(User).filter(User.id == int(user_id)).first()
            except Exception as e:
                logger.error(f"Token decode error: {e}")
        
        # If no user found, return error
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Validate plan
        if checkout_request.plan not in PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan selected")
        
        plan_info = PLANS[checkout_request.plan]
        
        # Select price based on billing period
        if checkout_request.billing_period == "yearly":
            price_id = plan_info["yearly_price_id"]
        else:
            price_id = plan_info["monthly_price_id"]
        
        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.id)}
            )
            user.stripe_customer_id = customer.id
            db.commit()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url="https://bankcsvconverter.com/dashboard.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://bankcsvconverter.com/pricing.html",
            metadata={
                "user_id": str(user.id),
                "plan": checkout_request.plan,
                "billing_period": checkout_request.billing_period
            }
        )
        
        return {"url": session.url}
        
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

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
        
    except Exception as e:
        logger.error(f"Error in payment_success: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer-portal")
async def create_customer_portal_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session."""
    try:
        # Similar simplified auth
        user = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from jose import jwt
                from config.jwt_config import JWT_SECRET_KEY, JWT_ALGORITHM
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    user = db.query(User).filter(User.id == int(user_id)).first()
            except Exception as e:
                logger.error(f"Auth error: {e}")
        
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        if not user.stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail="No subscription found. Please subscribe first."
            )
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url="https://bankcsvconverter.com/settings.html",
        )
        
        return {"url": session.url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portal error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))