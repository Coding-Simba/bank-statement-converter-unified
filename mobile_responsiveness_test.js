/**
 * Mobile Responsiveness Test Script for BankCSV Converter
 * Run this in Chrome DevTools console on each page
 */

class MobileResponsivenessTest {
    constructor() {
        this.issues = [];
        this.testResults = {
            viewport: [],
            navigation: [],
            touchTargets: [],
            forms: [],
            images: [],
            typography: []
        };
    }

    // Test different mobile viewport sizes
    testViewportSizes() {
        const viewports = [
            { name: 'iPhone SE', width: 375, height: 667 },
            { name: 'iPhone 12', width: 390, height: 844 },
            { name: 'iPhone 12 Pro Max', width: 428, height: 926 },
            { name: 'Samsung Galaxy S20', width: 360, height: 800 },
            { name: 'iPad Mini', width: 768, height: 1024 },
            { name: 'Generic Mobile', width: 320, height: 568 }
        ];

        console.log('📱 Testing Mobile Viewports...');
        
        viewports.forEach(viewport => {
            // Simulate viewport resize
            console.log(`Testing ${viewport.name} (${viewport.width}x${viewport.height})`);
            
            // Check if content fits
            const body = document.body;
            const scrollWidth = body.scrollWidth;
            const hasHorizontalScroll = scrollWidth > viewport.width;
            
            if (hasHorizontalScroll) {
                this.issues.push(`Horizontal scroll detected on ${viewport.name}`);
            }
            
            this.testResults.viewport.push({
                device: viewport.name,
                width: viewport.width,
                horizontalScroll: hasHorizontalScroll,
                pass: !hasHorizontalScroll
            });
        });
    }

    // Test touch target sizes (minimum 44x44px recommended)
    testTouchTargets() {
        console.log('👆 Testing Touch Targets...');
        
        const interactiveElements = document.querySelectorAll(
            'button, a, input[type="button"], input[type="submit"], .btn, .nav-link'
        );
        
        interactiveElements.forEach((element, index) => {
            const rect = element.getBoundingClientRect();
            const minSize = 44; // Apple's recommended minimum
            
            const isTooSmall = rect.width < minSize || rect.height < minSize;
            const isVisible = rect.width > 0 && rect.height > 0;
            
            if (isVisible && isTooSmall) {
                this.issues.push(
                    `Touch target too small: ${element.tagName} ${element.className} 
                     (${Math.round(rect.width)}x${Math.round(rect.height)}px)`
                );
            }
            
            this.testResults.touchTargets.push({
                element: element.tagName + (element.className ? '.' + element.className : ''),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                pass: !isTooSmall || !isVisible
            });
        });
    }

    // Test mobile navigation
    testMobileNavigation() {
        console.log('🧭 Testing Mobile Navigation...');
        
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle, #mobileMenuToggle');
        const mobileMenu = document.querySelector('.mobile-menu, #mobileMenu');
        const desktopNav = document.querySelector('.desktop-only, .nav-links');
        
        const results = {
            hasMobileToggle: !!mobileMenuToggle,
            hasMobileMenu: !!mobileMenu,
            hasDesktopNav: !!desktopNav
        };
        
        if (!mobileMenuToggle) {
            this.issues.push('No mobile menu toggle found');
        }
        
        if (!mobileMenu) {
            this.issues.push('No mobile menu container found');  
        }
        
        // Test if mobile menu functionality works
        if (mobileMenuToggle && mobileMenu) {
            try {
                mobileMenuToggle.click();
                const isActive = mobileMenu.classList.contains('active') || 
                               mobileMenu.style.display === 'block';
                results.menuFunctional = isActive;
                
                // Close menu
                mobileMenuToggle.click();
            } catch (e) {
                this.issues.push('Mobile menu toggle not functional: ' + e.message);
                results.menuFunctional = false;
            }
        }
        
        this.testResults.navigation.push(results);
    }

    // Test form elements on mobile
    testFormElements() {
        console.log('📝 Testing Form Elements...');
        
        const forms = document.querySelectorAll('form');
        const inputs = document.querySelectorAll('input, textarea, select');
        
        forms.forEach((form, index) => {
            const formRect = form.getBoundingClientRect();
            const isResponsive = formRect.width <= window.innerWidth;
            
            if (!isResponsive) {
                this.issues.push(`Form ${index + 1} exceeds viewport width`);
            }
            
            this.testResults.forms.push({
                formIndex: index + 1,
                responsive: isResponsive,
                width: Math.round(formRect.width)
            });
        });
        
        inputs.forEach((input, index) => {
            const rect = input.getBoundingClientRect();
            const fontSize = window.getComputedStyle(input).fontSize;
            const fontSizeNum = parseFloat(fontSize);
            
            // iOS requires 16px+ font size to prevent zoom
            if (fontSizeNum < 16) {
                this.issues.push(
                    `Input ${index + 1} font size too small (${fontSize}) - may cause zoom on iOS`
                );
            }
        });
    }

