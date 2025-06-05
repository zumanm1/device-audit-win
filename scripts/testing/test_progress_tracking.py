#!/usr/bin/env python3
"""
Playwright test script for NetAuditPro Enhanced Progress Tracking

This script uses Playwright to test the Enhanced Progress Tracking
functionality in the NetAuditPro application.
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_enhanced_progress_tracking():
    """Test the Enhanced Progress Tracking section of NetAuditPro."""
    
    async with async_playwright() as p:
        # Launch the browser with appropriate flags for root environment
        browser = await p.chromium.launch(
            headless=True,  # Headless mode is required in environments without X server
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # Create a new browser context and page
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to the NetAuditPro application
        print("Navigating to NetAuditPro...")
        await page.goto('http://localhost:5007')
        
        # Wait for the page to load completely
        await page.wait_for_load_state('networkidle')
        
        # Take a screenshot of the initial state
        await page.screenshot(path='initial_state.png')
        print("Captured initial state")
        
        # Check if an audit is already running
        is_running = await page.evaluate('''() => {
            const statusElement = document.querySelector('.status-card .card-header h4');
            return statusElement && statusElement.textContent.includes('Running');
        }''')
        
        if is_running:
            print("Audit is already running, stopping it first...")
            stop_button = await page.query_selector('#stop-reset-audit')
            if stop_button:
                await stop_button.click()
                # Wait for the stop action to complete
                await page.wait_for_timeout(2000)
        
        # Start monitoring console logs
        page.on('console', lambda msg: print(f"CONSOLE: {msg.text}"))
        
        # Click the Run Audit button (which doesn't have an ID but is in a form with action='/start_audit')
        print("Starting the audit...")
        run_button = await page.query_selector('form[action="/start_audit"] button')
        if run_button:
            await run_button.click()
            
            # Wait for the audit to start
            await page.wait_for_timeout(3000)
            
            # Check if the Enhanced Progress Tracking section is updating
            print("Monitoring Enhanced Progress Tracking updates...")
            
            # Take screenshots at intervals to document progress
            for i in range(3):
                # Wait for some time between checks
                await page.wait_for_timeout(5000)
                
                # Get current progress data
                progress_data = await page.evaluate('''() => {
                    const progressPercent = document.querySelector('#enhanced-progress-bar')?.style.width || '0%';
                    const currentDevice = document.querySelector('#current-device-name')?.textContent || 'None';
                    const successCount = document.querySelector('#success-count')?.textContent || '0';
                    const warningCount = document.querySelector('#warning-count')?.textContent || '0';
                    const failureCount = document.querySelector('#failure-count')?.textContent || '0';
                    
                    return {
                        progressPercent, 
                        currentDevice,
                        successCount,
                        warningCount,
                        failureCount
                    };
                }''')
                
                print(f"Progress Update #{i+1}:")
                print(f"  Progress: {progress_data['progressPercent']}")
                print(f"  Current Device: {progress_data['currentDevice']}")
                print(f"  Success Count: {progress_data['successCount']}")
                print(f"  Warning Count: {progress_data['warningCount']}")
                print(f"  Failure Count: {progress_data['failureCount']}")
                
                # Take a screenshot of the current state
                await page.screenshot(path=f'progress_state_{i+1}.png')
            
            # Test stopping the audit
            print("Testing stop/reset functionality...")
            stop_button = await page.query_selector('#stop-reset-audit')
            if stop_button:
                await stop_button.click()
                # Wait for the stop action to complete
                await page.wait_for_timeout(2000)
                
                # Take a screenshot of the final state
                await page.screenshot(path='final_state.png')
                
                # Verify the UI has reset
                reset_verified = await page.evaluate('''() => {
                    const statusElement = document.querySelector('.status-card .card-header h4');
                    return statusElement && !statusElement.textContent.includes('Running');
                }''')
                
                if reset_verified:
                    print("Stop/Reset functionality verified successfully")
                else:
                    print("Stop/Reset functionality verification failed")
        else:
            print("Failed to find the Run Audit button")
        
        # Close the browser
        await browser.close()
        print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_enhanced_progress_tracking())
