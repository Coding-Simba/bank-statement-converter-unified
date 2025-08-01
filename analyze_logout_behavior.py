#!/usr/bin/env python3
"""
Cross-Tab Logout Analysis Script

This script analyzes the current authentication system to identify
potential issues with cross-tab logout behavior.
"""

import os
import re
import json
from pathlib import Path

def analyze_auth_system():
    """Analyze the authentication system for cross-tab logout issues."""
    
    print("🔍 Analyzing Cross-Tab Logout Implementation")
    print("=" * 60)
    
    issues = []
    recommendations = []
    
    # Check JavaScript authentication files
    js_files = [
        'js/auth-unified.js',
        'js/auth-fixed.js', 
        'js/auth.js',
        'js/auth-service.js'
    ]
    
    print("\n📁 JavaScript Authentication Files:")
    for js_file in js_files:
        if os.path.exists(js_file):
            print(f"  ✅ {js_file}")
            analyze_js_file(js_file, issues, recommendations)
        else:
            print(f"  ❌ {js_file} (not found)")
    
    # Check HTML files for logout buttons
    print("\n🌐 HTML Files with Logout Buttons:")
    html_files = Path('.').glob('*.html')
    logout_pages = []
    
    for html_file in html_files:
        content = html_file.read_text()
        if 'logout' in content.lower():
            logout_pages.append(str(html_file))
            print(f"  ✅ {html_file}")
            analyze_html_logout(str(html_file), content, issues, recommendations)
    
    # Check backend logout implementation
    print("\n🔧 Backend Authentication:")
    backend_auth_files = [
        'backend/api/auth_cookie.py',
        'backend/api/auth.py'
    ]
    
    for auth_file in backend_auth_files:
        if os.path.exists(auth_file):
            print(f"  ✅ {auth_file}")
            analyze_backend_auth(auth_file, issues, recommendations)
        else:
            print(f"  ❌ {auth_file} (not found)")
    
    # Analyze cross-tab communication mechanisms
    print("\n🔄 Cross-Tab Communication Analysis:")
    analyze_cross_tab_mechanisms(issues, recommendations)
    
    # Print findings
    print("\n" + "=" * 60)
    print("🚨 IDENTIFIED ISSUES:")
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("  ✅ No major issues identified")
    
    print("\n💡 RECOMMENDATIONS:")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("  ✅ Current implementation appears solid")
    
    # Generate test scenarios
    print("\n📋 SUGGESTED TEST SCENARIOS:")
    generate_test_scenarios()

def analyze_js_file(filepath, issues, recommendations):
    """Analyze JavaScript authentication file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for logout function
        if 'logout' not in content.lower():
            issues.append(f"{filepath}: No logout function found")
            return
        
        # Check for cross-tab communication
        if 'localStorage' in content:
            if 'storage' not in content.lower() or 'addEventListener' not in content:
                issues.append(f"{filepath}: Uses localStorage but no storage event listener")
                recommendations.append(f"Add storage event listener in {filepath} for cross-tab sync")
        
        # Check for proper cookie clearing
        if 'logout' in content and 'removeItem' not in content:
            issues.append(f"{filepath}: Logout function may not clear localStorage")
        
        # Check for window location redirect
        if 'logout' in content and 'window.location' in content:
            recommendations.append(f"{filepath}: Consider adding cross-tab notification before redirect")
        
    except Exception as e:
        issues.append(f"Error reading {filepath}: {e}")

def analyze_html_logout(filepath, content, issues, recommendations):
    """Analyze HTML file for logout button implementation."""
    
    # Check for logout button IDs
    logout_patterns = [
        r'id=["\']logout',
        r'class=["\'][^"\']*logout',
        r'href=["\'][^"\']*logout'
    ]
    
    logout_elements = []
    for pattern in logout_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        logout_elements.extend(matches)
    
    if not logout_elements:
        return  # No logout elements found
    
    # Check if logout elements have proper event handlers
    if 'onclick' not in content.lower() and 'addEventListener' not in content.lower():
        issues.append(f"{filepath}: Logout buttons found but no event handlers")

def analyze_backend_auth(filepath, issues, recommendations):
    """Analyze backend authentication implementation."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for logout endpoint
        if '@router.post("/logout")' not in content and 'def logout' not in content:
            issues.append(f"{filepath}: No logout endpoint found")
            return
        
        # Check for proper cookie clearing
        if 'logout' in content.lower():
            if 'delete_cookie' not in content and 'clear' not in content.lower():
                issues.append(f"{filepath}: Logout endpoint may not clear cookies properly")
            
            # Check for session invalidation
            if 'session' in content.lower() and 'invalidate' not in content.lower():
                recommendations.append(f"{filepath}: Consider adding session invalidation")
        
    except Exception as e:
        issues.append(f"Error reading {filepath}: {e}")

