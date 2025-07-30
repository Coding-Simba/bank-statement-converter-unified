#!/bin/bash

echo "Testing Validation Feature"
echo "========================="

# Test credentials
BASE_URL="https://bankcsvconverter.com"
TEST_EMAIL="validation_test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"

# 1. Register user
echo "1. Creating test account..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Validation Test\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    exit 1
fi

echo "✅ Got access token"

# 2. Upload a test PDF
echo -e "\n2. Uploading test PDF..."
TEST_PDF="/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/convert" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@$TEST_PDF")

STATEMENT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$STATEMENT_ID" ]; then
    echo "❌ Failed to upload PDF"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Uploaded PDF, Statement ID: $STATEMENT_ID"

# 3. Test validation API endpoints
echo -e "\n3. Testing validation endpoints..."

# Get validation data
echo "   Getting validation data..."
VALIDATION_RESPONSE=$(curl -s -X GET "$BASE_URL/api/statement/$STATEMENT_ID/validation" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$VALIDATION_RESPONSE" | grep -q "transactions"; then
    echo "   ✅ Retrieved validation data"
    
    # Count transactions
    TRANS_COUNT=$(echo "$VALIDATION_RESPONSE" | grep -o '"date"' | wc -l)
    echo "   Found $TRANS_COUNT transactions"
else
    echo "   ❌ Failed to get validation data"
    echo "   Response: $VALIDATION_RESPONSE"
fi

# Test validation update
echo -e "\n   Testing validation update..."
UPDATE_DATA='{
  "transactions": [
    {
      "date": "2022-02-11",
      "description": "Test Transaction - Validated",
      "amount": 100.50,
      "balance": 1000.00
    }
  ]
}'

UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/statement/$STATEMENT_ID/validation" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$UPDATE_DATA")

if echo "$UPDATE_RESPONSE" | grep -q "success"; then
    echo "   ✅ Validation update successful"
else
    echo "   ❌ Validation update failed"
    echo "   Response: $UPDATE_RESPONSE"
fi

# 4. Test validation page access
echo -e "\n4. Testing validation page..."
VALIDATION_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/validation.html?id=$STATEMENT_ID")

if [ "$VALIDATION_PAGE_STATUS" == "200" ]; then
    echo "✅ Validation page accessible"
else
    echo "❌ Validation page returned HTTP $VALIDATION_PAGE_STATUS"
fi

# 5. Test validated CSV download
echo -e "\n5. Testing validated CSV download..."
curl -s "$BASE_URL/api/statement/$STATEMENT_ID/download?validated=true" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o test_validated.csv

if [ -f test_validated.csv ]; then
    echo "✅ Downloaded validated CSV"
    echo "   First few lines:"
    head -5 test_validated.csv
    rm test_validated.csv
else
    echo "❌ Failed to download validated CSV"
fi

echo -e "\n✅ Validation feature test complete!"
echo "You can manually test the UI at:"
echo "$BASE_URL/validation.html?id=$STATEMENT_ID"