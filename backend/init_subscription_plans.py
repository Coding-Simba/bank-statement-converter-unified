"""Initialize subscription plans in the database."""

from models.database import init_db, get_db, Plan
import json

def init_plans():
    """Initialize the subscription plans in the database."""
    db = next(get_db())
    
    plans = [
        {
            "name": "free",
            "display_name": "Free",
            "monthly_pages": 150,  # 5 per day * 30 days
            "monthly_price": 0,
            "yearly_price": 0,
            "features": json.dumps([
                "5 conversions per day",
                "Support for 50+ banks",
                "CSV & Excel export",
                "Email support"
            ])
        },
        {
            "name": "starter",
            "display_name": "Starter",
            "monthly_pages": 400,
            "monthly_price": 30,
            "yearly_price": 24,
            "features": json.dumps([
                "400 pages per month",
                "Support for 50+ banks",
                "CSV & Excel export",
                "Secure processing",
                "Email support",
                "Basic transaction categorization"
            ])
        },
        {
            "name": "professional",
            "display_name": "Professional",
            "monthly_pages": 1000,
            "monthly_price": 60,
            "yearly_price": 48,
            "features": json.dumps([
                "1000 pages per month",
                "Support for 1000+ banks",
                "CSV & Excel export",
                "Batch processing",
                "Priority support",
                "Custom date formats",
                "Advanced transaction categorization"
            ])
        },
        {
            "name": "business",
            "display_name": "Business",
            "monthly_pages": 4000,
            "monthly_price": 99,
            "yearly_price": 79,
            "features": json.dumps([
                "4000 pages per month",
                "Support for 1000+ banks",
                "CSV, Excel & JSON export",
                "Bulk batch processing",
                "Dedicated support",
                "Custom integrations",
                "White-label option",
                "Advanced analytics & reporting"
            ])
        }
    ]
    
    for plan_data in plans:
        # Check if plan already exists
        existing_plan = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
        if not existing_plan:
            plan = Plan(**plan_data)
            db.add(plan)
            print(f"Created plan: {plan_data['display_name']}")
        else:
            # Update existing plan
            for key, value in plan_data.items():
                setattr(existing_plan, key, value)
            print(f"Updated plan: {plan_data['display_name']}")
    
    db.commit()
    db.close()
    print("All plans initialized successfully!")

if __name__ == "__main__":
    init_db()  # Ensure all tables exist
    init_plans()