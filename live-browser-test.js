/**
 * Live Browser Testing Script for BankCSV Converter
 * Tests actual functionality on the live website
 */

class LiveBrowserTester {
    constructor() {
        this.baseUrl = 'https://bankcsvconverter.com';
        this.testResults = {
            timestamp: new Date().toISOString(),
            browser: this.detectBrowser(),
            tests: {},
            errors: [],
            warnings: [],
            summary: {}
        };
    }

    detectBrowser() {
        const ua = navigator.userAgent;
        const browser = {
            userAgent: ua,
            name: 'Unknown',
            version: 'Unknown',
            engine: 'Unknown',
            mobile: /Mobile|Android|iPhone|iPad/i.test(ua)
        };

        if (ua.includes('Chrome') && !ua.includes('Edg')) {
            browser.name = 'Chrome';
            browser.version = ua.match(/Chrome\/(\d+\.?\d*)/)?.[1] || 'Unknown';
            browser.engine = 'Blink';
        } else if (ua.includes('Firefox')) {
            browser.name = 'Firefox';
            browser.version = ua.match(/Firefox\/(\d+\.?\d*)/)?.[1] || 'Unknown';
            browser.engine = 'Gecko';
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browser.name = 'Safari';
            browser.version = ua.match(/Version\/(\d+\.?\d*)/)?.[1] || 'Unknown';
            browser.engine = 'WebKit';
        } else if (ua.includes('Edg')) {
            browser.name = 'Edge';
            browser.version = ua.match(/Edg\/(\d+\.?\d*)/)?.[1] || 'Unknown';
            browser.engine = 'Blink';
        }

        return browser;
    }

