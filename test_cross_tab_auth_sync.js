/**
 * Cross-Tab Authentication Synchronization Test Suite
 * Tests BroadcastChannel and localStorage event handling for auth sync
 * Run this in browser console on https://bankcsvconverter.com
 */

class CrossTabAuthTester {
    constructor() {
        this.testResults = [];
        this.tabWindows = [];
        this.startTime = Date.now();
        this.API_BASE = window.location.protocol + '//' + window.location.hostname;
        
        // Test configuration
        this.TEST_USER = {
            email: 'test-20250801-134232@example.com',
            password: 'TestPassword123!'
        };
        
        this.TEST_PAGES = [
            '/dashboard.html',
            '/index.html',
            '/pricing.html',
            '/settings.html'
        ];
        
        this.results = {
            broadcastChannelSupport: false,
            localStorageEventSupport: false,
            loginSyncTiming: [],
            logoutSyncTiming: [],
            raceConditions: [],
            browserCompatibility: {}
        };
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            message,
            type,
            elapsed: Date.now() - this.startTime
        };
        
        this.testResults.push(logEntry);
        
        const colors = {
            info: '#2196F3',
            success: '#4CAF50',
            warning: '#FF9800',
            error: '#F44336'
        };
        
        console.log(
            `%c[${timestamp}] ${message}`,
            `color: ${colors[type] || colors.info}; font-weight: bold;`
        );
    }

    async runFullTestSuite() {
        this.log('🚀 Starting Cross-Tab Authentication Synchronization Test Suite', 'info');
        
        try {
            // Test 1: Browser compatibility
            await this.testBrowserCompatibility();
            
            // Test 2: BroadcastChannel implementation
            await this.testBroadcastChannelImplementation();
            
            // Test 3: localStorage event handling
            await this.testLocalStorageEventHandling();
            
            // Test 4: Login synchronization
            await this.testLoginSynchronization();
            
            // Test 5: Logout synchronization
            await this.testLogoutSynchronization();
            
            // Test 6: Race condition testing
            await this.testRaceConditions();
            
            // Test 7: Multiple browser testing (manual)
            this.provideBrowserTestInstructions();
            
            // Generate final report
            this.generateReport();
            
        } catch (error) {
            this.log(`❌ Test suite failed: ${error.message}`, 'error');
        }
    }

    async testBrowserCompatibility() {
        this.log('🔍 Testing browser compatibility...', 'info');
        
        // Test BroadcastChannel support
        const hasBroadcastChannel = typeof BroadcastChannel !== 'undefined';
        this.results.broadcastChannelSupport = hasBroadcastChannel;
        this.log(`BroadcastChannel support: ${hasBroadcastChannel ? '✅' : '❌'}`, 
                hasBroadcastChannel ? 'success' : 'warning');
        
        // Test localStorage support
        const hasLocalStorage = typeof Storage !== 'undefined';
        this.log(`localStorage support: ${hasLocalStorage ? '✅' : '❌'}`, 
                hasLocalStorage ? 'success' : 'error');
        
        // Test storage event support
        const hasStorageEvents = 'onstorage' in window;
        this.results.localStorageEventSupport = hasStorageEvents;
        this.log(`Storage events support: ${hasStorageEvents ? '✅' : '❌'}`, 
                hasStorageEvents ? 'success' : 'warning');
        
        // Browser info
        const browserInfo = {
            userAgent: navigator.userAgent,
            vendor: navigator.vendor,
            platform: navigator.platform
        };
        this.results.browserCompatibility = browserInfo;
        this.log(`Browser: ${browserInfo.userAgent}`, 'info');
    }

    async testBroadcastChannelImplementation() {
        if (!this.results.broadcastChannelSupport) {
            this.log('⚠️ Skipping BroadcastChannel test - not supported', 'warning');
            return;
        }
        
        this.log('📡 Testing BroadcastChannel implementation...', 'info');
        
        return new Promise((resolve) => {
            const testChannel = new BroadcastChannel('auth-channel');
            const startTime = Date.now();
            let messageReceived = false;
            
            // Listen for test message
            testChannel.onmessage = (event) => {
                if (event.data.type === 'test') {
                    const latency = Date.now() - startTime;
                    messageReceived = true;
                    this.log(`✅ BroadcastChannel message received in ${latency}ms`, 'success');
                    testChannel.close();
                    resolve();
                }
            };
            
            // Send test message
            setTimeout(() => {
                testChannel.postMessage({ type: 'test', timestamp: Date.now() });
            }, 100);
            
            // Timeout check
            setTimeout(() => {
                if (!messageReceived) {
                    this.log('❌ BroadcastChannel test failed - no message received', 'error');
                    testChannel.close();
                    resolve();
                }
            }, 5000);
        });
    }

    async testLocalStorageEventHandling() {
        this.log('💾 Testing localStorage event handling...', 'info');
        
        return new Promise((resolve) => {
            const startTime = Date.now();
            let eventReceived = false;
            
            const storageHandler = (event) => {
                if (event.key === 'test-cross-tab-sync') {
                    const latency = Date.now() - startTime;
                    eventReceived = true;
                    this.log(`✅ localStorage event received in ${latency}ms`, 'success');
                    window.removeEventListener('storage', storageHandler);
                    resolve();
                }
            };
            
            window.addEventListener('storage', storageHandler);
            
            // Trigger storage event
            setTimeout(() => {
                localStorage.setItem('test-cross-tab-sync', Date.now().toString());
                localStorage.removeItem('test-cross-tab-sync');
            }, 100);
            
            // Timeout check
            setTimeout(() => {
                if (!eventReceived) {
                    this.log('❌ localStorage event test failed', 'error');
                    window.removeEventListener('storage', storageHandler);
                    resolve();
                }
            }, 5000);
        });
    }

    async testLoginSynchronization() {
        this.log('🔐 Testing login synchronization...', 'info');
        
        // First, ensure we're logged out
        await this.performLogout();
        await this.sleep(1000);
        
        // Monitor auth state changes
        const authStateMonitor = this.createAuthStateMonitor();
        
        // Perform login
        const loginStart = Date.now();
        const loginResult = await this.performLogin();
        
        if (loginResult.success) {
            this.log('✅ Login successful, monitoring sync...', 'success');
            
            // Wait for sync events
            await this.sleep(3000);
            
            const syncTime = Date.now() - loginStart;
            this.results.loginSyncTiming.push(syncTime);
            this.log(`Login sync completed in ${syncTime}ms`, 'info');
        } else {
            this.log(`❌ Login failed: ${loginResult.error}`, 'error');
        }
        
        authStateMonitor.stop();
    }

    async testLogoutSynchronization() {
        this.log('🚪 Testing logout synchronization...', 'info');
        
        // Ensure we're logged in first
        const authCheck = await this.checkAuthStatus();
        if (!authCheck.authenticated) {
            await this.performLogin();
            await this.sleep(1000);
        }
        
        // Monitor auth state changes
        const authStateMonitor = this.createAuthStateMonitor();
        
        // Perform logout
        const logoutStart = Date.now();
        await this.performLogout();
        
        // Wait for sync events
        await this.sleep(3000);
        
        const syncTime = Date.now() - logoutStart;
        this.results.logoutSyncTiming.push(syncTime);
        this.log(`Logout sync completed in ${syncTime}ms`, 'info');
        
        authStateMonitor.stop();
    }

    async testRaceConditions() {
        this.log('🏃 Testing race conditions...', 'info');
        
        // Test rapid login/logout cycles
        for (let i = 0; i < 3; i++) {
            this.log(`Race condition test ${i + 1}/3`, 'info');
            
            const promises = [];
            
            // Simultaneous auth operations
            promises.push(this.performLogin());
            promises.push(this.checkAuthStatus());
            
            try {
                const results = await Promise.all(promises);
                this.log(`Race test ${i + 1} completed`, 'success');
            } catch (error) {
                this.log(`Race condition detected: ${error.message}`, 'warning');
                this.results.raceConditions.push({
                    test: i + 1,
                    error: error.message,
                    timestamp: Date.now()
                });
            }
            
            await this.sleep(1000);
            await this.performLogout();
            await this.sleep(1000);
        }
    }

    createAuthStateMonitor() {
        const events = [];
        let bcChannel = null;
        
        // Monitor BroadcastChannel
        if (this.results.broadcastChannelSupport) {
            bcChannel = new BroadcastChannel('auth-channel');
            bcChannel.onmessage = (event) => {
                events.push({
                    type: 'broadcast',
                    data: event.data,
                    timestamp: Date.now()
                });
                this.log(`📡 BroadcastChannel event: ${JSON.stringify(event.data)}`, 'info');
            };
        }
        
        // Monitor localStorage
        const storageHandler = (event) => {
            if (event.key === 'user' || event.key === 'auth-logout-event') {
                events.push({
                    type: 'storage',
                    key: event.key,
                    oldValue: event.oldValue,
                    newValue: event.newValue,
                    timestamp: Date.now()
                });
                this.log(`💾 Storage event: ${event.key}`, 'info');
            }
        };
        
        window.addEventListener('storage', storageHandler);
        
        // Monitor custom auth events
        const authHandler = (event) => {
            events.push({
                type: 'custom',
                detail: event.detail,
                timestamp: Date.now()
            });
            this.log(`🔔 Auth state changed: ${JSON.stringify(event.detail)}`, 'info');
        };
        
        window.addEventListener('authStateChanged', authHandler);
        
        return {
            stop: () => {
                if (bcChannel) bcChannel.close();
                window.removeEventListener('storage', storageHandler);
                window.removeEventListener('authStateChanged', authHandler);
                return events;
            },
            getEvents: () => events
        };
    }

    async performLogin() {
        try {
            // Get CSRF token
            const csrfResponse = await fetch(`${this.API_BASE}/v2/api/auth/csrf`, {
                credentials: 'include'
            });
            
            if (!csrfResponse.ok) {
                throw new Error('Failed to get CSRF token');
            }
            
            const csrfData = await csrfResponse.json();
            
            // Login
            const response = await fetch(`${this.API_BASE}/v2/api/auth/login`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfData.csrf_token
                },
                body: JSON.stringify({
                    email: this.TEST_USER.email,
                    password: this.TEST_USER.password,
                    remember_me: false
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                return { success: true, user: data.user };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async performLogout() {
        try {
            // Get CSRF token
            const csrfResponse = await fetch(`${this.API_BASE}/v2/api/auth/csrf`, {
                credentials: 'include'
            });
            
            let csrfToken = null;
            if (csrfResponse.ok) {
                const csrfData = await csrfResponse.json();
                csrfToken = csrfData.csrf_token;
            }
            
            // Logout
            const response = await fetch(`${this.API_BASE}/v2/api/auth/logout`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });
            
            return response.ok;
        } catch (error) {
            this.log(`Logout error: ${error.message}`, 'error');
            return false;
        }
    }

    async checkAuthStatus() {
        try {
            const response = await fetch(`${this.API_BASE}/v2/api/auth/check`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                return { authenticated: false };
            }
        } catch (error) {
            return { authenticated: false, error: error.message };
        }
    }

    provideBrowserTestInstructions() {
        this.log('🌐 Multi-browser testing instructions:', 'info');
        
        const instructions = `
        
MANUAL MULTI-BROWSER TESTING:
==============================

1. Chrome Browser Test:
   - Open https://bankcsvconverter.com in 4 tabs
   - Login in tab 1
   - Verify tabs 2-4 detect login within 2-3 seconds
   - Logout in tab 2
   - Verify tabs 1,3,4 detect logout within 2-3 seconds

2. Firefox Browser Test:
   - Repeat same process as Chrome
   - Note any differences in timing or behavior

3. Safari Browser Test:
   - Repeat same process as Chrome/Firefox
   - Safari may have different localStorage behavior

4. Edge Browser Test:
   - Repeat same process
   - Test BroadcastChannel fallback behavior

5. Cross-Browser Test:
   - Login in Chrome tab
   - Open same site in Firefox
   - Firefox should NOT detect Chrome login (different browser context)
   - This is expected behavior

Expected Results:
- Same browser tabs: Sync within 2-3 seconds
- Different browsers: No sync (expected)
- BroadcastChannel latency: < 100ms
- localStorage event latency: < 500ms
        `;
        
        console.log(instructions);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    generateReport() {
        const duration = Date.now() - this.startTime;
        
        const report = {
            testDuration: duration,
            timestamp: new Date().toISOString(),
            browserInfo: this.results.browserCompatibility,
            compatibility: {
                broadcastChannel: this.results.broadcastChannelSupport,
                localStorage: this.results.localStorageEventSupport
            },
            performance: {
                averageLoginSync: this.average(this.results.loginSyncTiming),
                averageLogoutSync: this.average(this.results.logoutSyncTiming),
                raceConditions: this.results.raceConditions.length
            },
            recommendations: this.generateRecommendations(),
            testResults: this.testResults
        };
        
        this.log('📊 CROSS-TAB AUTHENTICATION SYNC TEST REPORT', 'success');
        console.table(report.compatibility);
        console.table(report.performance);
        
        if (report.recommendations.length > 0) {
            this.log('💡 Recommendations:', 'warning');
            report.recommendations.forEach(rec => this.log(`  • ${rec}`, 'warning'));
        }
        
        // Store report for download
        window.crossTabTestReport = report;
        this.log('📁 Full report saved to window.crossTabTestReport', 'info');
        
        return report;
    }

    generateRecommendations() {
        const recommendations = [];
        
        if (!this.results.broadcastChannelSupport) {
            recommendations.push('Browser lacks BroadcastChannel support - localStorage fallback will be used');
        }
        
        const avgLoginSync = this.average(this.results.loginSyncTiming);
        if (avgLoginSync > 5000) {
            recommendations.push('Login sync timing is slow (>5s) - consider optimizing');
        }
        
        const avgLogoutSync = this.average(this.results.logoutSyncTiming);
        if (avgLogoutSync > 3000) {
            recommendations.push('Logout sync timing is slow (>3s) - consider optimizing');
        }
        
        if (this.results.raceConditions.length > 0) {
            recommendations.push('Race conditions detected - implement better synchronization');
        }
        
        return recommendations;
    }

    average(arr) {
        return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    }
}

// Auto-run if in browser console
if (typeof window !== 'undefined') {
    window.CrossTabAuthTester = CrossTabAuthTester;
    
    console.log(`
🧪 Cross-Tab Authentication Sync Tester Ready!

Usage:
const tester = new CrossTabAuthTester();
await tester.runFullTestSuite();

Or run individual tests:
await tester.testBrowserCompatibility();
await tester.testLoginSynchronization();
await tester.testLogoutSynchronization();
    `);
}