    // Test image responsiveness
    testImages() {
        console.log('🖼️ Testing Images...');
        
        const images = document.querySelectorAll('img');
        
        images.forEach((img, index) => {
            const rect = img.getBoundingClientRect();
            const exceedsViewport = rect.width > window.innerWidth;
            const hasMaxWidth = window.getComputedStyle(img).maxWidth !== 'none';
            
            if (exceedsViewport && !hasMaxWidth) {
                this.issues.push(`Image ${index + 1} exceeds viewport and lacks max-width`);
            }
            
            this.testResults.images.push({
                imageIndex: index + 1,
                width: Math.round(rect.width),
                exceedsViewport,
                hasMaxWidth,
                pass: !exceedsViewport || hasMaxWidth
            });
        });
    }

    // Test typography scaling
    testTypography() {
        console.log('📝 Testing Typography...');
        
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const paragraphs = document.querySelectorAll('p');
        
        [...headings, ...paragraphs].forEach((element, index) => {
            const fontSize = window.getComputedStyle(element).fontSize;
            const fontSizeNum = parseFloat(fontSize);
            const tagName = element.tagName.toLowerCase();
            
            // Check minimum readable sizes
            const minSizes = {
                h1: 24, h2: 20, h3: 18, h4: 16, h5: 14, h6: 14, p: 14
            };
            
            const minSize = minSizes[tagName] || 14;
            
            if (fontSizeNum < minSize) {
                this.issues.push(
                    `${tagName.toUpperCase()} font size too small: ${fontSize} (min: ${minSize}px)`
                );
            }
            
            this.testResults.typography.push({
                element: tagName,
                fontSize: fontSizeNum,
                minSize,
                pass: fontSizeNum >= minSize
            });
        });
    }

    // Check for viewport meta tag
    testViewportMeta() {
        console.log('🔍 Testing Viewport Meta Tag...');
        
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        
        if (!viewportMeta) {
            this.issues.push('Missing viewport meta tag');
            return false;
        }
        
        const content = viewportMeta.getAttribute('content');
        const hasWidthDevice = content.includes('width=device-width');
        const hasInitialScale = content.includes('initial-scale=1');
        
        if (!hasWidthDevice) {
            this.issues.push('Viewport meta tag missing width=device-width');
        }
        
        if (!hasInitialScale) {
            this.issues.push('Viewport meta tag missing initial-scale=1');
        }
        
        return hasWidthDevice && hasInitialScale;
    }

    // Run all tests
    runAllTests() {
        console.clear();
        console.log('🚀 Starting Mobile Responsiveness Tests for:', window.location.href);
        console.log('=' .repeat(60));
        
        this.testViewportMeta();
        this.testViewportSizes();
        this.testTouchTargets();
        this.testMobileNavigation();
        this.testFormElements();
        this.testImages();
        this.testTypography();
        
        this.generateReport();
    }

    // Generate comprehensive report
    generateReport() {
        console.log('\n📊 MOBILE RESPONSIVENESS TEST REPORT');
        console.log('=' .repeat(60));
        
        // Summary
        const totalIssues = this.issues.length;
        const status = totalIssues === 0 ? '✅ PASS' : `❌ ${totalIssues} ISSUES FOUND`;
        
        console.log(`%cOverall Status: ${status}`, 
                   totalIssues === 0 ? 'color: green; font-weight: bold' : 'color: red; font-weight: bold');
        
        if (totalIssues > 0) {
            console.log('\n🐛 Issues Found:');
            this.issues.forEach((issue, index) => {
                console.log(`${index + 1}. ${issue}`);
            });
        }
        
        // Detailed results
        console.log('\n📱 Viewport Tests:', this.testResults.viewport);
        console.log('👆 Touch Target Tests:', this.testResults.touchTargets);
        console.log('🧭 Navigation Tests:', this.testResults.navigation);
        console.log('📝 Form Tests:', this.testResults.forms);
        console.log('🖼️ Image Tests:', this.testResults.images);
        console.log('📝 Typography Tests:', this.testResults.typography);
        
        // Recommendations
        if (totalIssues > 0) {
            console.log('\n💡 Recommendations:');
            console.log('1. Fix touch targets < 44x44px');
            console.log('2. Ensure no horizontal scrolling');
            console.log('3. Use font sizes ≥ 16px for inputs');
            console.log('4. Add max-width: 100% to images');
            console.log('5. Test on real devices');
        }
        
        return {
            passed: totalIssues === 0,
            issueCount: totalIssues,
            issues: this.issues,
            results: this.testResults
        };
    }
}

// Auto-run test
const mobileTest = new MobileResponsivenessTest();
const results = mobileTest.runAllTests();

// Return results for external use
window.mobileTestResults = results;