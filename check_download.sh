#\!/bin/bash

# Get auth token
TEST_EMAIL="test$(date +%s)@example.com"
REGISTER_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"fullName\":\"Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"TestPass123\!\"}")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Upload file
TEST_PDF="/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf"
UPLOAD_RESPONSE=$(curl -s -X POST "https://bankcsvconverter.com/api/convert" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@$TEST_PDF")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

# Extract filename
FILENAME=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['filename'])")
FILE_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo -e "\nTrying to download CSV..."

# Try different download endpoints
echo -e "\n1. Direct filename download:"
curl -s "https://bankcsvconverter.com/downloads/$FILENAME" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o test_download1.csv

echo "First 5 lines:"
head -5 test_download1.csv

echo -e "\n2. API download endpoint:"
curl -s "https://bankcsvconverter.com/api/download/$FILE_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o test_download2.csv

echo "First 5 lines:"
head -5 test_download2.csv

echo -e "\n3. Direct download link:"
curl -s -L "https://bankcsvconverter.com/download/$FILENAME" \
  -o test_download3.csv

echo "First 5 lines:"
head -5 test_download3.csv

