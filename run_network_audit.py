#!/usr/bin/env python3
"""
Script to automate the NetAuditPro workflow:
1. Set network-inventory.csv as the active inventory
2. Run an audit against the devices
3. Monitor the audit progress with auto-refresh
"""

import asyncio
import time
import os
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "audit_screenshots"

async def run_network_audit():
    """Run a full network audit with the updated inventory"""
    async with async_playwright() as p:
        # Launch browser in headless mode (required for environments without X Server)
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        
        # Enable console logging
        page = await context.new_page()
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        try:
            print("\n===== NETWORK AUDIT AUTOMATION =====")
            
            # Step 1: Set the new inventory as active
            print("\nSetting network-inventory.csv as active inventory...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of initial inventory page
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_page.png")
            
            # Select network-inventory.csv from the dropdown
            await page.select_option("#active_inventory_file_manage", "network-inventory.csv")
            print("✅ Selected network-inventory.csv in dropdown")
            
            # Click Set as Active button
            set_active_button = await page.query_selector('button:text("Set as Active")')
            if set_active_button:
                await set_active_button.click()
            else:
                print("❌ Could not find 'Set as Active' button")
            await page.wait_for_timeout(2000)
            print("✅ Set network-inventory.csv as active")
            
            # Take screenshot after setting active inventory
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_inventory_activated.png")
            
            # Step 2: Navigate to home page and run audit
            print("\nNavigating to home page to run audit...")
            await page.goto(f"{APP_URL}/")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of home page before audit
            await page.screenshot(path=f"{SCREENSHOT_DIR}/03_home_before_audit.png")
            
            # Click Run Audit button
            run_audit_button = await page.query_selector('button:text("Run Audit")')
            if run_audit_button:
                await run_audit_button.click()
                print("✅ Started audit")
            else:
                print("❌ Could not find 'Run Audit' button")
            
            # Take screenshot after starting audit
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_audit_started.png")
            
            # Step 3: Monitor the audit progress for 5 minutes (10 refresh cycles)
            print("\nMonitoring audit progress with auto-refresh (30-second intervals)...")
            previous_logs = ""
            
            for i in range(10):  # Monitor for about 5 minutes (10 refresh cycles)
                current_time = time.strftime("%H:%M:%S", time.localtime())
                print(f"\n[{current_time}] Monitoring cycle {i+1}/10...")
                
                # Take screenshot at start of this cycle
                await page.screenshot(path=f"{SCREENSHOT_DIR}/05_audit_cycle_{i+1}.png")
                
                # Get current logs
                log_container = await page.query_selector("#audit-log-entries")
                if log_container:
                    current_logs = await log_container.inner_text()
                    log_lines = current_logs.count('\n') + 1 if current_logs else 0
                    
                    # Check if logs have been updated
                    if current_logs != previous_logs:
                        print(f"✅ Logs updated, {log_lines} lines found")
                        previous_logs = current_logs
                    else:
                        print(f"⚠️ No new log entries detected")
                else:
                    print("❌ Log container not found")
                
                # Check current audit status
                status_element = await page.query_selector("#current-audit-status")
                if status_element:
                    status_text = await status_element.inner_text()
                    print(f"Current audit status: {status_text}")
                
                # Wait for the auto-refresh cycle (30 seconds) minus time already spent
                wait_time = max(25, 30 - 5)  # Ensure at least 25 seconds wait
                print(f"Waiting {wait_time} seconds for next auto-refresh...")
                await page.wait_for_timeout(wait_time * 1000)
            
            # Final screenshot after monitoring period
            await page.screenshot(path=f"{SCREENSHOT_DIR}/06_audit_completed.png")
            
            print("\n===== Audit Monitoring Complete =====")
            print(f"Screenshots saved to {SCREENSHOT_DIR}/")
            
        except Exception as e:
            print(f"❌ Error during audit: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Run the audit automation
    asyncio.run(run_network_audit())
