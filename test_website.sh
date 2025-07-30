#!/bin/bash

# Comprehensive Website Test Script

echo "Testing BankCSVConverter.com"
echo "============================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="https://bankcsvconverter.com"

# Test user credentials
TEST_EMAIL="test$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"
TEST_NAME="Test User"

echo "1. Testing Homepage"
echo "-------------------"
if curl -s "$BASE_URL" | grep -q "Bank Statement Converter"; then
    echo -e "${GREEN}✅ Homepage loads successfully${NC}"
else
    echo -e "${RED}❌ Homepage failed to load${NC}"
fi

echo ""
echo "2. Testing Registration"
echo "----------------------"
echo "Creating account: $TEST_EMAIL"

REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"$TEST_NAME\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Registration successful${NC}"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "   Access token received"
else
    echo -e "${RED}❌ Registration failed${NC}"
    echo "   Response: $REGISTER_RESPONSE"
fi

echo ""
echo "3. Testing Login"
echo "----------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Login successful${NC}"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
else
    echo -e "${RED}❌ Login failed${NC}"
fi

echo ""
echo "4. Testing File Upload"
echo "---------------------"
# Test with a sample PDF
TEST_PDF="/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"

if [ -f "$TEST_PDF" ]; then
    echo "Uploading: $(basename "$TEST_PDF")"
    
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/convert" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "file=@$TEST_PDF")
    
    if echo "$UPLOAD_RESPONSE" | grep -q "transactions\|csv"; then
        echo -e "${GREEN}✅ File upload successful${NC}"
        
        # Count transactions
        TRANSACTION_COUNT=$(echo "$UPLOAD_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'transactions' in data:
        print(len(data['transactions']))
    else:
        print('0')
except:
    print('0')
" 2>/dev/null)
        
        echo "   Transactions extracted: $TRANSACTION_COUNT"
        
        if [ "$TRANSACTION_COUNT" -gt 10 ]; then
            echo -e "${GREEN}   ✅ Parser working correctly (expected ~17 for Westpac)${NC}"
        else
            echo -e "${RED}   ❌ Low transaction count${NC}"
        fi
    else
        echo -e "${RED}❌ File upload failed${NC}"
        echo "   Response: $UPLOAD_RESPONSE"
    fi
else
    echo -e "${RED}❌ Test PDF not found${NC}"
fi

echo ""
echo "5. Testing Multiple PDFs"
echo "-----------------------"
TEST_PDFS=(
    "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf:51"
    "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf:9"
    "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf:30"
)

for pdf_info in "${TEST_PDFS[@]}"; do
    PDF_PATH="${pdf_info%%:*}"
    EXPECTED="${pdf_info##*:}"
    
    if [ -f "$PDF_PATH" ]; then
        echo -n "Testing $(basename "$PDF_PATH") (expect $EXPECTED transactions)... "
        
        UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/convert" \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -F "file=@$PDF_PATH")
        
        TRANSACTION_COUNT=$(echo "$UPLOAD_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'transactions' in data:
        print(len(data['transactions']))
    elif 'data' in data and 'transactions' in data['data']:
        print(len(data['data']['transactions']))
    else:
        print('0')
except:
    print('0')
" 2>/dev/null)
        
        if [ "$TRANSACTION_COUNT" -ge $((EXPECTED - 2)) ]; then
            echo -e "${GREEN}✅ Got $TRANSACTION_COUNT transactions${NC}"
        else
            echo -e "${RED}❌ Got only $TRANSACTION_COUNT transactions${NC}"
        fi
    fi
done

echo ""
echo "6. Testing API Endpoints"
echo "-----------------------"
# Test various API endpoints
endpoints=(
    "/api/auth/me:GET:$ACCESS_TOKEN"
    "/api/convert:GET:$ACCESS_TOKEN"
)

for endpoint_info in "${endpoints[@]}"; do
    IFS=':' read -r endpoint method token <<< "$endpoint_info"
    echo -n "Testing $method $endpoint... "
    
    if [ -n "$token" ]; then
        RESPONSE=$(curl -s -X "$method" "$BASE_URL$endpoint" \
          -H "Authorization: Bearer $token" \
          -w "\n%{http_code}")
    else
        RESPONSE=$(curl -s -X "$method" "$BASE_URL$endpoint" \
          -w "\n%{http_code}")
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    
    if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
        echo -e "${GREEN}✅ HTTP $HTTP_CODE${NC}"
    else
        echo -e "${RED}❌ HTTP $HTTP_CODE${NC}"
    fi
done

echo ""
echo "Test Complete!"
echo "=============="