#\!/bin/bash

echo "Testing Bank PDFs"
echo "================="

# Create test account
TEST_EMAIL="banks$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"TestPass123\!\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to get access token"
    exit 1
fi

echo "Testing Woodforest PDF (expect ~51 transactions)..."
if [ -f "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "file=@/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf")
    
    STATEMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('id', ''))" 2>/dev/null)
    
    if [ -n "$STATEMENT_ID" ]; then
        curl -s "https://bankcsvconverter.com/api/statement/$STATEMENT_ID/download" \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -o woodforest_test.csv
        
        TRANS_COUNT=$(($(wc -l < woodforest_test.csv) - 1))
        echo "Woodforest: $TRANS_COUNT transactions"
        
        if [ $TRANS_COUNT -ge 45 ]; then
            echo "✅ Woodforest parser working\!"
        else
            echo "❌ Woodforest parser needs work"
        fi
    fi
fi

echo -e "\nTest complete\!"

