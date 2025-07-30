#\!/bin/bash

echo "Testing Full Conversion Flow"
echo "============================"

# Create test account
TEST_EMAIL="flow$(date +%s)@example.com"
echo "1. Creating account: $TEST_EMAIL"

REGISTER_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"TestPass123\!\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "   ✓ Got access token"

# Upload file
TEST_PDF="/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"
echo -e "\n2. Uploading PDF..."

UPLOAD_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@$TEST_PDF")

echo "   Upload response: $UPLOAD_RESPONSE"

# Extract statement ID
STATEMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "   Statement ID: $STATEMENT_ID"

# Download CSV
echo -e "\n3. Downloading CSV..."
curl -s "https://bankcsvconverter.com/api/statement/$STATEMENT_ID/download" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o westpac_test.csv

echo "   Downloaded to westpac_test.csv"

# Check content
echo -e "\n4. CSV Content (first 10 lines):"
head -10 westpac_test.csv

echo -e "\n5. Transaction count:"
TRANS_COUNT=$(($(wc -l < westpac_test.csv) - 1))
echo "   $TRANS_COUNT transactions"

if [ $TRANS_COUNT -ge 15 ]; then
    echo "   ✅ Parser working correctly\!"
else
    echo "   ❌ Parser needs fixing (expected ~17 transactions)"
fi

