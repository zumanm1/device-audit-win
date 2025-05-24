#!/usr/bin/env python3
"""
Test script for the new inventory filtering functionality in NetAuditPro.

This script tests the ability to filter the CSV inventory by hostname, IP address,
and device type, ensuring that users can quickly find specific devices.
"""

import os
import time
from playwright.sync_api import sync_playwright, expect

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "inventory_filter_screenshots"

def setup():
    """Set up test environment"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"Screenshots will be saved to {SCREENSHOT_DIR}")

def test_inventory_filtering():
    """Test the inventory filtering functionality"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            print("\n===== Testing Inventory Filtering =====")
            
            # Navigate to inventory management page
            print("Navigating to inventory management page...")
            page.goto(f"{APP_URL}/manage_inventories")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_page.png")
            
            # Check filter UI elements
            print("\nChecking filter UI elements...")
            filter_form = page.query_selector("#inventory-filter-form")
            if not filter_form:
                print("❌ Filter form not found")
                return False
            
            hostname_filter = page.query_selector("#hostname-filter")
            ip_filter = page.query_selector("#ip-filter")
            device_type_filter = page.query_selector("#device-type-filter")
            apply_button = page.query_selector("#apply-filters")
            reset_button = page.query_selector("#reset-filters")
            
            if all([hostname_filter, ip_filter, device_type_filter, apply_button, reset_button]):
                print("✅ All filter UI elements found")
            else:
                print("❌ Some filter UI elements are missing")
                missing = []
                if not hostname_filter: missing.append("hostname-filter")
                if not ip_filter: missing.append("ip-filter")
                if not device_type_filter: missing.append("device-type-filter")
                if not apply_button: missing.append("apply-filters")
                if not reset_button: missing.append("reset-filters")
                print(f"   Missing elements: {', '.join(missing)}")
                return False
            
            # Count total devices in inventory
            table = page.query_selector("#csvTable")
            if not table:
                print("❌ Inventory table not found")
                return False
            
            rows = page.query_selector_all("#csvTableBody tr")
            total_devices = len(rows)
            print(f"Total devices in inventory: {total_devices}")
            
            # Test hostname filtering
            print("\nTesting hostname filtering...")
            hostname_filter.fill("R")  # Filter for routers starting with R
            apply_button.click()
            page.wait_for_timeout(1000)  # Wait for filtering to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/02_hostname_filter.png")
            
            # Check filter results
            filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            hostname_filtered_count = len(filtered_rows)
            print(f"Devices matching hostname filter 'R': {hostname_filtered_count}")
            
            # Check results count display
            results_count = page.query_selector("#filter-results-count")
            if results_count:
                count_text = results_count.inner_text()
                print(f"Results count display: {count_text}")
                if f"Showing {hostname_filtered_count} of {total_devices}" in count_text:
                    print("✅ Results count display is accurate")
                else:
                    print(f"❌ Results count display is inaccurate: {count_text}")
            
            # Reset filters
            print("\nTesting filter reset...")
            reset_button.click()
            page.wait_for_timeout(1000)  # Wait for reset to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/03_filter_reset.png")
            
            # Check that all rows are visible again
            visible_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            reset_count = len(visible_rows)
            print(f"Visible rows after reset: {reset_count}")
            if reset_count == total_devices:
                print("✅ Filter reset working correctly")
            else:
                print(f"❌ Filter reset not working correctly. Expected {total_devices}, got {reset_count}")
            
            # Test IP filtering
            print("\nTesting IP address filtering...")
            ip_filter.fill("192.168")  # Filter for IPs containing 192.168
            apply_button.click()
            page.wait_for_timeout(1000)  # Wait for filtering to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/04_ip_filter.png")
            
            # Check filter results
            filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            ip_filtered_count = len(filtered_rows)
            print(f"Devices matching IP filter '192.168': {ip_filtered_count}")
            
            # Reset filters
            reset_button.click()
            page.wait_for_timeout(1000)  # Wait for reset to complete
            
            # Test device type filtering
            print("\nTesting device type filtering...")
            # First, check that the dropdown has been populated with values
            options = page.query_selector_all("#device-type-filter option")
            print(f"Device type filter has {len(options)} options:")
            for option in options:
                print(f"  - {option.inner_text()}")
            
            # Select a device type (if available)
            if len(options) > 1:
                page.select_option("#device-type-filter", value=options[1].get_attribute("value"))
                apply_button.click()
                page.wait_for_timeout(1000)  # Wait for filtering to complete
                page.screenshot(path=f"{SCREENSHOT_DIR}/05_device_type_filter.png")
                
                # Check filter results
                filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
                device_type_filtered_count = len(filtered_rows)
                print(f"Devices matching selected device type: {device_type_filtered_count}")
            
            # Test combined filtering
            print("\nTesting combined filtering...")
            reset_button.click()
            page.wait_for_timeout(1000)  # Wait for reset to complete
            
            # Apply multiple filters
            hostname_filter.fill("R")
            if len(options) > 1:
                page.select_option("#device-type-filter", value=options[1].get_attribute("value"))
            apply_button.click()
            page.wait_for_timeout(1000)  # Wait for filtering to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/06_combined_filter.png")
            
            # Check filter results
            filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            combined_filtered_count = len(filtered_rows)
            print(f"Devices matching combined filters: {combined_filtered_count}")
            
            print("\n✅ Inventory filtering test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error during inventory filtering test: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    setup()
    test_inventory_filtering()
