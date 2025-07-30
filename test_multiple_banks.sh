#\!/bin/bash

echo "Testing Multiple Bank PDFs"
echo "=========================="

# Create test account
TEST_EMAIL="multibank$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"TestPass123\!\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Got access token"
echo ""

# Test PDFs with expected counts
declare -A test_pdfs=(
    ["/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf"]=51
    ["/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf"]=30
    ["/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf"]=9
    ["/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"]=15
)

for pdf_path in "${\!test_pdfs[@]}"; do
    expected=${test_pdfs[$pdf_path]}
    bank_name=$(basename "$pdf_path" | cut -d'.' -f1)
    
    echo "Testing: $bank_name (expect ~$expected transactions)"
    echo "-----------------------------------------------"
    
    # Upload
    UPLOAD_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "file=@$pdf_path")
    
    STATEMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))" 2>/dev/null)
    
    if [ "$STATEMENT_ID" \!= "error" ]; then
        # Download CSV
        curl -s "https://bankcsvconverter.com/api/statement/$STATEMENT_ID/download" \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -o "test_${bank_name// /_}.csv"
        
        # Count transactions
        TRANS_COUNT=$(($(wc -l < "test_${bank_name// /_}.csv" 2>/dev/null || echo 1) - 1))
        
        if [ $TRANS_COUNT -ge $((expected - 5)) ] && [ $TRANS_COUNT -le $((expected + 5)) ]; then
            echo "✅ SUCCESS: Got $TRANS_COUNT transactions"
        else
            echo "❌ FAILED: Got $TRANS_COUNT transactions (expected ~$expected)"
            echo "First few lines:"
            head -5 "test_${bank_name// /_}.csv" 2>/dev/null
        fi
    else
        echo "❌ Upload failed"
    fi
    
    echo ""
done

# Cleanup
rm -f test_*.csv

echo "Testing complete\!"

