#\!/bin/bash

echo "Testing Woodforest Parser"
echo "========================"

# Get auth token
AUTH_JSON=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Test User\",\"email\":\"wood$(date +%s)@example.com\",\"password\":\"TestPass123\!\"}")

ACCESS_TOKEN=$(echo "$AUTH_JSON" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token obtained"

# Upload Woodforest PDF
echo "Uploading Woodforest PDF..."
UPLOAD_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf")

echo "Upload response: $UPLOAD_RESPONSE"

# Extract ID
STATEMENT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -n "$STATEMENT_ID" ]; then
    echo "Statement ID: $STATEMENT_ID"
    
    # Download CSV
    curl -s "https://bankcsvconverter.com/api/statement/$STATEMENT_ID/download" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -o woodforest.csv
    
    echo -e "\nFirst 10 lines of CSV:"
    head -10 woodforest.csv
    
    TRANS_COUNT=$(($(wc -l < woodforest.csv) - 1))
    echo -e "\nTotal transactions: $TRANS_COUNT"
    
    if [ $TRANS_COUNT -ge 45 ]; then
        echo "✅ Woodforest parser is working\!"
    else
        echo "❌ Woodforest parser needs work (expected ~51)"
    fi
fi

