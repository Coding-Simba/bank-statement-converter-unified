#!/bin/bash

# Check JS Files
echo "🔍 Checking JavaScript Files"
echo "==========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Check via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. What auth-unified file is being referenced in HTML?"
grep "auth-unified.*\.js" login.html pricing.html signup.html | head -10

echo -e "\n2. Does that file actually exist?"
ls -la js/auth-unified-1754075455.js

echo -e "\n3. Let's check if the file has any issues:"
head -50 js/auth-unified-1754075455.js | grep -E "(function|class|const|let|var)" | head -20

echo -e "\n4. Let's test the simple-login.html page directly:"
echo "Testing if simple-login.html is accessible:"
curl -s -I https://bankcsvconverter.com/simple-login.html | head -5

echo -e "\n5. Let's create an even simpler test:"
cat > ultra-simple-test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Ultra Simple Test</title>
</head>
<body>
    <h1>Ultra Simple API Test</h1>
    <button onclick="testAPI()">Test Login API</button>
    <pre id="result"></pre>
    
    <script>
        function testAPI() {
            fetch('https://bankcsvconverter.com/api/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: 'test@example.com', password: 'test123'})
            })
            .then(r => r.text())
            .then(text => {
                document.getElementById('result').textContent = text;
            })
            .catch(err => {
                document.getElementById('result').textContent = 'Error: ' + err;
            });
        }
    </script>
</body>
</html>
EOF

echo -e "\n6. Let's check what requests are actually being made:"
echo "Recent API requests from nginx logs:"
sudo tail -50 /var/log/nginx/access.log | grep -E "/api/auth|/v2/api" | tail -10

echo -e "\n7. Test direct API access from command line:"
echo "Testing from server:"
curl -X POST https://bankcsvconverter.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -k -s | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ API Working' if 'access_token' in d else '❌ API Failed')"

ENDSSH

echo -e "\nYou can now try: https://bankcsvconverter.com/ultra-simple-test.html"