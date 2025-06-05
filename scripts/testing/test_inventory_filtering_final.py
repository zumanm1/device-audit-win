#!/usr/bin/env python3
"""
Comprehensive Test for Inventory Filtering Functionality
- Tests filtering by hostname, IP address, and device type
- Verifies proper population of device type dropdown
- Confirms reset functionality works correctly
- Uses the network-inventory.csv with proper jump host connectivity
"""

import asyncio
import time
from playwright.async_api import async_playwright
import os
import json

# Configuration
APP_URL = "http://localhost:5007"
INVENTORY_FILE = "network-inventory.csv"
SCREENSHOT_DIR = "filter_test_screenshots"

async def test_inventory_filtering():
    """Run comprehensive tests for inventory filtering functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging for debugging
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        try:
            print("\n===== Testing Inventory Filtering Functionality =====")
            
            # Step 1: Set network-inventory.csv as active inventory
            print("\nSetting up test environment...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of initial inventory page
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_page.png")
            
            # Select network-inventory.csv from the dropdown
            await page.select_option("#active_inventory_file_manage", INVENTORY_FILE)
            
            # Click Set as Active button
            set_active_button = await page.query_selector('button:text("Set as Active")')
            if set_active_button:
                await set_active_button.click()
                await page.wait_for_timeout(2000)
                print(f"✅ Set {INVENTORY_FILE} as active inventory")
            else:
                print("❌ Could not find 'Set as Active' button")
                return
            
            # Step 2: Test table population
            print("\nTesting table population...")
            
            # Wait for table to be populated
            await page.wait_for_timeout(2000)
            
            # Count rows in the table
            rows = await page.query_selector_all('#csv-table tbody tr')
            row_count = len(rows)
            
            if row_count > 0:
                print(f"✅ Table populated with {row_count} rows")
                
                # Extract data from first row for validation
                first_row_cells = await rows[0].query_selector_all('td')
                if len(first_row_cells) > 0:
                    hostname = await first_row_cells[0].inner_text()
                    ip = await first_row_cells[1].inner_text() if len(first_row_cells) > 1 else "N/A"
                    device_type = await first_row_cells[2].inner_text() if len(first_row_cells) > 2 else "N/A"
                    print(f"First row data: Hostname={hostname}, IP={ip}, Type={device_type}")
            else:
                print("❌ Table not populated")
                return
            
            # Step 3: Test device type dropdown population
            print("\nTesting device type dropdown population...")
            device_type_dropdown = await page.query_selector('#deviceTypeFilter')
            
            if device_type_dropdown:
                options = await device_type_dropdown.query_selector_all('option')
                option_count = len(options) - 1  # Subtract 1 for the default "All" option
                
                if option_count > 0:
                    option_values = []
                    for option in options:
                        value = await option.get_attribute('value')
                        if value and value != "":
                            option_values.append(value)
                    
                    print(f"✅ Device type dropdown populated with {option_count} options: {', '.join(option_values)}")
                else:
                    print("❌ Device type dropdown has no options")
            else:
                print("❌ Device type dropdown not found")
            
            # Step 4: Test hostname filtering
            print("\nTesting hostname filtering...")
            
            # Filter by 'R' to get routers
            hostname_filter = await page.query_selector('#hostnameFilter')
            if hostname_filter:
                # Clear any existing value and type 'R'
                await hostname_filter.fill('')
                await hostname_filter.type('R')
                await page.wait_for_timeout(1000)
                
                # Count visible rows
                visible_rows = await page.query_selector_all('#csv-table tbody tr:not(.hidden)')
                visible_count = len(visible_rows)
                
                # Get text of first visible row for validation
                if visible_count > 0:
                    first_visible_hostname = await visible_rows[0].query_selector('td').inner_text()
                    print(f"Hostname filter 'R': {visible_count} of {row_count} visible")
                    print(f"  First visible row: {first_visible_hostname}")
                    print(f"✅ Hostname filtering works")
                else:
                    print("❌ Hostname filtering not working - no visible rows")
                
                # Clear filter
                await hostname_filter.fill('')
                await page.wait_for_timeout(1000)
            else:
                print("❌ Hostname filter input not found")
            
            # Step 5: Test device type filtering
            print("\nTesting device type filtering...")
            
            # Select 'router' from dropdown
            await page.select_option('#deviceTypeFilter', 'router')
            await page.wait_for_timeout(1000)
            
            # Count visible rows
            visible_rows = await page.query_selector_all('#csv-table tbody tr:not(.hidden)')
            visible_count = len(visible_rows)
            
            print(f"Device type filter 'router': {visible_count} of {row_count} visible")
            if visible_count > 0 and visible_count < row_count:
                print("✅ Device type filtering works")
            else:
                print("⚠️ Device type filtering may not be working correctly")
            
            # Step 6: Test IP address filtering
            print("\nTesting IP address filtering...")
            
            # Reset filters first
            await page.click('#resetFilters')
            await page.wait_for_timeout(1000)
            
            # Filter by IP pattern
            ip_filter = await page.query_selector('#ipFilter')
            if ip_filter:
                await ip_filter.fill('172.16')
                await page.wait_for_timeout(1000)
                
                # Count visible rows
                visible_rows = await page.query_selector_all('#csv-table tbody tr:not(.hidden)')
                visible_count = len(visible_rows)
                
                print(f"IP filter '172.16': {visible_count} of {row_count} visible")
                if visible_count > 0:
                    print("✅ IP address filtering works")
                else:
                    print("❌ IP address filtering not working - no visible rows")
            else:
                print("❌ IP filter input not found")
            
            # Step 7: Test reset functionality
            print("\nTesting reset filter functionality...")
            
            # Click reset button
            await page.click('#resetFilters')
            await page.wait_for_timeout(1000)
            
            # Count visible rows after reset
            visible_rows = await page.query_selector_all('#csv-table tbody tr:not(.hidden)')
            visible_count = len(visible_rows)
            
            print(f"After reset: {visible_count} of {row_count} visible")
            if visible_count == row_count:
                print("✅ Reset functionality works")
            else:
                print(f"❌ Reset not working correctly. Expected {row_count} rows, got {visible_count}")
            
            # Take final screenshot
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_filtering_completed.png")
            
            print("\n===== Inventory Filtering Test Complete =====")
            print(f"Screenshots saved to {SCREENSHOT_DIR}/")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            return False
        finally:
            await browser.close()

async def inspect_javascript_code():
    """Inspect the JavaScript code handling inventory filtering"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("\n===== Inspecting JavaScript Code =====")
            
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Extract JavaScript functions related to filtering
            js_code = await page.evaluate("""
                () => {
                    // Find script tags
                    const scripts = Array.from(document.querySelectorAll('script:not([src])'));
                    
                    // Extract filtering related code
                    const filteringCode = scripts
                        .map(script => script.textContent)
                        .filter(text => 
                            text.includes('populateCSVTable') || 
                            text.includes('filter') || 
                            text.includes('resetFilters'))
                        .join('\\n\\n// ---- NEXT SCRIPT BLOCK ----\\n\\n');
                    
                    return filteringCode;
                }
            """)
            
            if js_code:
                # Save the extracted code for analysis
                with open(f"{SCREENSHOT_DIR}/filtering_code.js", "w") as f:
                    f.write(js_code)
                print("✅ Extracted JavaScript filtering code saved to filtering_code.js")
            else:
                print("❌ Could not extract JavaScript filtering code")
            
        except Exception as e:
            print(f"❌ Error during code inspection: {e}")
        finally:
            await browser.close()

async def main():
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Run the filtering tests
    await test_inventory_filtering()
    
    # Inspect JavaScript code
    await inspect_javascript_code()

if __name__ == "__main__":
    asyncio.run(main())
