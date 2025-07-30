#!/bin/bash

# Test Production Extraction

echo "Testing Transaction Extraction on Production Server"
echo "================================================="

# Test PDFs
TEST_PDFS=(
    "Australia Westpac bank statement.pdf:17"
    "USA Woodforest.pdf:51"
    "USA Suntrust.pdf:9"
    "USA Citizens Bank.pdf:30"
    "Australia Commonwealth J C.pdf:20"
)

echo "Testing extraction via web API..."
echo ""

# Test each PDF
for pdf_info in "${TEST_PDFS[@]}"; do
    PDF_NAME="${pdf_info%%:*}"
    EXPECTED_COUNT="${pdf_info##*:}"
    PDF_PATH="/Users/MAC/Desktop/pdfs/1/$PDF_NAME"
    
    echo "Testing: $PDF_NAME"
    echo "Expected transactions: $EXPECTED_COUNT"
    
    # Upload and convert via API
    if [ -f "$PDF_PATH" ]; then
        # Make API call
        RESPONSE=$(curl -s -X POST http://bankcsvconverter.com/api/upload \
            -F "file=@$PDF_PATH" \
            -H "Accept: application/json" 2>/dev/null)
        
        # Check if response contains error
        if echo "$RESPONSE" | grep -q "error\|Error"; then
            echo "❌ Error in response"
            echo "$RESPONSE" | head -50
        else
            # Try to count transactions in response
            TRANSACTION_COUNT=$(echo "$RESPONSE" | grep -o '"date"' | wc -l)
            echo "Extracted transactions: $TRANSACTION_COUNT"
            
            if [ "$TRANSACTION_COUNT" -ge $((EXPECTED_COUNT - 2)) ]; then
                echo "✅ Good extraction"
            else
                echo "❌ Low extraction count"
            fi
        fi
    else
        echo "❌ PDF file not found: $PDF_PATH"
    fi
    
    echo "---"
    echo ""
done

echo "Test complete!"