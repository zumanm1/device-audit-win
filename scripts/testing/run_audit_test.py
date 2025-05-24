#!/usr/bin/env python3
"""
Script to test the NetAuditPro application with the new network inventory.
This script will:
1. Set network-inventory.csv as the active inventory
2. Run an audit against the devices
3. Monitor the audit progress
"""

import asyncio
import time
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "audit_test_screenshots"

async def test_network_audit():
    """Run a complete test of the network audit functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("\n===== Testing Network Audit =====")
            
            # Step 1: Set the new inventory as active
            print("\nSetting network-inventory.csv as active...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Select network-inventory.csv from the dropdown
            inventory_dropdown = await page.query_selector("#active_inventory_file_manage")
            if inventory_dropdown:
                options = await inventory_dropdown.query_selector_all("option")
                found_inventory = False
                
                for option in options:
                    value = await option.get_attribute("value")
                    if "network-inventory.csv" in value:
                        await inventory_dropdown.select_option(value)
                        found_inventory = True
                        print(f"✅ Selected network-inventory.csv in dropdown")
                        break
                
                if not found_inventory:
                    print("❌ network-inventory.csv not found in dropdown")
                    return
                
                # Click Set as Active button
                set_active_button = await page.query_selector('button:has-text("Set as Active")')
                if set_active_button:
                    await set_active_button.click()
                    await page.wait_for_timeout(2000)
                    print("✅ Set network-inventory.csv as active")
                else:
                    print("❌ Set as Active button not found")
                    return
            else:
                print("❌ Inventory dropdown not found")
                return
            
            # Step 2: Navigate to the home page and run an audit
            print("\nNavigating to home page to run audit...")
            await page.goto(f"{APP_URL}/")
            await page.wait_for_load_state("networkidle")
            
            # Click Run Audit button
            run_audit_button = await page.query_selector('button:has-text("Run Audit")')
            if run_audit_button:
                await run_audit_button.click()
                print("✅ Started audit")
            else:
                print("❌ Run Audit button not found")
                return
            
            # Step 3: Monitor the audit progress
            print("\nMonitoring audit progress...")
            
            # Check for auto-refresh functionality
            for i in range(3):  # Monitor for about 1.5 minutes (3 refresh cycles)
                print(f"\nMonitoring cycle {i+1}...")
                
                # Wait for the 30-second auto-refresh
                await page.wait_for_timeout(32000)  # 32 seconds to ensure refresh has occurred
                
                # Check if audit logs are being updated
                log_elements = await page.query_selector_all("#audit-log-entries .log-entry")
                log_count = len(log_elements)
                print(f"Found {log_count} log entries")
                
                # Check current audit status
                status_element = await page.query_selector("#current-audit-status")
                if status_element:
                    status_text = await status_element.inner_text()
                    print(f"Current audit status: {status_text}")
                
                # Take a screenshot
                await page.screenshot(path=f"{SCREENSHOT_DIR}/audit_progress_{i+1}.png")
            
            print("\n===== Audit Test Complete =====")
            return True
            
        except Exception as e:
            print(f"❌ Error during audit test: {e}")
            return False
        finally:
            await browser.close()

async def main():
    await test_network_audit()

if __name__ == "__main__":
    import os
    # Create screenshot directory
    os.makedirs("audit_test_screenshots", exist_ok=True)
    asyncio.run(main())