def analyze_cross_tab_mechanisms(issues, recommendations):
    """Analyze cross-tab communication mechanisms."""
    
    mechanisms = {
        'localStorage_events': False,
        'broadcast_channel': False,
        'shared_worker': False,
        'service_worker': False,
        'cookie_polling': False
    }
    
    # Check for storage event listeners
    js_files = Path('.').glob('**/*.js')
    for js_file in js_files:
        try:
            content = js_file.read_text()
            if 'storage' in content.lower() and 'addEventListener' in content:
                mechanisms['localStorage_events'] = True
            if 'BroadcastChannel' in content:
                mechanisms['broadcast_channel'] = True
            if 'SharedWorker' in content:
                mechanisms['shared_worker'] = True
            if 'serviceWorker' in content:
                mechanisms['service_worker'] = True
        except:
            continue
    
    active_mechanisms = [k for k, v in mechanisms.items() if v]
    
    if not active_mechanisms:
        issues.append("No cross-tab communication mechanisms detected")
        recommendations.append("Implement localStorage storage events for cross-tab logout sync")
    else:
        print(f"    🔄 Active mechanisms: {', '.join(active_mechanisms)}")

def generate_test_scenarios():
    """Generate comprehensive test scenarios."""
    
    scenarios = [
        {
            "name": "Basic Cross-Tab Logout",
            "steps": [
                "1. Open 3 tabs: Dashboard, Settings, Convert PDF",
                "2. Login in Dashboard tab",
                "3. Verify all tabs show authenticated state",
                "4. Click logout in Dashboard",
                "5. Check if other tabs automatically update"
            ]
        },
        {
            "name": "Cookie Persistence Test",
            "steps": [
                "1. Login and check browser cookies",
                "2. Note access_token and refresh_token values",
                "3. Logout from one tab",
                "4. Check if cookies are cleared from browser",
                "5. Verify expired/cleared cookies in DevTools"
            ]
        },
        {
            "name": "Protected Route Access",
            "steps": [
                "1. Login and navigate to protected page (dashboard)",
                "2. Logout from another tab",
                "3. Try to refresh the protected page",
                "4. Should redirect to login page",
                "5. Try to access /v2/api/auth/profile - should return 401"
            ]
        },
        {
            "name": "Multiple Session Test",
            "steps": [
                "1. Login in Chrome tab",
                "2. Login in Chrome incognito tab",
                "3. Logout from regular tab",
                "4. Check if incognito session remains active",
                "5. This should work independently"
            ]
        },
        {
            "name": "Storage Event Propagation",
            "steps": [
                "1. Open DevTools in multiple tabs",
                "2. Monitor localStorage changes",
                "3. Login in one tab",
                "4. Check localStorage 'user' key in all tabs",
                "5. Logout and verify 'user' key removal propagates"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        for step in scenario['steps']:
            print(f"   {step}")

def main():
    """Main analysis function."""
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    analyze_auth_system()
    
    print("\n" + "=" * 60)
    print("🧪 TESTING INSTRUCTIONS:")
    print("\n1. Open the test page: test_cross_tab_logout.html")
    print("2. Follow the step-by-step testing guide")
    print("3. Use browser DevTools to monitor:")
    print("   - Network tab for logout API calls")
    print("   - Application tab for cookie changes")
    print("   - Console for JavaScript errors")
    print("4. Document any issues found")
    
    print("\n🔧 DEBUGGING TIPS:")
    print("- Check browser console for JavaScript errors")
    print("- Monitor network requests during logout")
    print("- Verify cookie deletion in DevTools > Application > Cookies")
    print("- Test in multiple browsers (Chrome, Firefox, Safari)")
    print("- Test with browser extensions disabled")

if __name__ == "__main__":
    main()