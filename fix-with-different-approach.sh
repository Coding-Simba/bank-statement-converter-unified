#\!/bin/bash

# Fix with Different Approach
echo "🔧 Using a different approach to fix the auth script"
echo "==================================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Check what's on line 87..."
sed -n '85,90p' js/auth-unified-1754078277.js | nl -v 85

echo -e "\n2. Let's check if there's a pattern - what character encoding is being used?"
file js/auth-unified-1754078277.js

echo -e "\n3. Let's create the script using printf to avoid any shell escaping issues..."
printf '%s\n' \
'// Simple Auth Script' \
'console.log("Loading auth script");' \
'' \
'(function() {' \
'    var UnifiedAuth = {' \
'        user: null,' \
'        initialized: false,' \
'        ' \
'        init: function() {' \
'            this.initialized = true;' \
'            console.log("Auth initialized");' \
'        },' \
'        ' \
'        login: function(email, password) {' \
'            console.log("Login called for:", email);' \
'            ' \
'            return fetch("/api/auth/login", {' \
'                method: "POST",' \
'                credentials: "include",' \
'                headers: {' \
'                    "Content-Type": "application/json"' \
'                },' \
'                body: JSON.stringify({' \
'                    email: email,' \
'                    password: password,' \
'                    remember_me: false' \
'                })' \
'            })' \
'            .then(function(response) {' \
'                return response.json().then(function(data) {' \
'                    if (response.ok) {' \
'                        UnifiedAuth.user = data.user;' \
'                        if (data.access_token) {' \
'                            localStorage.setItem("access_token", data.access_token);' \
'                            localStorage.setItem("user", JSON.stringify(data.user));' \
'                        }' \
'                        return { success: true, user: data.user };' \
'                    } else {' \
'                        return { success: false, error: data.detail || "Login failed" };' \
'                    }' \
'                });' \
'            })' \
'            .catch(function(error) {' \
'                return { success: false, error: error.message };' \
'            });' \
'        },' \
'        ' \
'        logout: function() {' \
'            this.user = null;' \
'            localStorage.removeItem("user");' \
'            localStorage.removeItem("access_token");' \
'            return fetch("/api/auth/logout", {' \
'                method: "POST",' \
'                credentials: "include"' \
'            });' \
'        },' \
'        ' \
'        isAuthenticated: function() {' \
'            return this.user \!== null;' \
'        },' \
'        ' \
'        getUser: function() {' \
'            return this.user;' \
'        },' \
'        ' \
'        makeAuthenticatedRequest: function(url, options) {' \
'            options = options || {};' \
'            options.credentials = "include";' \
'            options.headers = options.headers || {};' \
'            ' \
'            var token = localStorage.getItem("access_token");' \
'            if (token) {' \
'                options.headers["Authorization"] = "Bearer " + token;' \
'            }' \
'            ' \
'            return fetch(url, options);' \
'        }' \
'    };' \
'    ' \
'    // Initialize' \
'    UnifiedAuth.init();' \
'    ' \
'    // Expose globally' \
'    window.UnifiedAuth = UnifiedAuth;' \
'    console.log("UnifiedAuth exposed globally");' \
'})();' > js/auth-script-clean.js

echo -e "\n4. Verify the file was created correctly..."
wc -l js/auth-script-clean.js
head -5 js/auth-script-clean.js

echo -e "\n5. Create timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-script-clean.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n6. Update HTML files..."
for file in login.html signup.html pricing.html; do
    if [ -f "$file" ]; then
        # Use a different sed delimiter to avoid issues
        sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n7. Let's also create a backup using base64 encoding to ensure no corruption..."
