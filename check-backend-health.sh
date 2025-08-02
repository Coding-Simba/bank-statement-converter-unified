#!/bin/bash

# Quick health check for backend
echo "🔍 Checking backend health..."

# Check backend status
echo -n "Backend service: "
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 \
    "sudo systemctl is-active bankcsv-backend" 2>/dev/null || echo "inactive"

# Test login endpoint
echo -n "Login endpoint: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://bankcsvconverter.com/v2/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}')

if [ "$STATUS" = "401" ] || [ "$STATUS" = "400" ]; then
    echo "✅ Working (Status: $STATUS)"
elif [ "$STATUS" = "502" ]; then
    echo "❌ Backend down (502)"
else
    echo "⚠️  Unexpected status: $STATUS"
fi

# Test health endpoint
echo -n "Health endpoint: "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/health)
if [ "$HEALTH" = "200" ]; then
    echo "✅ OK"
else
    echo "⚠️  Status: $HEALTH"
fi