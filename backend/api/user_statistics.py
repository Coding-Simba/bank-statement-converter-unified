"""User statistics API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from typing import Optional, Dict
from pydantic import BaseModel
from cachetools import TTLCache
import asyncio

from models.database import get_db, User, Statement, GenerationTracking
from dependencies import get_current_user

router = APIRouter()

# Plan limits configuration
PLAN_LIMITS = {
    "free": {"daily": 5, "monthly": 150},
    "starter": {"daily": 20, "monthly": 600},
    "professional": {"daily": 50, "monthly": 1500},
    "business": {"daily": -1, "monthly": -1}  # Unlimited
}

# Subscription cache - 5 minute TTL
subscription_cache: TTLCache = TTLCache(maxsize=1000, ttl=300)

class PlanLimits(BaseModel):
    daily: int
    monthly: int
    usedThisMonth: int

class StatisticsResponse(BaseModel):
    todayConversions: int
    totalConversions: int
    remainingToday: int
    planLimits: PlanLimits
    accountType: str

async def get_cached_subscription_info(user_id: int, db: Session) -> Dict:
    """Get subscription info with caching."""
    cache_key = f"subscription_{user_id}"
    
    # Check cache first
    if cache_key in subscription_cache:
        return subscription_cache[cache_key]
    
    # Get fresh data from database
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        subscription_info = {
            "plan": user.subscription_plan or "free",
            "status": user.subscription_status or "free",
            "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            "stripe_customer_id": user.stripe_customer_id
        }
        
        # Cache the result
        subscription_cache[cache_key] = subscription_info
        return subscription_info
    
    return {"plan": "free", "status": "free", "expires_at": None, "stripe_customer_id": None}


@router.get("/user/statistics", response_model=StatisticsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard display."""
    
    # Get user's plan from cache
    subscription_info = await get_cached_subscription_info(current_user.id, db)
    account_type = subscription_info["plan"]
    
    # Get today's conversion count
    today_tracking = db.query(GenerationTracking).filter(
        GenerationTracking.user_id == current_user.id,
        GenerationTracking.date == date.today()
    ).first()
    
    today_conversions = today_tracking.count if today_tracking else 0
    
    # Get total conversions count
    total_conversions = db.query(func.count(Statement.id)).filter(
        Statement.user_id == current_user.id,
        Statement.is_deleted == False
    ).scalar() or 0
    
    # Get this month's conversions
    start_of_month = date.today().replace(day=1)
    month_conversions = db.query(func.count(Statement.id)).filter(
        Statement.user_id == current_user.id,
        Statement.created_at >= start_of_month,
        Statement.is_deleted == False
    ).scalar() or 0
    
    # Get plan limits
    limits = PLAN_LIMITS.get(account_type, PLAN_LIMITS["free"])
    daily_limit = limits["daily"]
    monthly_limit = limits["monthly"]
    
    # Calculate remaining for today
    if daily_limit == -1:  # Unlimited
        remaining_today = 999999
    else:
        remaining_today = max(0, daily_limit - today_conversions)
    
    return StatisticsResponse(
        todayConversions=today_conversions,
        totalConversions=total_conversions,
        remainingToday=remaining_today,
        planLimits=PlanLimits(
            daily=daily_limit,
            monthly=monthly_limit,
            usedThisMonth=month_conversions
        ),
        accountType=account_type
    )

@router.get("/user/usage-summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed usage summary for the current user."""
    
    # Last 7 days usage
    seven_days_ago = date.today() - timedelta(days=7)
    daily_usage = db.query(
        GenerationTracking.date,
        GenerationTracking.count
    ).filter(
        GenerationTracking.user_id == current_user.id,
        GenerationTracking.date >= seven_days_ago
    ).order_by(GenerationTracking.date.desc()).all()
    
    # Format daily usage
    usage_by_day = [
        {
            "date": day.date.isoformat(),
            "count": day.count
        }
        for day in daily_usage
    ]
    
    # Get monthly usage for the last 6 months
    six_months_ago = date.today() - timedelta(days=180)
    monthly_usage = db.query(
        func.strftime("%Y-%m", Statement.created_at).label("month"),
        func.count(Statement.id).label("count")
    ).filter(
        Statement.user_id == current_user.id,
        Statement.created_at >= six_months_ago,
        Statement.is_deleted == False
    ).group_by("month").order_by("month").all()
    
    return {
        "dailyUsage": usage_by_day,
        "monthlyUsage": [
            {"month": month, "count": count}
            for month, count in monthly_usage
        ]
    }


@router.post("/user/clear-subscription-cache")
async def clear_subscription_cache(
    current_user: User = Depends(get_current_user)
):
    """Clear subscription cache for the current user."""
    cache_key = f"subscription_{current_user.id}"
    
    if cache_key in subscription_cache:
        del subscription_cache[cache_key]
        return {"message": "Subscription cache cleared"}
    
    return {"message": "No cache to clear"}