    async runAllTests() {
        console.log('🚀 Starting Live Browser Tests for BankCSV Converter');
        console.log(`🌐 Testing: ${this.baseUrl}`);
        console.log(`📱 Browser: ${this.testResults.browser.name} ${this.testResults.browser.version} (${this.testResults.browser.mobile ? 'Mobile' : 'Desktop'})`);
        
        const tests = [
            this.testPageLoad,
            this.testJavaScriptExecution,
            this.testFileUploadInterface,
            this.testAuthentication,
            this.testResponsiveDesign,
            this.testAccessibility,
            this.testSecurity,
            this.testPerformance
        ];

        for (const test of tests) {
            try {
                await test.call(this);
            } catch (error) {
                this.testResults.errors.push({
                    test: test.name,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                console.error(`❌ ${test.name} failed:`, error.message);
            }
        }

        this.generateSummary();
        this.displayResults();
        return this.testResults;
    }

    async testPageLoad() {
        const testName = 'Page Load Test';
        console.log(`📄 Running ${testName}...`);
        
        const startTime = performance.now();
        
        try {
            // Test if main elements are present
            const requiredElements = [
                '#uploadBox',
                '#fileInput',
                '#chooseFilesBtn',
                '.navbar',
                '.hero'
            ];

            const results = {
                elementsFound: 0,
                totalElements: requiredElements.length,
                loadTime: performance.now() - startTime,
                errors: []
            };

            requiredElements.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) {
                    results.elementsFound++;
                } else {
                    results.errors.push(`Element not found: ${selector}`);
                }
            });

            const success = results.elementsFound === results.totalElements;
            
            this.testResults.tests[testName] = {
                passed: success,
                score: Math.round((results.elementsFound / results.totalElements) * 100),
                details: results,
                recommendations: success ? 
                    ['✅ All critical elements loaded successfully'] :
                    ['❌ Some critical elements missing', ...results.errors]
            };

            console.log(`${success ? '✅' : '❌'} ${testName}: ${results.elementsFound}/${results.totalElements} elements found`);
            
        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    async testJavaScriptExecution() {
        const testName = 'JavaScript Execution Test';
        console.log(`🔧 Running ${testName}...`);

        const tests = {
            'ES6 Features': this.testES6Features,
            'DOM Manipulation': this.testDOMManipulation,
            'Event Handling': this.testEventHandling,
            'AJAX/Fetch': this.testFetchAPI,
            'Local Storage': this.testLocalStorage
        };

        const results = {};
        let passedTests = 0;

        for (const [testType, testFunc] of Object.entries(tests)) {
            try {
                const result = await testFunc.call(this);
                results[testType] = result;
                if (result.passed) passedTests++;
            } catch (error) {
                results[testType] = { passed: false, error: error.message };
            }
        }

        const success = passedTests === Object.keys(tests).length;

        this.testResults.tests[testName] = {
            passed: success,
            score: Math.round((passedTests / Object.keys(tests).length) * 100),
            details: results,
            passedTests,
            totalTests: Object.keys(tests).length
        };

        console.log(`${success ? '✅' : '❌'} ${testName}: ${passedTests}/${Object.keys(tests).length} passed`);
    }

    testES6Features() {
        try {
            // Test arrow functions
            const arrow = () => 'test';
            
            // Test template literals
            const template = `test ${arrow()}`;
            
            // Test destructuring
            const [a, b] = [1, 2];
            const {name} = {name: 'test'};
            
            // Test const/let
            const constVar = 'test';
            let letVar = 'test';
            
            return {
                passed: true,
                features: ['Arrow Functions', 'Template Literals', 'Destructuring', 'const/let']
            };
        } catch (error) {
            return {
                passed: false,
                error: error.message
            };
        }
    }

    testDOMManipulation() {
        try {
            // Create and manipulate elements
            const testDiv = document.createElement('div');
            testDiv.id = 'test-element';
            testDiv.innerHTML = '<span>Test</span>';
            testDiv.style.display = 'none';
            
            document.body.appendChild(testDiv);
            
            const found = document.getElementById('test-element');
            const hasChild = found.querySelector('span');
            
            document.body.removeChild(testDiv);
            
            return {
                passed: found && hasChild,
                features: ['createElement', 'appendChild', 'querySelector', 'innerHTML', 'style manipulation']
            };
        } catch (error) {
            return {
                passed: false,
                error: error.message
            };
        }
    }

    testEventHandling() {
        try {
            let eventFired = false;
            
            const testButton = document.createElement('button');
            testButton.addEventListener('click', () => {
                eventFired = true;
            });
            
            // Simulate click
            testButton.click();
            
            return {
                passed: eventFired,
                features: ['addEventListener', 'event simulation', 'event handling']
            };
        } catch (error) {
            return {
                passed: false,
                error: error.message
            };
        }
    }

    async testFetchAPI() {
        try {
            if (typeof fetch !== 'function') {
                return {
                    passed: false,
                    error: 'Fetch API not available'
                };
            }

            // Test basic fetch functionality with a data URL
            const response = await fetch('data:text/plain,test');
            const text = await response.text();
            
            return {
                passed: response.ok && text === 'test',
                features: ['fetch API', 'Response handling', 'text parsing']
            };
        } catch (error) {
            return {
                passed: false,
                error: error.message
            };
        }
    }

    testLocalStorage() {
        try {
            const testKey = 'browserTest';
            const testValue = 'testValue123';
            
            localStorage.setItem(testKey, testValue);
            const retrieved = localStorage.getItem(testKey);
            localStorage.removeItem(testKey);
            
            return {
                passed: retrieved === testValue,
                features: ['setItem', 'getItem', 'removeItem']
            };
        } catch (error) {
            return {
                passed: false,
                error: error.message
            };
        }
    }

    async testFileUploadInterface() {
        const testName = 'File Upload Interface Test';
        console.log(`📁 Running ${testName}...`);

        try {
            const uploadBox = document.getElementById('uploadBox');
            const fileInput = document.getElementById('fileInput');
            const chooseBtn = document.getElementById('chooseFilesBtn');

            const results = {
                uploadBoxPresent: !!uploadBox,
                fileInputPresent: !!fileInput,
                chooseBtnPresent: !!chooseBtn,
                dragDropSupported: false,
                fileAPISupported: typeof File === 'function' && typeof FileReader === 'function',
                formDataSupported: typeof FormData === 'function'
            };

            // Test drag and drop support
            if (uploadBox) {
                results.dragDropSupported = 'ondragstart' in uploadBox && 'ondrop' in uploadBox;
            }

            // Test file input attributes
            if (fileInput) {
                results.acceptsPDFs = fileInput.accept.includes('.pdf');
                results.allowsMultiple = fileInput.hasAttribute('multiple');
            }

            const score = Object.values(results).filter(Boolean).length / Object.keys(results).length * 100;
            const passed = score >= 80;

            this.testResults.tests[testName] = {
                passed,
                score: Math.round(score),
                details: results,
                recommendations: [
                    passed ? '✅ File upload interface is well-implemented' : '❌ File upload interface has issues',
                    results.dragDropSupported ? '✅ Drag & drop supported' : '⚠️ Drag & drop not supported',
                    results.fileAPISupported ? '✅ File API supported' : '❌ File API not supported - uploads may not work'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${Math.round(score)}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    async testAuthentication() {
        const testName = 'Authentication System Test';
        console.log(`🔐 Running ${testName}...`);

        try {
            const results = {
                authScriptLoaded: typeof window.UnifiedAuth !== 'undefined',
                cookiesEnabled: navigator.cookieEnabled,
                localStorageAvailable: typeof localStorage !== 'undefined',
                sessionStorageAvailable: typeof sessionStorage !== 'undefined',
                broadcastChannelSupported: typeof BroadcastChannel !== 'undefined'
            };

            // Test authentication endpoints (basic connectivity)
            try {
                const csrfResponse = await fetch(`${this.baseUrl}/v2/api/auth/csrf`, {
                    method: 'HEAD',
                    mode: 'no-cors'
                });
                results.authEndpointsReachable = true;
            } catch (error) {
                results.authEndpointsReachable = false;
                results.authEndpointError = error.message;
            }

            const score = Object.values(results).filter(v => v === true).length / 
                         Object.keys(results).filter(k => !k.includes('Error')).length * 100;
            const passed = score >= 75;

            this.testResults.tests[testName] = {
                passed,
                score: Math.round(score),
                details: results,
                recommendations: [
                    results.authScriptLoaded ? '✅ Auth system loaded' : '❌ Auth system not loaded',
                    results.cookiesEnabled ? '✅ Cookies enabled' : '❌ Cookies disabled - auth may not work',
                    results.broadcastChannelSupported ? '✅ Cross-tab sync supported' : '⚠️ Cross-tab sync will use fallback'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${Math.round(score)}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    async testResponsiveDesign() {
        const testName = 'Responsive Design Test';
        console.log(`📱 Running ${testName}...`);

        try {
            const originalWidth = window.innerWidth;
            const results = {
                supportsMediaQueries: typeof window.matchMedia === 'function',
                mobileMenuPresent: !!document.getElementById('mobileMenu'),
                mobileMenuTogglePresent: !!document.getElementById('mobileMenuToggle'),
                hasViewportMeta: !!document.querySelector('meta[name="viewport"]'),
                breakpoints: {}
            };

            // Test different breakpoints
            const breakpoints = [
                { name: 'mobile', query: '(max-width: 768px)' },
                { name: 'tablet', query: '(min-width: 769px) and (max-width: 1024px)' },
                { name: 'desktop', query: '(min-width: 1025px)' }
            ];

            if (results.supportsMediaQueries) {
                breakpoints.forEach(bp => {
                    const mediaQuery = window.matchMedia(bp.query);
                    results.breakpoints[bp.name] = {
                        matches: mediaQuery.matches,
                        query: bp.query
                    };
                });
            }

            // Check for responsive classes
            const responsiveElements = document.querySelectorAll('[class*="mobile"], [class*="tablet"], [class*="desktop"], [class*="responsive"]');
            results.hasResponsiveClasses = responsiveElements.length > 0;

            const score = (
                (results.supportsMediaQueries ? 25 : 0) +
                (results.mobileMenuPresent ? 25 : 0) +
                (results.hasViewportMeta ? 25 : 0) +
                (results.hasResponsiveClasses ? 25 : 0)
            );
            const passed = score >= 75;

            this.testResults.tests[testName] = {
                passed,
                score,
                details: results,
                recommendations: [
                    results.hasViewportMeta ? '✅ Viewport meta tag present' : '❌ Missing viewport meta tag',
                    results.supportsMediaQueries ? '✅ Media queries supported' : '❌ Media queries not supported',
                    results.mobileMenuPresent ? '✅ Mobile navigation available' : '⚠️ No mobile navigation detected'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${score}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    async testAccessibility() {
        const testName = 'Accessibility Test';
        console.log(`♿ Running ${testName}...`);

        try {
            const results = {
                hasLangAttribute: document.documentElement.hasAttribute('lang'),
                hasTitle: !!document.title && document.title.trim().length > 0,
                hasMetaDescription: !!document.querySelector('meta[name="description"]'),
                hasSkipLinks: !!document.querySelector('[href="#main"], [href="#content"]'),
                imagesHaveAlt: true,
                formsHaveLabels: true,
                headingStructure: this.checkHeadingStructure(),
                colorContrast: 'Not tested (requires visual analysis)',
                keyboardNavigation: 'Not tested (requires manual testing)'
            };

            // Check images for alt attributes
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                if (!img.hasAttribute('alt')) {
                    results.imagesHaveAlt = false;
                }
            });

            // Check form inputs for labels
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.type !== 'hidden' && !input.hasAttribute('aria-label') && 
                    !document.querySelector(`label[for="${input.id}"]`)) {
                    results.formsHaveLabels = false;
                }
            });

            const accessibilityScore = (
                (results.hasLangAttribute ? 15 : 0) +
                (results.hasTitle ? 15 : 0) +
                (results.hasMetaDescription ? 10 : 0) +
                (results.imagesHaveAlt ? 25 : 0) +
                (results.formsHaveLabels ? 25 : 0) +
                (results.headingStructure.proper ? 10 : 0)
            );
            const passed = accessibilityScore >= 70;

            this.testResults.tests[testName] = {
                passed,
                score: accessibilityScore,
                details: results,
                recommendations: [
                    results.hasLangAttribute ? '✅ Language attribute set' : '❌ Missing language attribute',
                    results.imagesHaveAlt ? '✅ Images have alt text' : '❌ Some images missing alt text',
                    results.formsHaveLabels ? '✅ Forms properly labeled' : '❌ Some form inputs missing labels',
                    '⚠️ Manual testing needed for keyboard navigation and color contrast'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${accessibilityScore}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    checkHeadingStructure() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const structure = [];
        let hasH1 = false;
        let proper = true;
        let previousLevel = 0;

        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            if (level === 1) hasH1 = true;
            
            if (level > previousLevel + 1) {
                proper = false; // Skipped heading level
            }
            
            structure.push({
                tag: heading.tagName,
                level,
                text: heading.textContent.trim().substring(0, 50)
            });
            
            previousLevel = level;
        });

        return {
            proper: proper && hasH1,
            hasH1,
            structure,
            issues: proper ? [] : ['Heading levels are not properly nested']
        };
    }

    async testSecurity() {
        const testName = 'Security Test';
        console.log(`🔒 Running ${testName}...`);

        try {
            const results = {
                httpsUsed: location.protocol === 'https:',
                mixedContentWarnings: false, // Would need more complex detection
                cspHeaderPresent: 'Not detectable from client-side',
                secureFormSubmission: true,
                cookieSecurityFlags: 'Not detectable from client-side'
            };

            // Check for secure form submission
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                if (form.action && form.action.startsWith('http:')) {
                    results.secureFormSubmission = false;
                }
            });

            // Check for external scripts over HTTP
            const scripts = document.querySelectorAll('script[src]');
            scripts.forEach(script => {
                if (script.src.startsWith('http:')) {
                    results.mixedContentWarnings = true;
                }
            });

            const securityScore = (
                (results.httpsUsed ? 40 : 0) +
                (results.secureFormSubmission ? 30 : 0) +
                (!results.mixedContentWarnings ? 30 : 0)
            );
            const passed = securityScore >= 80;

            this.testResults.tests[testName] = {
                passed,
                score: securityScore,
                details: results,
                recommendations: [
                    results.httpsUsed ? '✅ HTTPS enabled' : '❌ Not using HTTPS',
                    results.secureFormSubmission ? '✅ Forms submit securely' : '❌ Insecure form submission detected',
                    !results.mixedContentWarnings ? '✅ No mixed content detected' : '❌ Mixed content warnings possible'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${securityScore}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    async testPerformance() {
        const testName = 'Performance Test';
        console.log(`⚡ Running ${testName}...`);

        try {
            const results = {
                domContentLoaded: false,
                resourcesLoaded: false,
                jsErrors: this.testResults.errors.filter(e => e.test === 'JavaScript Execution Test').length,
                imageOptimization: this.checkImageOptimization(),
                criticalResourcesCount: this.countCriticalResources()
            };

            // Check if DOM and resources are loaded
            results.domContentLoaded = document.readyState !== 'loading';
            results.resourcesLoaded = document.readyState === 'complete';

            // Basic performance metrics if available
            if (performance.timing) {
                const timing = performance.timing;
                results.loadTime = timing.loadEventEnd - timing.navigationStart;
                results.domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
            }

            const perfScore = (
                (results.domContentLoaded ? 25 : 0) +
                (results.resourcesLoaded ? 25 : 0) +
                (results.jsErrors === 0 ? 25 : 0) +
                (results.imageOptimization.optimized >= results.imageOptimization.total * 0.8 ? 25 : 0)
            );
            const passed = perfScore >= 70;

            this.testResults.tests[testName] = {
                passed,
                score: perfScore,
                details: results,
                recommendations: [
                    results.domContentLoaded ? '✅ DOM loaded successfully' : '❌ DOM loading issues',
                    results.jsErrors === 0 ? '✅ No JavaScript errors' : `❌ ${results.jsErrors} JavaScript errors detected`,
                    results.imageOptimization.total > 0 ? 
                        `📊 ${results.imageOptimization.optimized}/${results.imageOptimization.total} images optimized` : 
                        '📊 No images to optimize'
                ]
            };

            console.log(`${passed ? '✅' : '❌'} ${testName}: Score ${perfScore}%`);

        } catch (error) {
            this.testResults.tests[testName] = {
                passed: false,
                error: error.message
            };
            throw error;
        }
    }

    checkImageOptimization() {
        const images = document.querySelectorAll('img');
        let optimized = 0;
        let total = images.length;

        images.forEach(img => {
            // Basic checks for optimization
            if (img.loading === 'lazy' || img.hasAttribute('loading')) optimized++;
            else if (img.src.includes('.webp') || img.src.includes('.avif')) optimized++;
            else if (img.hasAttribute('sizes') || img.hasAttribute('srcset')) optimized++;
        });

        return { optimized, total };
    }

    countCriticalResources() {
        const scripts = document.querySelectorAll('script[src]');
        const stylesheets = document.querySelectorAll('link[rel="stylesheet"]');
        return {
            scripts: scripts.length,
            stylesheets: stylesheets.length,
            total: scripts.length + stylesheets.length
        };
    }

    generateSummary() {
        const tests = Object.values(this.testResults.tests);
        const passedTests = tests.filter(t => t.passed).length;
        const totalTests = tests.length;
        const averageScore = tests.reduce((sum, test) => sum + (test.score || 0), 0) / totalTests;

        this.testResults.summary = {
            passedTests,
            totalTests,
            passRate: Math.round((passedTests / totalTests) * 100),
            averageScore: Math.round(averageScore),
            grade: this.calculateGrade(averageScore),
            recommendations: this.generateGlobalRecommendations()
        };
    }

    calculateGrade(score) {
        if (score >= 95) return 'A+';
        if (score >= 90) return 'A';
        if (score >= 85) return 'B+';
        if (score >= 80) return 'B';
        if (score >= 75) return 'C+';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    generateGlobalRecommendations() {
        const recommendations = [];
        const browser = this.testResults.browser;

        // Browser-specific recommendations
        if (browser.name === 'Safari') {
            recommendations.push('🍎 Safari detected - test file uploads carefully due to security restrictions');
        }
        
        if (browser.mobile) {
            recommendations.push('📱 Mobile browser detected - ensure touch interactions work properly');
        }

        if (parseFloat(browser.version) < 90 && ['Chrome', 'Edge'].includes(browser.name)) {
            recommendations.push('⚠️ Older Chromium version - consider polyfills for newer features');
        }

        // Global recommendations based on test results
        const failedTests = Object.entries(this.testResults.tests)
            .filter(([name, test]) => !test.passed)
            .map(([name]) => name);

        if (failedTests.length > 0) {
            recommendations.push(`❌ Failed tests: ${failedTests.join(', ')}`);
        }

        if (this.testResults.errors.length > 0) {
            recommendations.push(`🐛 ${this.testResults.errors.length} errors encountered during testing`);
        }

        return recommendations;
    }

    displayResults() {
        console.log('\n📊 TEST RESULTS SUMMARY');
        console.log('═'.repeat(50));
        
        const summary = this.testResults.summary;
        console.log(`🎯 Overall Grade: ${summary.grade} (${summary.averageScore}%)`);
        console.log(`✅ Tests Passed: ${summary.passedTests}/${summary.totalTests} (${summary.passRate}%)`);
        console.log(`🌐 Browser: ${this.testResults.browser.name} ${this.testResults.browser.version}`);
        
        if (this.testResults.errors.length > 0) {
            console.log(`🐛 Errors: ${this.testResults.errors.length}`);
        }

        console.log('\n📋 Test Details:');
        Object.entries(this.testResults.tests).forEach(([testName, result]) => {
            const status = result.passed ? '✅' : '❌';
            const score = result.score ? ` (${result.score}%)` : '';
            console.log(`   ${status} ${testName}${score}`);
        });

        if (summary.recommendations.length > 0) {
            console.log('\n💡 Recommendations:');
            summary.recommendations.forEach(rec => {
                console.log(`   ${rec}`);
            });
        }

        console.log('\n✅ Live browser testing complete!');
    }

    downloadReport() {
        const blob = new Blob([JSON.stringify(this.testResults, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `live-browser-test-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Make it available globally
window.LiveBrowserTester = LiveBrowserTester;

// Auto-run if not in iframe (to avoid running in test environments)
if (window.self === window.top) {
    document.addEventListener('DOMContentLoaded', async () => {
        const tester = new LiveBrowserTester();
        await tester.runAllTests();
        
        // Add download button to page
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = '📊 Download Test Report';
        downloadBtn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        `;
        downloadBtn.onclick = () => tester.downloadReport();
        document.body.appendChild(downloadBtn);
    });
}