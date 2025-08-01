/**
 * Manual Cross-Tab Authentication Test Script
 * Run this in browser console on https://bankcsvconverter.com/cross_tab_auth_test.html
 * 
 * Instructions:
 * 1. Open 4-5 tabs with different pages
 * 2. Run this script in console of one tab
 * 3. Follow the prompts to test cross-tab synchronization
 */

async function runCrossTabAuthTest() {
    console.log('🔄 Starting Cross-Tab Authentication Synchronization Test');
    console.log('==========================================');
    
    const results = {
        browserSupport: {},
        syncTiming: {},
        reliability: {},
        errors: []
    };
    
    // Test 1: Browser Compatibility
    console.log('\n📋 Test 1: Browser Compatibility');
    
    const hasBroadcastChannel = typeof BroadcastChannel !== 'undefined';
    const hasLocalStorage = typeof Storage !== 'undefined';
    const hasStorageEvents = 'onstorage' in window;
    
    results.browserSupport = {
        broadcastChannel: hasBroadcastChannel,
        localStorage: hasLocalStorage,
        storageEvents: hasStorageEvents,
        userAgent: navigator.userAgent
    };
    
    console.log(`  BroadcastChannel: ${hasBroadcastChannel ? '✅' : '❌'}`);
    console.log(`  localStorage: ${hasLocalStorage ? '✅' : '❌'}`);
    console.log(`  Storage Events: ${hasStorageEvents ? '✅' : '❌'}`);
    
    // Test 2: Auth API Connectivity
    console.log('\n🔗 Test 2: Authentication API Connectivity');
    
    try {
        const csrfResponse = await fetch('/v2/api/auth/csrf', { credentials: 'include' });
        const csrfData = await csrfResponse.json();
        console.log('  ✅ CSRF token obtained:', csrfData.csrf_token.substring(0, 10) + '...');
        
        const authResponse = await fetch('/v2/api/auth/check', { credentials: 'include' });
        const authData = await authResponse.json();
        console.log('  ✅ Auth check successful:', authData.authenticated ? 'Authenticated' : 'Not authenticated');
        
        results.apiConnectivity = true;
    } catch (error) {
        console.log('  ❌ API connectivity failed:', error.message);
        results.apiConnectivity = false;
        results.errors.push(`API connectivity: ${error.message}`);
    }
    
    // Test 3: Cross-Tab Event System
    console.log('\n📡 Test 3: Cross-Tab Event System');
    
    let eventsReceived = 0;
    const eventPromises = [];
    
    // Test BroadcastChannel
    if (hasBroadcastChannel) {
        const bcPromise = new Promise((resolve) => {
            const channel = new BroadcastChannel('auth-channel');
            const timeout = setTimeout(() => {
                channel.close();
                resolve({ type: 'broadcast', received: false, time: null });
            }, 5000);
            
            channel.onmessage = (event) => {
                clearTimeout(timeout);
                eventsReceived++;
                console.log('  📡 BroadcastChannel event received:', event.data);
                channel.close();
                resolve({ type: 'broadcast', received: true, time: Date.now() });
            };
            
            // Send test message
            setTimeout(() => {
                channel.postMessage({ type: 'test', timestamp: Date.now() });
            }, 100);
        });
        eventPromises.push(bcPromise);
    }
    
    // Test localStorage events
    if (hasStorageEvents) {
        const storagePromise = new Promise((resolve) => {
            const timeout = setTimeout(() => {
                window.removeEventListener('storage', storageHandler);
                resolve({ type: 'storage', received: false, time: null });
            }, 5000);
            
            const storageHandler = (event) => {
                if (event.key === 'test-cross-tab-sync') {
                    clearTimeout(timeout);
                    eventsReceived++;
                    console.log('  💾 Storage event received:', event.key);
                    window.removeEventListener('storage', storageHandler);
                    resolve({ type: 'storage', received: true, time: Date.now() });
                }
            };
            
            window.addEventListener('storage', storageHandler);
            
            // Trigger storage event
            setTimeout(() => {
                localStorage.setItem('test-cross-tab-sync', Date.now().toString());
                localStorage.removeItem('test-cross-tab-sync');
            }, 100);
        });
        eventPromises.push(storagePromise);
    }
    
    const eventResults = await Promise.all(eventPromises);
    results.eventSystem = eventResults;
    
    eventResults.forEach(result => {
        console.log(`  ${result.received ? '✅' : '❌'} ${result.type} events: ${result.received ? 'Working' : 'Failed'}`);
    });
    
    // Test 4: Authentication Flow
    console.log('\n🔐 Test 4: Authentication Flow Test');
    console.log('  ⚠️  This test requires manual verification in other tabs');
    console.log('  📋 Instructions:');
    console.log('     1. Open 3-4 additional tabs with different pages');
    console.log('     2. Watch for authentication state changes in those tabs');
    console.log('     3. This tab will perform login/logout operations');
    
    const confirm = window.confirm('Ready to test authentication flow? Make sure you have other tabs open.');
    
    if (confirm) {
        // Test login synchronization
        console.log('\n  🔓 Testing login synchronization...');
        const loginStart = Date.now();
        
        try {
            // Get CSRF token
            const csrfResponse = await fetch('/v2/api/auth/csrf', { credentials: 'include' });
            const csrfData = await csrfResponse.json();
            
            // Perform login
            const loginResponse = await fetch('/v2/api/auth/login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfData.csrf_token
                },
                body: JSON.stringify({
                    email: 'test-20250801-134232@example.com',
                    password: 'TestPassword123!',
                    remember_me: false
                })
            });
            
            if (loginResponse.ok) {
                const loginTime = Date.now() - loginStart;
                console.log(`    ✅ Login successful in ${loginTime}ms`);
                results.syncTiming.login = loginTime;
                
                // Wait for sync
                console.log('    ⏳ Waiting 3 seconds for tab synchronization...');
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                const syncVerification = window.confirm('Did other tabs detect the login? (Check navigation/UI changes)');
                results.reliability.loginSync = syncVerification;
                console.log(`    ${syncVerification ? '✅' : '❌'} Login sync verified: ${syncVerification}`);
                
                // Test logout synchronization
                console.log('\n  🚪 Testing logout synchronization...');
                const logoutStart = Date.now();
                
                const logoutResponse = await fetch('/v2/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': csrfData.csrf_token
                    }
                });
                
                if (logoutResponse.ok) {
                    const logoutTime = Date.now() - logoutStart;
                    console.log(`    ✅ Logout successful in ${logoutTime}ms`);
                    results.syncTiming.logout = logoutTime;
                    
                    // Wait for sync
                    console.log('    ⏳ Waiting 3 seconds for tab synchronization...');
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    const logoutSyncVerification = window.confirm('Did other tabs detect the logout? (Check if they show login forms)');
                    results.reliability.logoutSync = logoutSyncVerification;
                    console.log(`    ${logoutSyncVerification ? '✅' : '❌'} Logout sync verified: ${logoutSyncVerification}`);
                } else {
                    console.log('    ❌ Logout failed');
                    results.errors.push('Logout API call failed');
                }
            } else {
                console.log('    ❌ Login failed');
                results.errors.push('Login API call failed');
            }
        } catch (error) {
            console.log('    ❌ Authentication flow error:', error.message);
            results.errors.push(`Auth flow: ${error.message}`);
        }
    }
    
    // Test 5: Performance Analysis
    console.log('\n📊 Test 5: Performance Analysis');
    
    const performanceResults = {
        broadcastChannelLatency: null,
        storageEventLatency: null,
        overallReliability: null
    };
    
    // Measure BroadcastChannel latency
    if (hasBroadcastChannel) {
        console.log('  ⏱️  Measuring BroadcastChannel latency...');
        const latencies = [];
        
        for (let i = 0; i < 5; i++) {
            const start = Date.now();
            const latency = await new Promise((resolve) => {
                const channel = new BroadcastChannel('auth-channel');
                const timeout = setTimeout(() => {
                    channel.close();
                    resolve(null);
                }, 1000);
                
                channel.onmessage = () => {
                    clearTimeout(timeout);
                    const latency = Date.now() - start;
                    channel.close();
                    resolve(latency);
                };
                
                channel.postMessage({ type: 'latency-test', timestamp: start });
            });
            
            if (latency !== null) latencies.push(latency);
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        if (latencies.length > 0) {
            performanceResults.broadcastChannelLatency = Math.round(latencies.reduce((a, b) => a + b) / latencies.length);
            console.log(`    📡 Average BroadcastChannel latency: ${performanceResults.broadcastChannelLatency}ms`);
        }
    }
    
    // Calculate overall reliability
    const successfulTests = Object.values(results.reliability).filter(Boolean).length;
    const totalTests = Object.keys(results.reliability).length;
    performanceResults.overallReliability = totalTests > 0 ? Math.round((successfulTests / totalTests) * 100) : 0;
    
    results.performance = performanceResults;
    
    // Final Report
    console.log('\n📋 FINAL CROSS-TAB AUTHENTICATION TEST REPORT');
    console.log('==============================================');
    
    console.log('\n🔧 Browser Support:');
    Object.entries(results.browserSupport).forEach(([key, value]) => {
        if (key !== 'userAgent') {
            console.log(`  ${value ? '✅' : '❌'} ${key}: ${value ? 'Supported' : 'Not supported'}`);
        }
    });
    
    if (results.syncTiming.login) {
        console.log(`\n⏱️  Synchronization Timing:`);
        console.log(`  Login sync: ${results.syncTiming.login}ms`);
        if (results.syncTiming.logout) console.log(`  Logout sync: ${results.syncTiming.logout}ms`);
    }
    
    if (Object.keys(results.reliability).length > 0) {
        console.log(`\n🎯 Reliability:`);
        Object.entries(results.reliability).forEach(([key, value]) => {
            console.log(`  ${key}: ${value ? '✅ Working' : '❌ Failed'}`);
        });
        console.log(`  Overall: ${performanceResults.overallReliability}%`);
    }
    
    if (results.errors.length > 0) {
        console.log(`\n❌ Errors encountered:`);
        results.errors.forEach(error => console.log(`  • ${error}`));
    }
    
    // Recommendations
    console.log('\n💡 Recommendations:');
    
    if (!results.browserSupport.broadcastChannel) {
        console.log('  • Browser lacks BroadcastChannel support - localStorage fallback should be used');
    }
    
    if (results.syncTiming.login && results.syncTiming.login > 3000) {
        console.log('  • Login synchronization is slow (>3s) - consider optimization');
    }
    
    if (results.syncTiming.logout && results.syncTiming.logout > 2000) {
        console.log('  • Logout synchronization is slow (>2s) - consider optimization');
    }
    
    if (performanceResults.overallReliability < 90) {
        console.log('  • Synchronization reliability is below 90% - investigate failed tests');
    }
    
    if (results.errors.length === 0 && performanceResults.overallReliability >= 90) {
        console.log('  ✅ All tests passed! Cross-tab authentication sync is working well.');
    }
    
    // Store results for export
    window.crossTabTestResults = results;
    console.log('\n📁 Full results stored in window.crossTabTestResults');
    
    return results;
}

// Usage instructions
console.log(`
🧪 Cross-Tab Authentication Test Script Loaded!

Usage:
1. Open multiple tabs with different pages
2. Run: await runCrossTabAuthTest()
3. Follow the interactive prompts
4. Results will be logged and stored in window.crossTabTestResults

Quick test (automated only):
await runCrossTabAuthTest()
`);

// Auto-export function
window.exportCrossTabResults = function() {
    if (window.crossTabTestResults) {
        const blob = new Blob([JSON.stringify(window.crossTabTestResults, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cross-tab-auth-test-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        console.log('✅ Test results exported successfully');
    } else {
        console.log('❌ No test results to export. Run the test first.');
    }
};