cat > js/auth-base64.js << 'EOFB64'
Ly8gU2ltcGxlIEF1dGggU2NyaXB0CmNvbnNvbGUubG9nKCJMb2FkaW5nIGF1dGggc2NyaXB0Iik7Cgood
function() {
    // Decode and eval the base64 script
    var script = atob('dmFyIFVuaWZpZWRBdXRoID0gewogICAgdXNlcjogbnVsbCwKICAgIGluaXRpYWxpemVkOiBmYWxzZSwKICAgIAogICAgaW5pdDogZnVuY3Rpb24oKSB7CiAgICAgICAgdGhpcy5pbml0aWFsaXplZCA9IHRydWU7CiAgICAgICAgY29uc29sZS5sb2coIkF1dGggaW5pdGlhbGl6ZWQiKTsKICAgIH0sCiAgICAKICAgIGxvZ2luOiBmdW5jdGlvbihlbWFpbCwgcGFzc3dvcmQpIHsKICAgICAgICBjb25zb2xlLmxvZygiTG9naW4gY2FsbGVkIGZvcjoiLCBlbWFpbCk7CiAgICAgICAgCiAgICAgICAgcmV0dXJuIGZldGNoKCIvYXBpL2F1dGgvbG9naW4iLCB7CiAgICAgICAgICAgIG1ldGhvZDogIlBPU1QiLAogICAgICAgICAgICBjcmVkZW50aWFsczogImluY2x1ZGUiLAogICAgICAgICAgICBoZWFkZXJzOiB7CiAgICAgICAgICAgICAgICAiQ29udGVudC1UeXBlIjogImFwcGxpY2F0aW9uL2pzb24iCiAgICAgICAgICAgIH0sCiAgICAgICAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsKICAgICAgICAgICAgICAgIGVtYWlsOiBlbWFpbCwKICAgICAgICAgICAgICAgIHBhc3N3b3JkOiBwYXNzd29yZCwKICAgICAgICAgICAgICAgIHJlbWVtYmVyX21lOiBmYWxzZQogICAgICAgICAgICB9KQogICAgICAgIH0pCiAgICAgICAgLnRoZW4oZnVuY3Rpb24ocmVzcG9uc2UpIHsKICAgICAgICAgICAgcmV0dXJuIHJlc3BvbnNlLmpzb24oKS50aGVuKGZ1bmN0aW9uKGRhdGEpIHsKICAgICAgICAgICAgICAgIGlmIChyZXNwb25zZS5vaykgewogICAgICAgICAgICAgICAgICAgIFVuaWZpZWRBdXRoLnVzZXIgPSBkYXRhLnVzZXI7CiAgICAgICAgICAgICAgICAgICAgaWYgKGRhdGEuYWNjZXNzX3Rva2VuKSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJhY2Nlc3NfdG9rZW4iLCBkYXRhLmFjY2Vzc190b2tlbik7CiAgICAgICAgICAgICAgICAgICAgICAgIGxvY2FsU3RvcmFnZS5zZXRJdGVtKCJ1c2VyIiwgSlNPTi5zdHJpbmdpZnkoZGF0YS51c2VyKSk7CiAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgICAgIHJldHVybiB7IHN1Y2Nlc3M6IHRydWUsIHVzZXI6IGRhdGEudXNlciB9OwogICAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgICAgICByZXR1cm4geyBzdWNjZXNzOiBmYWxzZSwgZXJyb3I6IGRhdGEuZGV0YWlsIHx8ICJMb2dpbiBmYWlsZWQiIH07CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgIH0pOwogICAgICAgIH0pCiAgICAgICAgLmNhdGNoKGZ1bmN0aW9uKGVycm9yKSB7CiAgICAgICAgICAgIHJldHVybiB7IHN1Y2Nlc3M6IGZhbHNlLCBlcnJvcjogZXJyb3IubWVzc2FnZSB9OwogICAgICAgIH0pOwogICAgfSwKICAgIAogICAgbG9nb3V0OiBmdW5jdGlvbigpIHsKICAgICAgICB0aGlzLnVzZXIgPSBudWxsOwogICAgICAgIGxvY2FsU3RvcmFnZS5yZW1vdmVJdGVtKCJ1c2VyIik7CiAgICAgICAgbG9jYWxTdG9yYWdlLnJlbW92ZUl0ZW0oImFjY2Vzc190b2tlbiIpOwogICAgICAgIHJldHVybiBmZXRjaCgiL2FwaS9hdXRoL2xvZ291dCIsIHsKICAgICAgICAgICAgbWV0aG9kOiAiUE9TVCIsCiAgICAgICAgICAgIGNyZWRlbnRpYWxzOiAiaW5jbHVkZSIKICAgICAgICB9KTsKICAgIH0sCiAgICAKICAgIGlzQXV0aGVudGljYXRlZDogZnVuY3Rpb24oKSB7CiAgICAgICAgcmV0dXJuIHRoaXMudXNlciAhPT0gbnVsbDsKICAgIH0sCiAgICAKICAgIGdldFVzZXI6IGZ1bmN0aW9uKCkgewogICAgICAgIHJldHVybiB0aGlzLnVzZXI7CiAgICB9LAogICAgCiAgICBtYWtlQXV0aGVudGljYXRlZFJlcXVlc3Q6IGZ1bmN0aW9uKHVybCwgb3B0aW9ucykgewogICAgICAgIG9wdGlvbnMgPSBvcHRpb25zIHx8IHt9OwogICAgICAgIG9wdGlvbnMuY3JlZGVudGlhbHMgPSAiaW5jbHVkZSI7CiAgICAgICAgb3B0aW9ucy5oZWFkZXJzID0gb3B0aW9ucy5oZWFkZXJzIHx8IHt9OwogICAgICAgIAogICAgICAgIHZhciB0b2tlbiA9IGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhY2Nlc3NfdG9rZW4iKTsKICAgICAgICBpZiAodG9rZW4pIHsKICAgICAgICAgICAgb3B0aW9ucy5oZWFkZXJzWyJBdXRob3JpemF0aW9uIl0gPSAiQmVhcmVyICIgKyB0b2tlbjsKICAgICAgICB9CiAgICAgICAgCiAgICAgICAgcmV0dXJuIGZldGNoKHVybCwgb3B0aW9ucyk7CiAgICB9Cn07CgpVbmlmaWVkQXV0aC5pbml0KCk7CndpbmRvdy5VbmlmaWVkQXV0aCA9IFVuaWZpZWRBdXRoOw==');
    eval(script);
    console.log("Auth script loaded from base64");
})();
EOFB64

echo -e "\nNew file created: js/auth-unified-${TIMESTAMP}.js"
echo "Test at: https://bankcsvconverter.com/login.html"

ENDSSH

echo ""
echo "✅ Created auth script using printf to avoid shell escaping\!"
