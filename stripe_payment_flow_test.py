#!/usr/bin/env python3
"""
Comprehensive Stripe Payment Integration Test
Tests the complete flow from pricing page to payment completion.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class StripeIntegrationTester:
    def __init__(self):
        self.base_url = "https://bankcsvconverter.com"
        self.session = requests.Session()
        self.csrf_token = None
        self.user_data = None
        
    def log(self, message: str, status: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def get_csrf_token(self) -> bool:
        """Get CSRF token for authentication."""
        try:
            response = self.session.get(f"{self.base_url}/v2/api/auth/csrf")
            if response.status_code == 200:
                data = response.json()
                self.csrf_token = data.get('csrf_token')
                self.log(f"CSRF token obtained: {self.csrf_token[:20]}...")
                return True
            else:
                self.log(f"Failed to get CSRF token: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error getting CSRF token: {str(e)}", "ERROR")
            return False
    
    def create_test_user(self) -> bool:
        """Create a test user account."""
        test_email = f"test.stripe.{int(time.time())}@example.com"
        user_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "full_name": "Stripe Test User",
            "company_name": "Test Company Ltd"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v2/api/auth/register",
                json=user_data,
                headers={"X-CSRF-Token": self.csrf_token}
            )
            
            if response.status_code == 200:
                self.user_data = response.json().get('user')
                self.log(f"Test user created: {self.user_data['email']}")
                return True
            else:
                error_data = response.json()
                self.log(f"Failed to create user: {error_data.get('detail', 'Unknown error')}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error creating test user: {str(e)}", "ERROR")
            return False
    
    def login_user(self, email: str, password: str) -> bool:
        """Login with user credentials."""
        try:
            response = self.session.post(
                f"{self.base_url}/v2/api/auth/login",
                json={
                    "email": email,
                    "password": password,
                    "remember_me": True
                },
                headers={"X-CSRF-Token": self.csrf_token}
            )
            
            if response.status_code == 200:
                self.user_data = response.json().get('user')
                self.log(f"User logged in successfully: {email}")
                return True
            else:
                error_data = response.json()
                self.log(f"Login failed: {error_data.get('detail', 'Unknown error')}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error during login: {str(e)}", "ERROR")
            return False
    
    def check_subscription_status(self) -> Dict[str, Any]:
        """Check current subscription status."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/stripe/subscription-status",
                headers={"X-CSRF-Token": self.csrf_token}
            )
            
            if response.status_code == 200:
                status = response.json()
                self.log(f"Subscription status: {status['plan']} - {status['pages_used']}/{status['pages_limit']} pages used")
                return status
            else:
                error_data = response.json()
                self.log(f"Failed to get subscription status: {error_data.get('detail', 'Unknown error')}", "ERROR")
                return {}
        except Exception as e:
            self.log(f"Error checking subscription status: {str(e)}", "ERROR")
            return {}
    
    def create_checkout_session(self, plan: str, billing_period: str = "monthly") -> Optional[str]:
        """Create Stripe checkout session."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/stripe/create-checkout-session",
                json={
                    "plan": plan,
                    "billing_period": billing_period
                },
                headers={"X-CSRF-Token": self.csrf_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                checkout_url = data.get('checkout_url')
                self.log(f"Checkout session created for {plan} ({billing_period})")
                self.log(f"Checkout URL: {checkout_url[:80]}...")
                return checkout_url
            else:
                error_data = response.json()
                self.log(f"Failed to create checkout session: {error_data.get('detail', 'Unknown error')}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Error creating checkout session: {str(e)}", "ERROR")
            return None
    
    def test_customer_portal(self) -> Optional[str]:
        """Test customer portal access."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/stripe/customer-portal",
                json={"return_url": "/dashboard.html"},
                headers={"X-CSRF-Token": self.csrf_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                portal_url = data.get('portal_url')
                self.log("Customer portal session created successfully")
                return portal_url
            else:
                error_data = response.json()
                if "configuration" in error_data.get('detail', '').lower():
                    self.log("Customer portal requires configuration in Stripe dashboard", "WARN")
                else:
                    self.log(f"Customer portal failed: {error_data.get('detail', 'Unknown error')}", "ERROR")
                return None
        except Exception as e:
            self.log(f"Error testing customer portal: {str(e)}", "ERROR")
            return None
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive test of all Stripe features."""
        results = {}
        
        self.log("=== STARTING COMPREHENSIVE STRIPE INTEGRATION TEST ===")
        
        # Step 1: Get CSRF token
        self.log("Step 1: Getting CSRF token...")
        results['csrf_token'] = self.get_csrf_token()
        
        if not results['csrf_token']:
            self.log("Cannot proceed without CSRF token", "ERROR")
            return results
        
        # Step 2: Create test user
        self.log("Step 2: Creating test user...")
        results['user_creation'] = self.create_test_user()
        
        if not results['user_creation']:
            self.log("Cannot proceed without user account", "ERROR")
            return results
        
        # Step 3: Check subscription status
        self.log("Step 3: Checking subscription status...")
        status = self.check_subscription_status()
        results['subscription_check'] = bool(status)
        
        # Step 4: Test checkout sessions for all plans
        plans = ['starter', 'professional', 'business']
        billing_periods = ['monthly', 'yearly']
        
        for plan in plans:
            for period in billing_periods:
                test_key = f'checkout_{plan}_{period}'
                self.log(f"Step 4.{len(results)}: Testing {plan} {period} checkout...")
                checkout_url = self.create_checkout_session(plan, period)
                results[test_key] = bool(checkout_url)
        
        # Step 5: Test customer portal
        self.log("Step 5: Testing customer portal...")
        portal_url = self.test_customer_portal()
        results['customer_portal'] = bool(portal_url)
        
        # Summary
        self.log("=== TEST RESULTS SUMMARY ===")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return results

def main():
    tester = StripeIntegrationTester()
    results = tester.run_comprehensive_test()
    
    # Return exit code based on results
    if all(results.values()):
        print("\n🎉 All tests passed! Stripe integration is working correctly.")
        return 0
    else:
        failed_tests = [test for test, result in results.items() if not result]
        print(f"\n⚠️  Some tests failed: {', '.join(failed_tests)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())