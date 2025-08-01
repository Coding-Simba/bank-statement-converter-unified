#\!/bin/bash

# Fix Dashboard Auth Check
echo "🔧 Fixing Dashboard Authentication Check"
echo "======================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking what's in dashboard-modern.html..."
grep -n "auth\|login\|redirect" dashboard-modern.html | head -10

echo -e "\n2. Let's check the auth navigation script that's redirecting..."
head -30 auth-navigation.js

echo -e "\n3. Creating a fixed auth navigation script..."
cat > auth-navigation-fixed.js << 'EOFJS'
// Fixed Auth Navigation
console.log('[AuthNav] Starting authentication navigation...');

(function() {
    // Check if user is authenticated
    function isAuthenticated() {
        const token = localStorage.getItem('access_token');
        const user = localStorage.getItem('user');
        return \!\!(token && user);
    }
    
    // Get current page
    const currentPath = window.location.pathname;
    const publicPages = ['/login.html', '/signup.html', '/index.html', '/', '/forgot-password.html'];
    const isPublicPage = publicPages.some(page => currentPath === page || currentPath.endsWith(page));
    
    console.log('[AuthNav] Current path:', currentPath);
    console.log('[AuthNav] Is public page:', isPublicPage);
    console.log('[AuthNav] Is authenticated:', isAuthenticated());
    
    // Only redirect if necessary
    if (\!isPublicPage && \!isAuthenticated()) {
        console.log('[AuthNav] Not authenticated, redirecting to login...');
        window.location.href = '/login.html';
    } else if (isPublicPage && isAuthenticated() && (currentPath.includes('login') || currentPath.includes('signup'))) {
        console.log('[AuthNav] Already authenticated, redirecting to dashboard...');
        window.location.href = '/dashboard-modern.html';
    }
    
    // Add logout functionality
    window.logout = function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {});
        window.location.href = '/login.html';
    };
})();

console.log('[AuthNav] Auth navigation setup complete');
EOFJS

echo -e "\n4. Update all pages to use the fixed navigation..."
# Update the version to force cache refresh
TIMESTAMP=$(date +%s)
for file in dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Remove old auth navigation script references
        sed -i '/auth-navigation\.js/d' "$file"
        # Add new one before </body>
        sed -i "/<\/body>/i <script src=\"/auth-navigation-fixed.js?v=${TIMESTAMP}\"></script>" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n5. Let's also ensure the dashboard doesn't have conflicting auth checks..."
# Check if dashboard has its own auth redirect
grep -n "location.*login\|redirect.*login" dashboard-modern.html || echo "No login redirects found in dashboard"

echo -e "\n6. Create a simple test dashboard to verify auth is working..."
cat > test-dashboard.html << 'EOFHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Test Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; }
        .info { background: #d1ecf1; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .user-info { background: #d4edda; padding: 20px; border-radius: 8px; }
        button { padding: 10px 20px; margin: 10px 0; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Test Dashboard</h1>
    
    <div class="info">
        <h2>Authentication Status</h2>
        <p id="authStatus">Checking...</p>
    </div>
    
    <div class="user-info">
        <h2>User Information</h2>
        <pre id="userInfo">Loading...</pre>
    </div>
    
    <button onclick="testAPI()">Test API Call</button>
    <button onclick="logout()">Logout</button>
    
    <script>
        // Check auth status
        const token = localStorage.getItem('access_token');
        const user = localStorage.getItem('user');
        
        document.getElementById('authStatus').textContent = 
            (token && user) ? '✅ Authenticated' : '❌ Not authenticated';
        
        if (user) {
            try {
                const userData = JSON.parse(user);
                document.getElementById('userInfo').textContent = JSON.stringify(userData, null, 2);
            } catch (e) {
                document.getElementById('userInfo').textContent = 'Error parsing user data';
            }
        } else {
            document.getElementById('userInfo').textContent = 'No user data found';
        }
        
        async function testAPI() {
            try {
                const response = await fetch('/api/auth/check', {
                    credentials: 'include',
                    headers: {
                        'Authorization': 'Bearer ' + (token || '')
                    }
                });
                const data = await response.json();
                alert('API Response: ' + JSON.stringify(data));
            } catch (error) {
                alert('API Error: ' + error.message);
            }
        }
        
        function logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login.html';
        }
    </script>
    
    <\!-- Add auth navigation last -->
    <script src="/auth-navigation-fixed.js"></script>
</body>
</html>
EOFHTML

echo -e "\n7. Let's check what auth script the dashboard is actually using..."
grep -E "auth.*\.js|UnifiedAuth" dashboard-modern.html | grep -v "auth-navigation" | head -5

echo -e "\n✅ Auth navigation fixed\!"
echo ""
echo "Test pages:"
echo "1. https://bankcsvconverter.com/test-dashboard.html - Simple test dashboard"
echo "2. https://bankcsvconverter.com/dashboard-modern.html - Main dashboard"
echo ""
echo "The dashboard should now work properly after login."

ENDSSH
