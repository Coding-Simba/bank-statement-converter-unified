#!/usr/bin/env python3
"""
Quick test script to verify the backend setup
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

async def test_backend():
    async with httpx.AsyncClient() as client:
        print("🔍 Testing Backend API...")
        print("-" * 50)
        
        # Test 1: Check API health
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"✅ API Health Check: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"❌ API not running: {e}")
            print("   Please run: uvicorn main:app --reload --host 0.0.0.0 --port 5000")
            return
        
        # Test 2: Get session for anonymous user
        try:
            response = await client.get(f"{BASE_URL}/api/auth/session")
            session_data = response.json()
            print(f"\n✅ Anonymous Session: {response.status_code}")
            print(f"   Session ID: {session_data.get('session_id', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Session endpoint error: {e}")
        
        # Test 3: Check conversion limits (anonymous)
        try:
            response = await client.get(f"{BASE_URL}/api/check-limit")
            limit_data = response.json()
            print(f"\n✅ Anonymous Limits: {response.status_code}")
            print(f"   Daily Limit: {limit_data.get('daily_limit', 'N/A')}")
            print(f"   Used Today: {limit_data.get('used_today', 'N/A')}")
            print(f"   Remaining: {limit_data.get('remaining', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Limit check error: {e}")
        
        # Test 4: Register a test user
        test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        test_password = "TestPassword123!"
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/register", json={
                "email": test_email,
                "password": test_password
            })
            if response.status_code == 200:
                user_data = response.json()
                print(f"\n✅ User Registration: {response.status_code}")
                print(f"   Email: {test_email}")
                print(f"   Access Token: {user_data.get('access_token', 'N/A')[:20]}...")
                
                # Test 5: Check limits for registered user
                headers = {"Authorization": f"Bearer {user_data.get('access_token')}"}
                response = await client.get(f"{BASE_URL}/api/check-limit", headers=headers)
                limit_data = response.json()
                print(f"\n✅ Registered User Limits: {response.status_code}")
                print(f"   Daily Limit: {limit_data.get('daily_limit', 'N/A')}")
                print(f"   Account Type: {limit_data.get('account_type', 'N/A')}")
            else:
                print(f"\n❌ Registration failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"\n❌ Registration error: {e}")
        
        print("\n" + "-" * 50)
        print("✨ Backend test complete!")

if __name__ == "__main__":
    asyncio.run(test_backend())