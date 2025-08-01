/**
 * Comprehensive Stripe Checkout Debug Test Script
 * Run this in the browser console on the pricing page to test and debug Stripe integration
 * 
 * Usage:
 * 1. Navigate to /pricing.html
 * 2. Open browser console (F12)
 * 3. Copy and paste this entire script
 * 4. Press Enter to run
 * 5. Follow the test results and error messages
 */

(function() {
    'use strict';
    
    console.log('🔧 STRIPE CHECKOUT DEBUG TEST STARTING...');
    console.log('==========================================');
    
    // Test Configuration
    const TEST_CONFIG = {
        logNetworkRequests: true,
        simulateButtonClicks: true,
        testPlan: 'professional', // starter, professional, business
        testBillingPeriod: 'monthly', // monthly, yearly
        maxWaitTime: 10000 // 10 seconds
    };
    
    // Network monitoring
    const networkLogs = [];
    
    // Override fetch to monitor network requests
    if (TEST_CONFIG.logNetworkRequests) {
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const [url, options = {}] = args;
            const startTime = Date.now();
            
            console.log('🌐 NETWORK REQUEST:', {
                url,
                method: options.method || 'GET',
                headers: options.headers,
                body: options.body,
                timestamp: new Date().toISOString()
            });
            
            return originalFetch.apply(this, args)
                .then(response => {
                    const endTime = Date.now();
                    const logEntry = {
                        url,
                        method: options.method || 'GET',
                        status: response.status,
                        statusText: response.statusText,
                        duration: endTime - startTime,
                        headers: Object.fromEntries(response.headers.entries()),
                        timestamp: new Date().toISOString()
                    };
                    
                    networkLogs.push(logEntry);
                    
                    console.log('✅ NETWORK RESPONSE:', logEntry);
                    
                    return response;
                })
                .catch(error => {
                    const endTime = Date.now();
                    const logEntry = {
                        url,
                        method: options.method || 'GET',
                        error: error.message,
                        duration: endTime - startTime,
                        timestamp: new Date().toISOString()
                    };
                    
                    networkLogs.push(logEntry);
                    
                    console.error('❌ NETWORK ERROR:', logEntry);
                    
                    throw error;
                });
        };
    }
    
    // Test Results Object
    const testResults = {
        unifiedAuthExists: false,
        unifiedAuthReady: false,
        userAuthenticated: false,
        csrfToken: null,
        apiBase: null,
        pricingButtons: 0,
        toggleWorks: false,
        networkRequests: [],
        errors: []
    };
    
    // Helper function to wait for condition
    function waitFor(condition, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            function check() {
                if (condition()) {
                    resolve(true);
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error('Timeout waiting for condition'));
                } else {
                    setTimeout(check, 100);
                }
            }
            
            check();
        });
    }
    
    // Test 1: Check if UnifiedAuth exists and is ready
    async function testUnifiedAuth() {
        console.log('\n📋 TEST 1: UnifiedAuth System Check');
        console.log('==================================');
        
        try {
            // Check if UnifiedAuth exists
            testResults.unifiedAuthExists = typeof window.UnifiedAuth !== 'undefined';
            console.log('UnifiedAuth exists:', testResults.unifiedAuthExists);
            
            if (!testResults.unifiedAuthExists) {
                testResults.errors.push('UnifiedAuth not found on window object');
                return;
            }
            
            // Wait for initialization
            await waitFor(() => window.UnifiedAuth.initialized, 10000);
            testResults.unifiedAuthReady = window.UnifiedAuth.initialized;
            console.log('UnifiedAuth ready:', testResults.unifiedAuthReady);
            
            // Check authentication status
            testResults.userAuthenticated = window.UnifiedAuth.isAuthenticated();
            console.log('User authenticated:', testResults.userAuthenticated);
            
            // Check CSRF token
            testResults.csrfToken = window.UnifiedAuth.csrfToken;
            console.log('CSRF token:', testResults.csrfToken ? '✅ Available' : '❌ Missing');
            
            // Check API base
            const hostname = window.location.hostname;
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                testResults.apiBase = 'http://localhost:5000';
            } else {
                testResults.apiBase = `${window.location.protocol}//${hostname}`;
            }
            console.log('API Base URL:', testResults.apiBase);
            
            // Show user info if authenticated
            if (testResults.userAuthenticated) {
                const user = window.UnifiedAuth.getUser();
                console.log('User info:', user);
            }
            
        } catch (error) {
            console.error('❌ UnifiedAuth test failed:', error);
            testResults.errors.push(`UnifiedAuth test failed: ${error.message}`);
        }
    }
    
    // Test 2: Test makeAuthenticatedRequest function
    async function testMakeAuthenticatedRequest() {
        console.log('\n📋 TEST 2: makeAuthenticatedRequest Function');
        console.log('============================================');
        
        if (!testResults.unifiedAuthReady) {
            console.log('⏭️ Skipping - UnifiedAuth not ready');
            return;
        }
        
        try {
            // Test auth check endpoint
            console.log('Testing auth check endpoint...');
            const authResponse = await window.UnifiedAuth.makeAuthenticatedRequest('/api/auth/check');
            console.log('Auth check response status:', authResponse.status);
            
            if (authResponse.ok) {
                const authData = await authResponse.json();
                console.log('Auth check data:', authData);
            } else {
                console.log('Auth check failed:', authResponse.statusText);
            }
            
            // Test Stripe subscription status if authenticated
            if (testResults.userAuthenticated) {
                console.log('Testing Stripe subscription status...');
                const stripeResponse = await window.UnifiedAuth.makeAuthenticatedRequest('/api/stripe/subscription-status');
                console.log('Stripe status response:', stripeResponse.status);
                
                if (stripeResponse.ok) {
                    const stripeData = await stripeResponse.json();
                    console.log('Stripe subscription data:', stripeData);
                } else {
                    const errorText = await stripeResponse.text();
                    console.log('Stripe status error:', errorText);
                    testResults.errors.push(`Stripe status error: ${stripeResponse.status} - ${errorText}`);
                }
            }
            
        } catch (error) {
            console.error('❌ makeAuthenticatedRequest test failed:', error);
            testResults.errors.push(`makeAuthenticatedRequest test failed: ${error.message}`);
        }
    }
    
    // Test 3: Check pricing page elements
    async function testPricingPageElements() {
        console.log('\n📋 TEST 3: Pricing Page Elements');
        console.log('================================');
        
        try {
            // Check pricing buttons
            const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
            testResults.pricingButtons = pricingButtons.length;
            console.log('Pricing buttons found:', testResults.pricingButtons);
            
            pricingButtons.forEach((button, index) => {
                const plans = ['starter', 'professional', 'business'];
                const plan = plans[index];
                console.log(`Button ${index + 1} (${plan}):`, {
                    text: button.textContent,
                    href: button.href,
                    disabled: button.disabled,
                    classes: button.className
                });
            });
            
            // Check pricing toggle
            const toggleElement = document.getElementById('pricingToggle');
            if (toggleElement) {
                console.log('Pricing toggle found:', {
                    classes: toggleElement.className,
                    isYearly: toggleElement.classList.contains('active')
                });
                
                // Test toggle functionality
                console.log('Testing toggle click...');
                const beforeState = toggleElement.classList.contains('active');
                toggleElement.click();
                
                setTimeout(() => {
                    const afterState = toggleElement.classList.contains('active');
                    testResults.toggleWorks = beforeState !== afterState;
                    console.log('Toggle works:', testResults.toggleWorks);
                    
                    // Reset to original state
                    if (beforeState !== afterState) {
                        toggleElement.click();
                    }
                }, 100);
            } else {
                console.log('❌ Pricing toggle not found');
                testResults.errors.push('Pricing toggle element not found');
            }
            
        } catch (error) {
            console.error('❌ Pricing page elements test failed:', error);
            testResults.errors.push(`Pricing page elements test failed: ${error.message}`);
        }
    }
    
    // Test 4: Simulate buy button click
    async function testBuyButtonClick() {
        console.log('\n📋 TEST 4: Buy Button Click Simulation');
        console.log('======================================');
        
        if (!TEST_CONFIG.simulateButtonClicks) {
            console.log('⏭️ Skipping - Button click simulation disabled');
            return;
        }
        
        try {
            const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
            const plans = ['starter', 'professional', 'business'];
            const testPlanIndex = plans.indexOf(TEST_CONFIG.testPlan);
            
            if (testPlanIndex === -1 || !pricingButtons[testPlanIndex]) {
                console.log('❌ Test plan button not found');
                testResults.errors.push(`Test plan button not found: ${TEST_CONFIG.testPlan}`);
                return;
            }
            
            const testButton = pricingButtons[testPlanIndex];
            console.log(`Testing ${TEST_CONFIG.testPlan} plan button...`);
            
            // Set billing period
            const toggleElement = document.getElementById('pricingToggle');
            if (toggleElement) {
                const isCurrentlyYearly = toggleElement.classList.contains('active');
                const shouldBeYearly = TEST_CONFIG.testBillingPeriod === 'yearly';
                
                if (isCurrentlyYearly !== shouldBeYearly) {
                    console.log(`Setting billing period to ${TEST_CONFIG.testBillingPeriod}...`);
                    toggleElement.click();
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
            }
            
            // Record network requests before click
            const requestCountBefore = networkLogs.length;
            
            // Simulate click
            console.log('Simulating button click...');
            testButton.click();
            
            // Wait for potential network requests
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check for new network requests
            const newRequests = networkLogs.slice(requestCountBefore);
            console.log('Network requests after click:', newRequests.length);
            
            newRequests.forEach((request, index) => {
                console.log(`Request ${index + 1}:`, request);
            });
            
            testResults.networkRequests = newRequests;
            
        } catch (error) {
            console.error('❌ Buy button click test failed:', error);
            testResults.errors.push(`Buy button click test failed: ${error.message}`);
        }
    }
    
    // Test 5: Test Stripe API endpoints directly
    async function testStripeEndpoints() {
        console.log('\n📋 TEST 5: Direct Stripe API Testing');
        console.log('====================================');
        
        if (!testResults.userAuthenticated) {
            console.log('⏭️ Skipping - User not authenticated');
            return;
        }
        
        try {
            // Test create checkout session
            console.log('Testing create checkout session...');
            const payload = {
                plan: TEST_CONFIG.testPlan,
                billing_period: TEST_CONFIG.testBillingPeriod
            };
            
            console.log('Request payload:', payload);
            
            const checkoutResponse = await window.UnifiedAuth.makeAuthenticatedRequest(
                '/api/stripe/create-checkout-session',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                }
            );
            
            console.log('Checkout session response status:', checkoutResponse.status);
            console.log('Checkout session response headers:', Object.fromEntries(checkoutResponse.headers.entries()));
            
            if (checkoutResponse.ok) {
                const checkoutData = await checkoutResponse.json();
                console.log('✅ Checkout session created successfully:', checkoutData);
                
                // Validate response structure
                if (checkoutData.checkout_url) {
                    console.log('✅ Checkout URL received:', checkoutData.checkout_url);
                } else {
                    console.log('❌ No checkout_url in response');
                    testResults.errors.push('No checkout_url in response');
                }
            } else {
                const errorText = await checkoutResponse.text();
                console.log('❌ Checkout session failed:', errorText);
                testResults.errors.push(`Checkout session failed: ${checkoutResponse.status} - ${errorText}`);
                
                try {
                    const errorJson = JSON.parse(errorText);
                    console.log('Error details:', errorJson);
                } catch (e) {
                    console.log('Could not parse error as JSON');
                }
            }
            
        } catch (error) {
            console.error('❌ Stripe endpoints test failed:', error);
            testResults.errors.push(`Stripe endpoints test failed: ${error.message}`);
        }
    }
    
    // Test 6: Check environment and configuration
    async function testEnvironmentConfig() {
        console.log('\n📋 TEST 6: Environment & Configuration');
        console.log('=====================================');
        
        try {
            // Check current URL
            console.log('Current URL:', window.location.href);
            console.log('Current hostname:', window.location.hostname);
            console.log('Current protocol:', window.location.protocol);
            
            // Check if on pricing page
            const isPricingPage = window.location.pathname.includes('pricing');
            console.log('On pricing page:', isPricingPage);
            
            // Check for required scripts
            const scripts = Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
            console.log('Loaded scripts:', scripts);
            
            const requiredScripts = [
                'auth-unified.js',
                'stripe-integration.js'
            ];
            
            requiredScripts.forEach(script => {
                const found = scripts.some(s => s.includes(script));
                console.log(`${script} loaded:`, found ? '✅' : '❌');
                if (!found) {
                    testResults.errors.push(`Required script not loaded: ${script}`);
                }
            });
            
            // Check console errors
            console.log('Checking for console errors...');
            // Note: Can't easily capture previous console errors, but future ones will be visible
            
        } catch (error) {
            console.error('❌ Environment config test failed:', error);
            testResults.errors.push(`Environment config test failed: ${error.message}`);
        }
    }
    
    // Generate summary report
    function generateSummaryReport() {
        console.log('\n📊 COMPREHENSIVE TEST SUMMARY');
        console.log('=============================');
        
        console.log('Test Results:', testResults);
        
        // Count passed/failed tests
        const passedTests = [
            testResults.unifiedAuthExists,
            testResults.unifiedAuthReady,
            testResults.pricingButtons > 0,
            testResults.errors.length === 0
        ].filter(Boolean).length;
        
        const totalTests = 6;
        
        console.log(`Tests Status: ${passedTests}/${totalTests} areas checked`);
        
        if (testResults.errors.length > 0) {
            console.log('\n❌ ERRORS FOUND:');
            testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        // Specific recommendations
        console.log('\n💡 RECOMMENDATIONS:');
        
        if (!testResults.unifiedAuthExists) {
            console.log('• UnifiedAuth not loaded - check if auth-unified.js is included');
        }
        
        if (!testResults.unifiedAuthReady) {
            console.log('• UnifiedAuth not initialized - check for initialization errors');
        }
        
        if (!testResults.userAuthenticated) {
            console.log('• User not authenticated - login required for Stripe checkout');
        }
        
        if (!testResults.csrfToken) {
            console.log('• CSRF token missing - may cause authenticated requests to fail');
        }
        
        if (testResults.pricingButtons === 0) {
            console.log('• No pricing buttons found - check DOM structure');
        }
        
        if (testResults.networkRequests.length === 0 && TEST_CONFIG.simulateButtonClicks) {
            console.log('• No network requests made after button click - check event handlers');
        }
        
        // Show network logs summary
        if (networkLogs.length > 0) {
            console.log('\n🌐 NETWORK REQUESTS SUMMARY:');
            networkLogs.forEach((req, index) => {
                console.log(`${index + 1}. ${req.method} ${req.url} → ${req.status || 'ERROR'}`);
            });
        }
        
        console.log('\n🔧 Next Steps:');
        console.log('1. Fix any errors shown above');
        console.log('2. Check browser network tab for additional details');
        console.log('3. Verify backend API is running and accessible');
        console.log('4. Check Stripe configuration in backend');
        console.log('5. Ensure user has valid authentication cookies');
        
        // Return results for programmatic access
        return {
            ...testResults,
            networkLogs,
            summary: {
                totalTests,
                passedTests,
                hasErrors: testResults.errors.length > 0
            }
        };
    }
    
    // Run all tests
    async function runAllTests() {
        try {
            await testUnifiedAuth();
            await testMakeAuthenticatedRequest();
            await testPricingPageElements();
            await testBuyButtonClick();
            await testStripeEndpoints();
            await testEnvironmentConfig();
            
            // Generate final report
            return generateSummaryReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error);
            testResults.errors.push(`Test suite failed: ${error.message}`);
            return generateSummaryReport();
        }
    }
    
    // Make test results available globally
    window.StripeDebugTest = {
        run: runAllTests,
        results: testResults,
        networkLogs: networkLogs,
        config: TEST_CONFIG
    };
    
    // Auto-run tests
    console.log('🚀 Starting automated tests...');
    runAllTests().then(results => {
        console.log('\n✅ All tests completed!');
        console.log('Results available at: window.StripeDebugTest.results');
        console.log('Network logs available at: window.StripeDebugTest.networkLogs');
        
        // Store results globally for later access
        window.stripeTestResults = results;
    });
    
})();