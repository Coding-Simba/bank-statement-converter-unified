#!/bin/bash

echo "Debugging File Upload Response"
echo "=============================="

# Create test account
TEST_EMAIL="debug$(date +%s)@example.com"
echo "Creating account: $TEST_EMAIL"

# Register
REGISTER_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Debug User\",\"email\":\"$TEST_EMAIL\",\"password\":\"TestPass123!\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Registration failed"
    exit 1
fi

echo "Got access token"
echo ""

# Test file upload
TEST_PDF="/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"

echo "Uploading PDF and showing full response..."
echo "==========================================="

# Make request and save full response
RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@$TEST_PDF")

echo "Raw Response:"
echo "$RESPONSE" | head -200

echo -e "\n\nPretty JSON (if valid):"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "Not valid JSON"

echo -e "\n\nChecking response structure..."
echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Response type: {type(data)}')
    print(f'Keys: {list(data.keys()) if isinstance(data, dict) else \"Not a dict\"}')
    if 'data' in data:
        print(f'Data keys: {list(data[\"data\"].keys())}')
    if 'csv_content' in data:
        print('Has CSV content')
    if 'transactions' in data:
        print(f'Direct transactions count: {len(data[\"transactions\"])}')
    elif 'data' in data and 'transactions' in data['data']:
        print(f'Nested transactions count: {len(data[\"data\"][\"transactions\"])}')
except Exception as e:
    print(f'Error parsing: {e}')
"