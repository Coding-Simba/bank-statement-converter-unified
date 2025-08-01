/**
 * PRICING TOGGLE DIAGNOSTIC SCRIPT
 * 
 * Paste this entire script into your browser console on the pricing page
 * to diagnose toggle functionality issues.
 */

console.clear();
console.log('🔧 PRICING TOGGLE DIAGNOSTIC SCRIPT STARTING...\n');

// Create a results object to track all findings
const diagnosticResults = {
    elementChecks: {},
    eventListeners: {},
    styleChecks: {},
    functionalityTests: {},
    errors: []
};

try {
    // ===== 1. ELEMENT EXISTENCE CHECKS =====
    console.log('📋 1. CHECKING ELEMENT EXISTENCE...');
    
    const elements = {
        toggle: document.getElementById('pricingToggle'),
        monthlyLabel: document.getElementById('monthlyLabel'),
        yearlyLabel: document.getElementById('yearlyLabel'),
        toggleSlider: document.querySelector('.toggle-slider'),
        priceElements: document.querySelectorAll('.price-value'),
        annualPrices: document.querySelectorAll('.annual-price'),
        periodElements: document.querySelectorAll('.period')
    };
    
    Object.entries(elements).forEach(([name, element]) => {
        const exists = element !== null;
        const count = element && element.length !== undefined ? element.length : (exists ? 1 : 0);
        diagnosticResults.elementChecks[name] = { exists, count, element };
        
        console.log(`   ${exists ? '✅' : '❌'} ${name}: ${exists ? `Found (${count > 1 ? count + ' elements' : 'single element'})` : 'NOT FOUND'}`);
        
        if (exists && element.length === undefined) {
            console.log(`      Element: `, element);
        }
    });
    
    // ===== 2. EVENT LISTENER CHECKS =====
    console.log('\n🎯 2. CHECKING EVENT LISTENERS...');
    
    const checkEventListeners = (element, elementName) => {
        if (!element) return;
        
        try {
            // Get event listeners (Chrome DevTools specific)
            const listeners = getEventListeners ? getEventListeners(element) : {};
            diagnosticResults.eventListeners[elementName] = listeners;
            
            if (Object.keys(listeners).length > 0) {
                console.log(`   ✅ ${elementName} has event listeners:`, Object.keys(listeners));
                Object.entries(listeners).forEach(([event, handlers]) => {
                    console.log(`      - ${event}: ${handlers.length} handler(s)`);
                });
            } else {
                console.log(`   ⚠️  ${elementName} has NO event listeners`);
            }
        } catch (e) {
            console.log(`   ⚠️  Cannot check event listeners for ${elementName} (getEventListeners not available)`);
            diagnosticResults.eventListeners[elementName] = 'unavailable';
        }
    };
    
    checkEventListeners(elements.toggle, 'pricingToggle');
    checkEventListeners(elements.monthlyLabel, 'monthlyLabel');
    checkEventListeners(elements.yearlyLabel, 'yearlyLabel');
    
    // ===== 3. CSS STYLE CHECKS =====
    console.log('\n🎨 3. CHECKING CSS STYLES...');
    
    if (elements.toggle) {
        const toggleStyles = window.getComputedStyle(elements.toggle);
        const sliderStyles = elements.toggleSlider ? window.getComputedStyle(elements.toggleSlider) : null;
        
        const styleInfo = {
            toggle: {
                position: toggleStyles.position,
                width: toggleStyles.width,
                height: toggleStyles.height,
                backgroundColor: toggleStyles.backgroundColor,
                borderRadius: toggleStyles.borderRadius,
                cursor: toggleStyles.cursor,
                transition: toggleStyles.transition,
                display: toggleStyles.display,
                visibility: toggleStyles.visibility,
                opacity: toggleStyles.opacity
            }
        };
        
        if (sliderStyles) {
            styleInfo.slider = {
                position: sliderStyles.position,
                width: sliderStyles.width,
                height: sliderStyles.height,
                backgroundColor: sliderStyles.backgroundColor,
                borderRadius: sliderStyles.borderRadius,
                transform: sliderStyles.transform,
                transition: sliderStyles.transition,
                top: sliderStyles.top,
                left: sliderStyles.left
            };
        }
        
        diagnosticResults.styleChecks = styleInfo;
        
        console.log('   Toggle element styles:');
        Object.entries(styleInfo.toggle).forEach(([prop, value]) => {
            console.log(`      ${prop}: ${value}`);
        });
        
        if (styleInfo.slider) {
            console.log('   Slider element styles:');
            Object.entries(styleInfo.slider).forEach(([prop, value]) => {
                console.log(`      ${prop}: ${value}`);
            });
        }
        
        // Check for !important styles in CSS
        const styleSheet = Array.from(document.styleSheets).find(sheet => {
            try {
                return Array.from(sheet.cssRules || sheet.rules || []).some(rule => 
                    rule.selectorText && rule.selectorText.includes('toggle-switch')
                );
            } catch (e) {
                return false;
            }
        });
        
        if (styleSheet) {
            console.log('   📌 Found toggle-related CSS rules with !important declarations');
        }
    }
    
    // ===== 4. CLASS STATE CHECKS =====
    console.log('\n🏷️  4. CHECKING CURRENT STATE...');
    
    const currentState = {
        toggleHasActive: elements.toggle ? elements.toggle.classList.contains('active') : false,
        monthlyLabelActive: elements.monthlyLabel ? elements.monthlyLabel.classList.contains('active') : false,
        yearlyLabelActive: elements.yearlyLabel ? elements.yearlyLabel.classList.contains('active') : false,
        currentPrices: []
    };
    
    if (elements.priceElements) {
        elements.priceElements.forEach((el, index) => {
            currentState.currentPrices.push({
                index,
                currentText: el.textContent,
                monthlyData: el.getAttribute('data-monthly'),
                yearlyData: el.getAttribute('data-yearly')
            });
        });
    }
    
    diagnosticResults.currentState = currentState;
    
    console.log(`   Toggle active state: ${currentState.toggleHasActive}`);
    console.log(`   Monthly label active: ${currentState.monthlyLabelActive}`);
    console.log(`   Yearly label active: ${currentState.yearlyLabelActive}`);
    console.log(`   Current prices:`, currentState.currentPrices);
    
    // ===== 5. MANUAL FUNCTIONALITY TESTS =====
    console.log('\n🧪 5. RUNNING FUNCTIONALITY TESTS...');
    
    const testResults = {};
    
    // Test 1: Manual class toggle
    if (elements.toggle) {
        console.log('   Test 1: Manual class toggle...');
        const initialState = elements.toggle.classList.contains('active');
        elements.toggle.classList.toggle('active');
        const afterToggle = elements.toggle.classList.contains('active');
        elements.toggle.classList.toggle('active'); // Restore
        
        testResults.manualClassToggle = {
            initialState,
            afterToggle,
            works: initialState !== afterToggle
        };
        
        console.log(`      Initial: ${initialState}, After toggle: ${afterToggle}, Works: ${testResults.manualClassToggle.works}`);
    }
    
    // Test 2: Manual click simulation
    if (elements.toggle) {
        console.log('   Test 2: Click event simulation...');
        const initialClasses = elements.toggle.className;
        
        try {
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            
            elements.toggle.dispatchEvent(clickEvent);
            
            const afterClickClasses = elements.toggle.className;
            testResults.clickSimulation = {
                initialClasses,
                afterClickClasses,
                changed: initialClasses !== afterClickClasses
            };
            
            console.log(`      Classes before: "${initialClasses}"`);
            console.log(`      Classes after: "${afterClickClasses}"`);
            console.log(`      Changed: ${testResults.clickSimulation.changed}`);
            
        } catch (e) {
            testResults.clickSimulation = { error: e.message };
            console.log(`      Error: ${e.message}`);
        }
    }
    
    // Test 3: Price update function test
    console.log('   Test 3: Price update mechanism...');
    if (elements.priceElements && elements.priceElements.length > 0) {
        const testPriceUpdate = (isYearly) => {
            console.log(`      Testing ${isYearly ? 'yearly' : 'monthly'} price update...`);
            
            elements.priceElements.forEach((el, index) => {
                const monthly = el.getAttribute('data-monthly');
                const yearly = el.getAttribute('data-yearly');
                const expectedText = isYearly ? yearly : monthly;
                
                console.log(`         Price ${index}: monthly="${monthly}", yearly="${yearly}", expected="${expectedText}"`);
            });
        };
        
        testPriceUpdate(false);
        testPriceUpdate(true);
    }
    
    diagnosticResults.functionalityTests = testResults;
    
    // ===== 6. JAVASCRIPT ERROR DETECTION =====
    console.log('\n🚨 6. CHECKING FOR JAVASCRIPT ERRORS...');
    
    // Override console.error to catch errors
    const originalConsoleError = console.error;
    const capturedErrors = [];
    
    console.error = function(...args) {
        capturedErrors.push(args.join(' '));
        originalConsoleError.apply(console, args);
    };
    
    // Try to trigger the toggle functionality
    if (elements.toggle) {
        try {
            console.log('   Attempting to trigger toggle...');
            elements.toggle.click();
        } catch (e) {
            capturedErrors.push(`Toggle click error: ${e.message}`);
        }
    }
    
    // Restore console.error
    console.error = originalConsoleError;
    
    diagnosticResults.errors = capturedErrors;
    if (capturedErrors.length > 0) {
        console.log('   ❌ JavaScript errors found:');
        capturedErrors.forEach(error => console.log(`      - ${error}`));
    } else {
        console.log('   ✅ No JavaScript errors detected');
    }
    
    // ===== 7. SUMMARY AND RECOMMENDATIONS =====
    console.log('\n📊 7. DIAGNOSTIC SUMMARY');
    console.log('================================');
    
    let issues = [];
    let recommendations = [];
    
    // Check for common issues
    if (!elements.toggle) {
        issues.push('Toggle element not found');
        recommendations.push('Verify the element ID "pricingToggle" exists in the DOM');
    }
    
    if (!elements.monthlyLabel || !elements.yearlyLabel) {
        issues.push('Label elements not found');
        recommendations.push('Check that monthlyLabel and yearlyLabel elements exist');
    }
    
    if (elements.toggle && (!diagnosticResults.eventListeners.pricingToggle || 
        Object.keys(diagnosticResults.eventListeners.pricingToggle).length === 0)) {
        issues.push('No event listeners detected on toggle');
        recommendations.push('Event listeners may not be properly attached');
    }
    
    if (testResults.clickSimulation && !testResults.clickSimulation.changed) {
        issues.push('Click events not changing element state');
        recommendations.push('Check if event handlers are working correctly');
    }
    
    if (capturedErrors.length > 0) {
        issues.push('JavaScript errors detected');
        recommendations.push('Fix JavaScript errors before proceeding');
    }
    
    console.log('Issues found:');
    if (issues.length === 0) {
        console.log('   ✅ No major issues detected!');
    } else {
        issues.forEach(issue => console.log(`   ❌ ${issue}`));
    }
    
    console.log('\nRecommendations:');
    if (recommendations.length === 0) {
        console.log('   🎉 Everything looks good!');
    } else {
        recommendations.forEach(rec => console.log(`   💡 ${rec}`));
    }
    
    // ===== 8. INTERACTIVE TEST FUNCTIONS =====
    console.log('\n🎮 8. INTERACTIVE TEST FUNCTIONS');
    console.log('================================');
    console.log('The following functions are now available in the console:');
    console.log('');
    console.log('🔧 debugToggle() - Run basic toggle test');
    console.log('🎯 testToggleClick() - Simulate toggle click');
    console.log('📊 showDiagnosticResults() - Show full diagnostic data');
    console.log('🔄 forceToggleState(isYearly) - Force toggle to yearly (true) or monthly (false)');
    console.log('🎨 checkToggleStyles() - Re-check all toggle styles');
    console.log('');
    
    // Make functions available globally
    window.debugToggle = function() {
        console.log('🔧 Debug Toggle Test:');
        const toggle = document.getElementById('pricingToggle');
        if (toggle) {
            console.log('Toggle element:', toggle);
            console.log('Current classes:', toggle.className);
            console.log('Click test...');
            toggle.click();
            console.log('Classes after click:', toggle.className);
        } else {
            console.log('❌ Toggle element not found');
        }
    };
    
    window.testToggleClick = function() {
        console.log('🎯 Testing Toggle Click:');
        const toggle = document.getElementById('pricingToggle');
        if (toggle) {
            const before = toggle.classList.contains('active');
            console.log('Before click - Active:', before);
            
            toggle.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            }));
            
            const after = toggle.classList.contains('active');
            console.log('After click - Active:', after);
            console.log('State changed:', before !== after);
        } else {
            console.log('❌ Toggle element not found');
        }
    };
    
    window.showDiagnosticResults = function() {
        console.log('📊 Full Diagnostic Results:', diagnosticResults);
    };
    
    window.forceToggleState = function(isYearly) {
        console.log(`🔄 Forcing toggle to ${isYearly ? 'yearly' : 'monthly'} state...`);
        
        const toggle = document.getElementById('pricingToggle');
        const monthlyLabel = document.getElementById('monthlyLabel');
        const yearlyLabel = document.getElementById('yearlyLabel');
        
        if (toggle && monthlyLabel && yearlyLabel) {
            // Update toggle visual state
            if (isYearly) {
                toggle.classList.add('active');
            } else {
                toggle.classList.remove('active');
            }
            
            // Update labels
            monthlyLabel.classList.toggle('active', !isYearly);
            yearlyLabel.classList.toggle('active', isYearly);
            
            // Update prices
            document.querySelectorAll('.price-value').forEach(el => {
                const monthly = el.getAttribute('data-monthly');
                const yearly = el.getAttribute('data-yearly');
                el.textContent = isYearly ? yearly : monthly;
            });
            
            // Update annual price display
            document.querySelectorAll('.annual-price').forEach(el => {
                el.style.display = isYearly ? 'block' : 'none';
            });
            
            console.log('✅ Toggle state forced successfully');
            console.log('Current state:', {
                toggleActive: toggle.classList.contains('active'),
                monthlyActive: monthlyLabel.classList.contains('active'),
                yearlyActive: yearlyLabel.classList.contains('active')
            });
        } else {
            console.log('❌ Could not find required elements');
        }
    };
    
    window.checkToggleStyles = function() {
        console.log('🎨 Re-checking Toggle Styles:');
        const toggle = document.getElementById('pricingToggle');
        const slider = document.querySelector('.toggle-slider');
        
        if (toggle) {
            const styles = window.getComputedStyle(toggle);
            console.log('Toggle styles:', {
                width: styles.width,
                height: styles.height,
                backgroundColor: styles.backgroundColor,
                cursor: styles.cursor,
                position: styles.position
            });
            
            if (slider) {
                const sliderStyles = window.getComputedStyle(slider);
                console.log('Slider styles:', {
                    width: sliderStyles.width,
                    height: sliderStyles.height,
                    backgroundColor: sliderStyles.backgroundColor,
                    transform: sliderStyles.transform,
                    transition: sliderStyles.transition
                });
            }
        }
    };
    
    console.log('✅ DIAGNOSTIC COMPLETE! Use the functions above to continue testing.');
    
} catch (error) {
    console.error('❌ Error running diagnostic script:', error);
    diagnosticResults.scriptError = error.message;
}

// Return the diagnostic results
window.pricingToggleDiagnostics = diagnosticResults;
console.log('\n📋 Diagnostic results stored in: window.pricingToggleDiagnostics');