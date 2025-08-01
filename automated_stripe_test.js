// Automated E2E Stripe Checkout Test
// Usage: node automated_stripe_test.js
// Requires: npm install playwright

const { chromium } = require('playwright');

async function runStripeCheckoutTest() {
    console.log('🚀 Starting E2E Stripe Checkout Test');
    
    const browser = await chromium.launch({ 
        headless: false, // Set to true for headless mode
        slowMo: 1000 // Slow down actions for visibility
    });
    
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    
    const page = await context.newPage();
    
    // Enable request interception to monitor network
    await page.route('**/*', route => {
        const url = route.request().url();
        if (url.includes('/api/stripe/')) {
            console.log('🔍 Stripe API Request:', route.request().method(), url);
            console.log('📝 Headers:', route.request().headers());
            if (route.request().postData()) {
                console.log('📦 Body:', route.request().postData());
            }
        }
        route.continue();
    });
    
    // Listen for responses
    page.on('response', response => {
        const url = response.url();
        if (url.includes('/api/stripe/')) {
            console.log('📥 Stripe API Response:', response.status(), url);
        }
    });
    
    try {
        // Step 1: Navigate to pricing page
        console.log('📄 Step 1: Navigating to pricing page');
        await page.goto('https://bankcsvconverter.com/pricing.html');
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'screenshots/01_pricing_page_loaded.png' });
        
        // Step 2: Check if user is authenticated
        console.log('🔐 Step 2: Checking authentication status');
        const authStatus = await page.evaluate(() => {
            return {
                bankAuthAvailable: typeof window.BankAuth !== 'undefined',
                isAuthenticated: window.BankAuth && window.BankAuth.TokenManager.isAuthenticated(),
                accessToken: window.BankAuth ? window.BankAuth.TokenManager.getAccessToken() : null
            };
        });
        
        console.log('Auth Status:', authStatus);
        
        if (!authStatus.isAuthenticated) {
            console.log('❌ User not authenticated. This test requires a logged-in user.');
            console.log('Please log in manually first or implement login automation.');
            return;
        }
        
        // Step 3: Analyze pricing plans
        console.log('💰 Step 3: Analyzing pricing plans');
        const plans = await page.evaluate(() => {
            const pricingCards = document.querySelectorAll('.pricing-card');
            return Array.from(pricingCards).map((card, index) => {
                const title = card.querySelector('.pricing-tier')?.textContent?.trim();
                const price = card.querySelector('.price-value')?.textContent?.trim();
                const button = card.querySelector('.pricing-cta.primary');
                return {
                    index,
                    title,
                    price: `$${price}/month`,
                    hasButton: !!button
                };
            });
        });
        
        console.log('Available plans:', plans);
        await page.screenshot({ path: 'screenshots/02_pricing_plans_overview.png' });
        
        // Step 4: Click on Professional plan (index 1 - the featured plan)
        console.log('🚀 Step 4: Clicking Professional plan buy button');
        const professionalButton = page.locator('.pricing-card').nth(1).locator('.pricing-cta.primary');
        
        // Wait for button to be visible and clickable
        await professionalButton.waitFor({ state: 'visible' });
        await page.screenshot({ path: 'screenshots/03_before_professional_click.png' });
        
        // Click the button and wait for navigation or popup
        const [response] = await Promise.all([
            page.waitForResponse(response => 
                response.url().includes('/api/stripe/create-checkout-session') && 
                response.status() === 200
            ),
            professionalButton.click()
        ]);
        
        console.log('✅ Checkout session creation response received');
        const responseData = await response.json();
        console.log('Checkout session data:', responseData);
        
        await page.screenshot({ path: 'screenshots/04_after_professional_click.png' });
        
        // Step 5: Wait for redirect to Stripe
        console.log('🔄 Step 5: Waiting for Stripe checkout redirect');
        await page.waitForURL('**/checkout.stripe.com/**', { timeout: 10000 });
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'screenshots/05_stripe_checkout_page.png' });
        
        // Step 6: Fill in test card details
        console.log('💳 Step 6: Filling in test card details');
        
        // Wait for Stripe elements to load
        await page.waitForSelector('[data-testid="card-number-field"]', { timeout: 15000 });
        
        // Fill card number
        await page.fill('[data-testid="card-number-field"]', '4242 4242 4242 4242');
        
        // Fill expiry date
        await page.fill('[data-testid="card-expiry-field"]', '12/25');
        
        // Fill CVC
        await page.fill('[data-testid="card-cvc-field"]', '123');
        
        // Fill ZIP code (if present)
        const zipField = page.locator('[data-testid="card-postal-field"]');
        if (await zipField.isVisible()) {
            await zipField.fill('10001');
        }
        
        await page.screenshot({ path: 'screenshots/06_card_details_filled.png' });
        
        // Step 7: Submit payment
        console.log('💳 Step 7: Submitting payment');
        const submitButton = page.locator('[data-testid="hosted-payment-submit-button"]');
        await submitButton.click();
        
        await page.screenshot({ path: 'screenshots/07_payment_processing.png' });
        
        // Step 8: Wait for success and redirect
        console.log('⏳ Step 8: Waiting for payment success and redirect');
        await page.waitForURL('**/bankcsvconverter.com/**', { timeout: 30000 });
        await page.waitForLoadState('networkidle');
        
        // Check if we're back on our site with success parameters
        const currentUrl = page.url();
        console.log('Final URL:', currentUrl);
        
        if (currentUrl.includes('session_id=')) {
            console.log('✅ Payment successful! Session ID found in URL');
        }
        
        await page.screenshot({ path: 'screenshots/08_payment_success.png' });
        
        // Step 9: Check subscription status
        console.log('📊 Step 9: Checking subscription status');
        
        // Wait a moment for any success messages to appear
        await page.waitForTimeout(3000);
        
        const subscriptionStatus = await page.evaluate(async () => {
            // Check if there's a success message
            const successMessage = document.querySelector('[style*="background: #d1fae5"]');
            
            // Try to fetch subscription status
            if (window.BankAuth && window.BankAuth.TokenManager.isAuthenticated()) {
                try {
                    const apiBase = window.location.hostname === 'localhost' ? 
                        'http://localhost:5000' : `${window.location.protocol}//${window.location.hostname}`;
                    
                    const response = await fetch(`${apiBase}/api/stripe/subscription-status`, {
                        headers: {
                            'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
                        }
                    });
                    
                    if (response.ok) {
                        const status = await response.json();
                        return {
                            hasSuccessMessage: !!successMessage,
                            subscriptionData: status
                        };
                    }
                } catch (error) {
                    console.error('Error fetching subscription status:', error);
                }
            }
            
            return {
                hasSuccessMessage: !!successMessage,
                subscriptionData: null
            };
        });
        
        console.log('Final subscription status:', subscriptionStatus);
        await page.screenshot({ path: 'screenshots/09_final_status.png' });
        
        console.log('🎉 E2E Test completed successfully!');
        console.log('📸 Screenshots saved in screenshots/ directory');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        await page.screenshot({ path: 'screenshots/error_state.png' });
        throw error;
    } finally {
        await browser.close();
    }
}

// Create screenshots directory
const fs = require('fs');
if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots');
}

// Run the test
runStripeCheckoutTest()
    .then(() => {
        console.log('✅ Test suite completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        console.error('❌ Test suite failed:', error);
        process.exit(1);
    });