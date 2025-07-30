"""Stripe payment integration API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import stripe
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from models.database import get_db, User, Subscription, Plan, UsageLog, Payment
from middleware.auth_middleware import get_current_user
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Plan configuration
PLANS = {
    "free": {
        "name": "Free",
        "price_id": None,
        "monthly_pages": 150,  # 5 per day * 30 days
        "price": 0,
    },
    "starter": {
        "name": "Starter",
        "price_id": os.getenv("STRIPE_STARTER_MONTHLY_PRICE_ID", ""),
        "price_yearly_id": os.getenv("STRIPE_STARTER_YEARLY_PRICE_ID", ""),
        "monthly_pages": 400,
        "price": 30,
        "yearly_price": 24,
    },
    "professional": {
        "name": "Professional",
        "price_id": os.getenv("STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID", ""),
        "price_yearly_id": os.getenv("STRIPE_PROFESSIONAL_YEARLY_PRICE_ID", ""),
        "monthly_pages": 1000,
        "price": 60,
        "yearly_price": 48,
    },
    "business": {
        "name": "Business",
        "price_id": os.getenv("STRIPE_BUSINESS_MONTHLY_PRICE_ID", ""),
        "price_yearly_id": os.getenv("STRIPE_BUSINESS_YEARLY_PRICE_ID", ""),
        "monthly_pages": 4000,
        "price": 99,
        "yearly_price": 79,
    }
}

router = APIRouter(prefix="/api/stripe", tags=["payments"])

class CreateCheckoutSessionRequest(BaseModel):
    plan: str
    billing_period: str = "monthly"  # monthly or yearly

class CreateCustomerPortalRequest(BaseModel):
    return_url: str = "/"

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription."""
    try:
        if request.plan not in PLANS or request.plan == "free":
            raise HTTPException(status_code=400, detail="Invalid plan selected")
        
        plan_info = PLANS[request.plan]
        
        # Select the appropriate price ID based on billing period
        if request.billing_period == "yearly":
            price_id = plan_info.get("price_yearly_id")
        else:
            price_id = plan_info.get("price_id")
            
        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID not configured for this plan")
        
        # Create or get customer
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
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:8000") + "/dashboard.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:8000") + "/pricing.html",
            metadata={
                "user_id": str(current_user.id),
                "plan": request.plan
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_successful_payment(session, db)
    
    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        await handle_subscription_created(subscription, db)
    
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await handle_subscription_updated(subscription, db)
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(subscription, db)
    
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        await handle_invoice_payment_succeeded(invoice, db)
    
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        await handle_invoice_payment_failed(invoice, db)
    
    return {"status": "success"}

@router.post("/customer-portal")
async def create_customer_portal_session(
    request: CreateCustomerPortalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session for managing subscriptions."""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No subscription found")
        
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=os.getenv("FRONTEND_URL", "http://localhost:8000") + request.return_url,
        )
        
        return {"portal_url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

@router.get("/subscription-status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current subscription status and usage."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        # Free plan
        usage = await get_current_month_usage(current_user.id, db)
        return {
            "plan": "free",
            "status": "active",
            "pages_used": usage,
            "pages_limit": PLANS["free"]["monthly_pages"],
            "renewal_date": None
        }
    
    # Get current month usage
    usage = await get_current_month_usage(current_user.id, db)
    
    plan_info = PLANS.get(subscription.plan_id, PLANS["free"])
    
    return {
        "plan": subscription.plan_id,
        "status": subscription.status,
        "pages_used": usage,
        "pages_limit": plan_info["monthly_pages"],
        "renewal_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end
    }

async def handle_successful_payment(session: Dict[str, Any], db: Session):
    """Handle successful checkout session."""
    user_id = int(session["metadata"]["user_id"])
    plan = session["metadata"]["plan"]
    
    # Update user's account type
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.account_type = plan
        db.commit()
    
    logger.info(f"Payment successful for user {user_id}, plan: {plan}")

async def handle_subscription_created(subscription: Dict[str, Any], db: Session):
    """Handle new subscription creation."""
    customer_id = subscription["customer"]
    
    # Find user by customer ID
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer ID: {customer_id}")
        return
    
    # Get plan from price ID
    plan_id = None
    price_id = subscription["items"]["data"][0]["price"]["id"]
    for plan_key, plan_info in PLANS.items():
        if plan_info.get("price_id") == price_id or plan_info.get("price_yearly_id") == price_id:
            plan_id = plan_key
            break
    
    if not plan_id:
        logger.error(f"Plan not found for price ID: {price_id}")
        return
    
    # Create or update subscription record
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription["id"]
    ).first()
    
    if not sub:
        sub = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription["id"],
            stripe_customer_id=customer_id,
            plan_id=plan_id,
            status=subscription["status"],
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
            cancel_at_period_end=subscription["cancel_at_period_end"]
        )
        db.add(sub)
    else:
        sub.status = subscription["status"]
        sub.plan_id = plan_id
        sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
        sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
        sub.cancel_at_period_end = subscription["cancel_at_period_end"]
    
    # Update user account type
    user.account_type = plan_id
    
    db.commit()
    logger.info(f"Subscription created/updated for user {user.id}, plan: {plan_id}")

async def handle_subscription_updated(subscription: Dict[str, Any], db: Session):
    """Handle subscription updates."""
    await handle_subscription_created(subscription, db)  # Same logic

async def handle_subscription_deleted(subscription: Dict[str, Any], db: Session):
    """Handle subscription cancellation."""
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription["id"]
    ).first()
    
    if sub:
        sub.status = "canceled"
        
        # Update user to free plan
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user:
            user.account_type = "free"
        
        db.commit()
        logger.info(f"Subscription canceled for user {sub.user_id}")

async def handle_invoice_payment_succeeded(invoice: Dict[str, Any], db: Session):
    """Handle successful invoice payment."""
    # Reset monthly usage on successful payment
    customer_id = invoice["customer"]
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    
    if user:
        logger.info(f"Invoice paid for user {user.id}")

async def handle_invoice_payment_failed(invoice: Dict[str, Any], db: Session):
    """Handle failed invoice payment."""
    customer_id = invoice["customer"]
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    
    if user:
        logger.warning(f"Invoice payment failed for user {user.id}")

async def get_current_month_usage(user_id: int, db: Session) -> int:
    """Get current month's page usage for a user."""
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    usage = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.created_at >= start_of_month
    ).count()
    
    return usage

@router.post("/log-usage")
async def log_usage(
    pages: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log page usage for the current user."""
    # Check if user has exceeded their limit
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    plan_id = subscription.plan_id if subscription else "free"
    plan_info = PLANS.get(plan_id, PLANS["free"])
    
    current_usage = await get_current_month_usage(current_user.id, db)
    
    if current_usage + pages > plan_info["monthly_pages"]:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly page limit exceeded. Current usage: {current_usage}/{plan_info['monthly_pages']}"
        )
    
    # Log the usage
    for _ in range(pages):
        usage_log = UsageLog(
            user_id=current_user.id,
            pages=1,
            created_at=datetime.utcnow()
        )
        db.add(usage_log)
    
    db.commit()
    
    return {
        "pages_used": current_usage + pages,
        "pages_limit": plan_info["monthly_pages"],
        "remaining": plan_info["monthly_pages"] - (current_usage + pages)
    }