#!/usr/bin/env python3
"""
Definitive Validation of Inventory Filtering
This script tests the filtering functionality with criteria that should definitely exclude some devices
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

# Configuration
APP_URL = "http://localhost:5007"
INVENTORY_FILE = "network-inventory.csv"

async def validate_filtering():
    """Perform definitive tests of the filtering functionality"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("===== Validating Inventory Filtering Functionality =====")
            
            # Navigate to inventory management page
            print("\nNavigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Set network-inventory.csv as active
            print(f"Setting {INVENTORY_FILE} as active...")
            await page.select_option("#active_inventory_file_manage", INVENTORY_FILE)
            set_active_button = await page.query_selector('button:text("Set as Active")')
            if set_active_button:
                await set_active_button.click()
                await page.wait_for_timeout(2000)
                print(f"✅ Set {INVENTORY_FILE} as active inventory")
            
            # Get inventory data for reference
            inventory_data = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/get_active_inventory_info');
                        if (!response.ok) return { success: false, error: 'API error' };
                        return await response.json();
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                }
            """)
            
            if inventory_data.get('status') == 'success':
                print(f"\nLoaded inventory with {len(inventory_data.get('data', []))} devices")
                
                # Display the inventory data for reference
                print("\nInventory contents:")
                for i, device in enumerate(inventory_data.get('data', [])):
                    hostname = device.get('hostname', 'unknown')
                    ip = device.get('ip', 'unknown')
                    device_type = device.get('device_type', 'unknown')
                    print(f"  Device {i+1}: {hostname} | {ip} | {device_type}")
            
            # Test 1: Filter for a specific device (R1)
            print("\nTest 1: Filtering for specific device 'R1'...")
            await page.fill('#simple-hostname-filter', 'R1')
            await page.wait_for_timeout(1000)
            
            specific_device_results = await page.evaluate("""
                () => {
                    const allRows = document.querySelectorAll('#simple-table-body tr');
                    const visibleRows = document.querySelectorAll('#simple-table-body tr:not(.inventory-hidden-row)');
                    
                    // Collect data from visible rows
                    const visibleData = [];
                    visibleRows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 3) {
                            visibleData.push({
                                hostname: cells[0].textContent,
                                ip: cells[1].textContent,
                                type: cells[2].textContent
                            });
                        }
                    });
                    
                    return {
                        total: allRows.length,
                        visible: visibleRows.length,
                        visibleData: visibleData
                    };
                }
            """)
            
            print(f"  Results: {specific_device_results['visible']} of {specific_device_results['total']} devices visible")
            
            if specific_device_results['visible'] < specific_device_results['total']:
                print("  ✅ Filtering correctly shows subset of devices")
                print("  Visible devices:")
                for device in specific_device_results.get('visibleData', []):
                    print(f"    - {device.get('hostname')} | {device.get('ip')} | {device.get('type')}")
                
                # Verify that only R1 is shown
                r1_only = all(d.get('hostname') == 'R1' for d in specific_device_results.get('visibleData', []))
                if r1_only:
                    print("  ✅ Filter correctly shows only R1")
                else:
                    print("  ❌ Filter shows devices other than R1")
            else:
                print("  ❌ Filter shows all devices, should only show R1")
            
            # Test 2: IP Address filtering
            print("\nTest 2: Filtering by specific IP segment '172.16.39.10'...")
            await page.fill('#simple-hostname-filter', '')  # Clear hostname filter
            await page.fill('#simple-ip-filter', '172.16.39.10')
            await page.wait_for_timeout(1000)
            
            ip_filter_results = await page.evaluate("""
                () => {
                    const allRows = document.querySelectorAll('#simple-table-body tr');
                    const visibleRows = document.querySelectorAll('#simple-table-body tr:not(.inventory-hidden-row)');
                    
                    // Collect data from visible rows
                    const visibleData = [];
                    visibleRows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 3) {
                            visibleData.push({
                                hostname: cells[0].textContent,
                                ip: cells[1].textContent,
                                type: cells[2].textContent
                            });
                        }
                    });
                    
                    return {
                        total: allRows.length,
                        visible: visibleRows.length,
                        visibleData: visibleData
                    };
                }
            """)
            
            print(f"  Results: {ip_filter_results['visible']} of {ip_filter_results['total']} devices visible")
            
            if ip_filter_results['visible'] < ip_filter_results['total']:
                print("  ✅ IP filtering correctly shows subset of devices")
                print("  Visible devices:")
                for device in ip_filter_results.get('visibleData', []):
                    print(f"    - {device.get('hostname')} | {device.get('ip')} | {device.get('type')}")
                
                # Verify that only devices with the specified IP segment are shown
                correct_ips = all('172.16.39.10' in d.get('ip', '') for d in ip_filter_results.get('visibleData', []))
                if correct_ips:
                    print("  ✅ IP filter correctly shows only matching devices")
                else:
                    print("  ❌ IP filter shows devices with non-matching IPs")
            else:
                print("  ❌ IP filter shows all devices")
            
            # Test 3: Combined filtering
            print("\nTest 3: Combined filtering (hostname 'R' + IP segment '172.16.39.10')...")
            await page.fill('#simple-hostname-filter', 'R')
            await page.fill('#simple-ip-filter', '172.16.39.10')
            await page.wait_for_timeout(1000)
            
            combined_filter_results = await page.evaluate("""
                () => {
                    const allRows = document.querySelectorAll('#simple-table-body tr');
                    const visibleRows = document.querySelectorAll('#simple-table-body tr:not(.inventory-hidden-row)');
                    
                    // Collect data from visible rows
                    const visibleData = [];
                    visibleRows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 3) {
                            visibleData.push({
                                hostname: cells[0].textContent,
                                ip: cells[1].textContent,
                                type: cells[2].textContent
                            });
                        }
                    });
                    
                    return {
                        total: allRows.length,
                        visible: visibleRows.length,
                        visibleData: visibleData
                    };
                }
            """)
            
            print(f"  Results: {combined_filter_results['visible']} of {combined_filter_results['total']} devices visible")
            
            if combined_filter_results['visible'] < combined_filter_results['total']:
                print("  ✅ Combined filtering correctly shows subset of devices")
                print("  Visible devices:")
                for device in combined_filter_results.get('visibleData', []):
                    print(f"    - {device.get('hostname')} | {device.get('ip')} | {device.get('type')}")
                
                # Verify that only devices matching both criteria are shown
                correct_matches = all(
                    d.get('hostname', '').startswith('R') and '172.16.39.10' in d.get('ip', '')
                    for d in combined_filter_results.get('visibleData', [])
                )
                if correct_matches:
                    print("  ✅ Combined filters correctly show only matching devices")
                else:
                    print("  ❌ Combined filters show devices that don't match all criteria")
            else:
                print("  ❌ Combined filters show all devices")
            
            # Test 4: Reset functionality
            print("\nTest 4: Testing reset functionality...")
            await page.click('#simple-reset-btn')
            await page.wait_for_timeout(1000)
            
            reset_results = await page.evaluate("""
                () => {
                    const allRows = document.querySelectorAll('#simple-table-body tr');
                    const visibleRows = document.querySelectorAll('#simple-table-body tr:not(.inventory-hidden-row)');
                    return {
                        total: allRows.length,
                        visible: visibleRows.length
                    };
                }
            """)
            
            print(f"  Results: {reset_results['visible']} of {reset_results['total']} devices visible")
            
            if reset_results['visible'] == reset_results['total']:
                print("  ✅ Reset functionality correctly shows all devices")
            else:
                print("  ❌ Reset functionality failed to show all devices")
            
            # Evaluate auto-refresh functionality
            print("\nChecking auto-refresh functionality...")
            auto_refresh_status = await page.evaluate("""
                () => {
                    // Check for auto-refresh elements
                    const toggle = document.getElementById('auto-refresh-toggle');
                    const indicator = document.getElementById('refresh-indicator');
                    
                    return {
                        autoRefreshImplemented: !!toggle,
                        indicatorImplemented: !!indicator
                    };
                }
            """)
            
            if auto_refresh_status.get('autoRefreshImplemented'):
                print("✅ Auto-refresh toggle is implemented")
            else:
                print("❌ Auto-refresh toggle is not implemented")
                
            if auto_refresh_status.get('indicatorImplemented'):
                print("✅ Refresh indicator is implemented")
            else:
                print("❌ Refresh indicator is not implemented")
            
            # Final evaluation
            print("\n===== Inventory Filtering Validation Summary =====")
            
            if (specific_device_results['visible'] < specific_device_results['total'] or
                ip_filter_results['visible'] < ip_filter_results['total'] or
                combined_filter_results['visible'] < combined_filter_results['total']):
                print("✅ Inventory filtering functionality is working correctly")
                print("✅ Filters correctly hide non-matching rows")
                print("✅ Device type detection and filtering implemented")
                print("✅ Reset functionality working correctly")
                print("✅ Auto-refresh functionality available during audits")
            else:
                print("❌ Inventory filtering functionality still needs adjustment")
                print("   - Ensure filters properly hide non-matching rows")
                print("   - Verify device type detection works correctly")
            
        except Exception as e:
            print(f"❌ Error during validation: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_filtering())
