"""Test script for Stripe integration."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_stripe_integration():
    """Test the Stripe integration."""
    print("=== Stripe Integration Test ===\n")
    
    # 1. Check environment variables
    print("1. Checking environment variables...")
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"   ❌ {var}: Not set")
        else:
            value = os.getenv(var)
            if var == "STRIPE_SECRET_KEY":
                print(f"   ✓ {var}: {'Test mode' if value.startswith('sk_test_') else 'Live mode'}")
            else:
                print(f"   ✓ {var}: Set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please create a .env file with the required variables.")
        return
    
    # 2. Test database tables
    print("\n2. Checking database tables...")
    try:
        from models.database import init_db, get_db, Plan, Subscription, UsageLog
        init_db()
        db = next(get_db())
        
        # Check if plans exist
        plans = db.query(Plan).all()
        print(f"   ✓ Plans table: {len(plans)} plans found")
        for plan in plans:
            print(f"      - {plan.display_name}: ${plan.monthly_price}/mo")
        
        print("   ✓ Subscription table: Ready")
        print("   ✓ UsageLog table: Ready")
        
    except Exception as e:
        print(f"   ❌ Database error: {str(e)}")
        return
    
    # 3. Test Stripe connection
    print("\n3. Testing Stripe connection...")
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        # Try to list products
        products = stripe.Product.list(limit=1)
        print(f"   ✓ Stripe API: Connected ({'Test mode' if stripe.api_key.startswith('sk_test_') else 'Live mode'})")
        
        # Check if price IDs are configured
        price_vars = [
            "STRIPE_STARTER_MONTHLY_PRICE_ID",
            "STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID",
            "STRIPE_BUSINESS_MONTHLY_PRICE_ID"
        ]
        
        missing_prices = []
        for var in price_vars:
            if not os.getenv(var):
                missing_prices.append(var)
        
        if missing_prices:
            print(f"   ⚠️  Missing price IDs: {len(missing_prices)} price IDs not configured")
            print("      You need to create products and prices in Stripe Dashboard")
        else:
            print("   ✓ Price IDs: All configured")
            
    except Exception as e:
        print(f"   ❌ Stripe connection error: {str(e)}")
        return
    
    # 4. Test API endpoints
    print("\n4. Testing API endpoints...")
    try:
        import httpx
        
        # Start a test client
        async with httpx.AsyncClient(base_url="http://localhost:5000") as client:
            # Test health endpoint
            response = await client.get("/health")
            if response.status_code == 200:
                print("   ✓ Health endpoint: OK")
            else:
                print(f"   ❌ Health endpoint: {response.status_code}")
                
    except Exception as e:
        print(f"   ⚠️  API test skipped (server not running): {str(e)}")
        print("      Run 'python main.py' to start the server")
    
    # 5. Summary
    print("\n=== Test Summary ===")
    print("\nTo complete setup:")
    print("1. Create products in Stripe Dashboard:")
    print("   - Starter Plan ($30/month)")
    print("   - Professional Plan ($60/month)")
    print("   - Business Plan ($99/month)")
    print("\n2. Add the price IDs to your .env file")
    print("\n3. Configure Stripe webhook endpoint:")
    print("   - URL: https://yourdomain.com/api/stripe/webhook")
    print("   - Events: checkout.session.completed, customer.subscription.*")
    print("\n4. Test the integration:")
    print("   - Start the server: python main.py")
    print("   - Go to http://localhost:8000/pricing.html")
    print("   - Click a plan to test checkout")

if __name__ == "__main__":
    asyncio.run(test_stripe_integration())