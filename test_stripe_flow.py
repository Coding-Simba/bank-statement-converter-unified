#!/usr/bin/env python3
"""
Test script for Stripe purchase flow on bankcsvconverter.com
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def test_stripe_flow():
    # Setup Chrome with console logging enabled
    options = webdriver.ChromeOptions()
    options.add_argument('--enable-logging')
    options.add_argument('--log-level=0')
    options.add_argument('--dump-dom')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Enable performance logging to capture console messages
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    results = {
        "steps": [],
        "console_messages": [],
        "errors": [],
        "final_url": "",
        "auth_persisted": False
    }
    
    try:
        # Step 1: Clear browser data
        print("Step 1: Starting fresh browser session (data cleared)")
        results["steps"].append("Step 1: Started fresh browser session")
        
        # Step 2: Navigate to pricing page
        print("Step 2: Navigating to pricing page...")
        driver.get("https://bankcsvconverter.com/pricing.html")
        time.sleep(3)  # Wait for page load
        results["steps"].append(f"Step 2: Navigated to pricing page - Current URL: {driver.current_url}")
        
        # Capture initial console messages
        logs = driver.get_log('browser')
        for log in logs:
            if any(keyword in log['message'] for keyword in ['[Force Auth]', '[Stripe Complete]', '[Auth Login Fix]', 'auth', 'Auth']):
                results["console_messages"].append(f"Initial load: {log['message']}")
        
        # Step 3: Check for console errors
        print("Step 3: Checking for console errors...")
        for log in logs:
            if log['level'] == 'SEVERE':
                results["errors"].append(f"Console error: {log['message']}")
        results["steps"].append("Step 3: Checked console for errors")
        
        # Step 4: Click Buy button
        print("Step 4: Looking for Buy button...")
        try:
            # Try to find a buy button (multiple possible selectors)
            buy_button = None
            selectors = [
                "button:contains('Buy')",
                "a:contains('Buy')",
                ".buy-button",
                "[data-price]",
                "button[onclick*='stripe']",
                "button[onclick*='purchase']"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith('button:contains') or selector.startswith('a:contains'):
                        # Use XPath for contains text
                        xpath = f"//{selector.split(':')[0]}[contains(text(), 'Buy')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                        if elements:
                            buy_button = elements[0]
                            break
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            buy_button = elements[0]
                            break
                except:
                    continue
            
            if buy_button:
                print(f"Found buy button: {buy_button.text}")
                driver.execute_script("arguments[0].scrollIntoView(true);", buy_button)
                time.sleep(1)
                buy_button.click()
                results["steps"].append(f"Step 4: Clicked buy button - Redirected to: {driver.current_url}")
            else:
                results["steps"].append("Step 4: No buy button found on page")
                results["errors"].append("Could not find any buy button on pricing page")
        except Exception as e:
            results["steps"].append(f"Step 4: Error clicking buy button - {str(e)}")
            results["errors"].append(f"Buy button error: {str(e)}")
        
        time.sleep(3)  # Wait for redirect
        
        # Step 5: Check redirect location
        current_url = driver.current_url
        print(f"Step 5: Current URL after buy click: {current_url}")
        results["steps"].append(f"Step 5: After buy click - URL: {current_url}")
        
        # Capture console messages after redirect
        logs = driver.get_log('browser')
        for log in logs:
            if any(keyword in log['message'] for keyword in ['[Force Auth]', '[Stripe Complete]', '[Auth Login Fix]', 'auth', 'Auth']):
                results["console_messages"].append(f"After buy click: {log['message']}")
        
        # Step 6: Check if on login page
        if 'login' in current_url.lower() or 'signin' in current_url.lower():
            print("Step 6: On login page")
            results["steps"].append("Step 6: Redirected to login page as expected")
            
            # Capture login page console messages
            logs = driver.get_log('browser')
            for log in logs:
                if any(keyword in log['message'] for keyword in ['[Force Auth]', '[Stripe Complete]', '[Auth Login Fix]', 'auth', 'Auth']):
                    results["console_messages"].append(f"Login page: {log['message']}")
            
            # Step 7: Try to login (would need real credentials)
            results["steps"].append("Step 7: Would need valid credentials to proceed with login")
            
        else:
            results["steps"].append(f"Step 6: Not redirected to login page - Current URL: {current_url}")
        
        # Capture final state
        results["final_url"] = driver.current_url
        
        # Check for any final console messages
        logs = driver.get_log('browser')
        for log in logs:
            if any(keyword in log['message'] for keyword in ['[Force Auth]', '[Stripe Complete]', '[Auth Login Fix]', 'auth', 'Auth']):
                results["console_messages"].append(f"Final: {log['message']}")
        
    except Exception as e:
        results["errors"].append(f"Test error: {str(e)}")
        print(f"Error during test: {str(e)}")
    
    finally:
        # Take screenshot for debugging
        driver.save_screenshot("/Users/MAC/chrome/bank-statement-converter-unified/stripe_test_screenshot.png")
        driver.quit()
    
    return results

if __name__ == "__main__":
    print("Starting Stripe purchase flow test...")
    results = test_stripe_flow()
    
    print("\n=== TEST RESULTS ===")
    print("\nSteps completed:")
    for step in results["steps"]:
        print(f"  - {step}")
    
    print("\nConsole messages (auth-related):")
    if results["console_messages"]:
        for msg in results["console_messages"]:
            print(f"  - {msg}")
    else:
        print("  - No auth-related console messages found")
    
    print("\nErrors encountered:")
    if results["errors"]:
        for error in results["errors"]:
            print(f"  - {error}")
    else:
        print("  - No errors")
    
    print(f"\nFinal URL: {results['final_url']}")
    print(f"Auth persisted: {results['auth_persisted']}")
    
    # Save results to file
    with open("/Users/MAC/chrome/bank-statement-converter-unified/stripe_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to stripe_test_results.json")