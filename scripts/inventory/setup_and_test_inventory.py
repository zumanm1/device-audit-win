#!/usr/bin/env python3
"""
Set up and test inventory filtering functionality in NetAuditPro.

This script:
1. Sets up a sample inventory file
2. Configures it as the active inventory
3. Tests the filtering functionality
"""

import os
import time
import requests
import json
from playwright.sync_api import sync_playwright, expect

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "inventory_filter_screenshots"
SAMPLE_INVENTORY_PATH = "/root/za-con/inventories/sample-inventory.csv"

def setup():
    """Set up test environment"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"Screenshots will be saved to {SCREENSHOT_DIR}")

def create_sample_inventory():
    """Create a sample inventory file if it doesn't exist"""
    if not os.path.exists(SAMPLE_INVENTORY_PATH):
        print(f"Creating sample inventory at {SAMPLE_INVENTORY_PATH}")
        sample_data = """hostname,ip,device_type,username,password,port,enable_secret
R1,192.168.1.1,router,admin,cisco123,22,cisco123
R2,192.168.1.2,router,admin,cisco123,22,cisco123
R3,192.168.1.3,router,admin,cisco123,22,cisco123
SW1,192.168.2.1,switch,admin,cisco123,22,cisco123
SW2,192.168.2.2,switch,admin,cisco123,22,cisco123
FW1,10.0.0.1,firewall,admin,cisco123,22,cisco123"""
        
        try:
            os.makedirs(os.path.dirname(SAMPLE_INVENTORY_PATH), exist_ok=True)
            with open(SAMPLE_INVENTORY_PATH, 'w') as f:
                f.write(sample_data)
            print("✅ Sample inventory created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating sample inventory: {e}")
            return False
    else:
        print(f"Sample inventory already exists at {SAMPLE_INVENTORY_PATH}")
        return True

def test_inventory_filtering():
    """Test the inventory filtering functionality"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # First, let's try to set our sample inventory as active using the web interface
            print("\n===== Setting Sample Inventory as Active =====")
            page.goto(f"{APP_URL}/manage_inventories")
            page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the inventory management page
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_management.png")
            
            # Look for our sample inventory in the dropdown
            inventory_dropdown = page.query_selector("#active_inventory_file_manage")
            
            if inventory_dropdown:
                # See if our sample-inventory.csv is in the options
                sample_inventory_filename = os.path.basename(SAMPLE_INVENTORY_PATH)
                options = page.query_selector_all("#active_inventory_file_manage option")
                
                sample_inventory_found = False
                for option in options:
                    if sample_inventory_filename in option.inner_text():
                        sample_inventory_found = True
                        print(f"✅ Found {sample_inventory_filename} in the dropdown")
                        
                        # Select our sample inventory
                        page.select_option("#active_inventory_file_manage", value=sample_inventory_filename)
                        
                        # Click the "Set as Active" button
                        set_active_button = page.query_selector('button:has-text("Set as Active")')
                        if set_active_button:
                            set_active_button.click()
                            page.wait_for_load_state("networkidle")
                            print("✅ Set sample inventory as active")
                        else:
                            print("❌ Set as Active button not found")
                        
                        break
                
                if not sample_inventory_found:
                    print(f"❌ Sample inventory '{sample_inventory_filename}' not found in dropdown")
                    print("Available inventories:")
                    for option in options:
                        print(f"  - {option.inner_text()}")
                        
                    # Upload the sample inventory
                    print("Attempting to upload sample inventory...")
                    # We'll need to navigate back to the inventory page after the refresh
                    page.goto(f"{APP_URL}/manage_inventories")
                    page.wait_for_load_state("networkidle")
                    
                    # Check if there's an upload form
                    upload_form = page.query_selector('form[enctype="multipart/form-data"]')
                    if upload_form:
                        print("✅ Found upload form")
                        # We can't directly upload a file using Playwright in this environment
                        # Instead, let's create an inventory and set it active in the inventory tab
                        print("Will test with existing inventory files")
                    else:
                        print("❌ Upload form not found")
            else:
                print("❌ Inventory dropdown not found")
            
            # Now test the inventory filtering
            print("\n===== Testing Inventory Filtering =====")
            
            # Navigate to inventory management page (Raw CSV tab)
            page.goto(f"{APP_URL}/manage_inventories")
            page.wait_for_load_state("networkidle")
            
            # Switch to the table view tab which has our filtering UI
            raw_tab = page.query_selector('#raw-tab')
            if raw_tab:
                raw_tab.click()
                page.wait_for_timeout(1000)  # Wait for tab to show
                
                # Now switch back to the table view
                table_tab = page.query_selector('#csv-tab')
                if table_tab:
                    table_tab.click()
                    page.wait_for_timeout(1000)  # Wait for tab to show
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/02_inventory_table.png")
            
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
            
            tbody = page.query_selector("#csvTableBody")
            if not tbody:
                print("❌ Table body not found")
                return False
                
            rows = page.query_selector_all("#csvTableBody tr")
            total_devices = len(rows)
            print(f"Total devices in inventory: {total_devices}")
            
            if total_devices == 0:
                print("❌ No devices found in the inventory table")
                print("Checking raw inventory content...")
                raw_tab = page.query_selector('#raw-tab')
                if raw_tab:
                    raw_tab.click()
                    page.wait_for_timeout(1000)  # Wait for tab to show
                    raw_content = page.query_selector('#raw_inventory_content_edit')
                    if raw_content:
                        content = raw_content.inner_text()
                        print(f"Raw inventory content: {content[:100]}...")
                    else:
                        print("❌ Raw inventory content element not found")
                else:
                    print("❌ Raw tab not found")
                return False
            
            # Test hostname filtering
            print("\nTesting hostname filtering...")
            hostname_filter.fill("R")  # Filter for routers starting with R
            apply_button.click()
            page.wait_for_timeout(1000)  # Wait for filtering to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/03_hostname_filter.png")
            
            # Check filter results
            filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            hostname_filtered_count = len(filtered_rows)
            print(f"Devices matching hostname filter 'R': {hostname_filtered_count}")
            
            # Check results count display
            results_count = page.query_selector("#filter-results-count")
            if results_count:
                count_text = results_count.inner_text()
                print(f"Results count display: {count_text}")
                expected_text = f"Showing {hostname_filtered_count} of {total_devices}"
                if expected_text in count_text:
                    print("✅ Results count display is accurate")
                else:
                    print(f"❌ Results count display is inaccurate. Expected '{expected_text}', got '{count_text}'")
            
            # Reset filters
            print("\nTesting filter reset...")
            reset_button.click()
            page.wait_for_timeout(1000)  # Wait for reset to complete
            page.screenshot(path=f"{SCREENSHOT_DIR}/04_filter_reset.png")
            
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
            page.screenshot(path=f"{SCREENSHOT_DIR}/05_ip_filter.png")
            
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
                page.screenshot(path=f"{SCREENSHOT_DIR}/06_device_type_filter.png")
                
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
            page.screenshot(path=f"{SCREENSHOT_DIR}/07_combined_filter.png")
            
            # Check filter results
            filtered_rows = page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
            combined_filtered_count = len(filtered_rows)
            print(f"Devices matching combined filters: {combined_filtered_count}")
            
            print("\n✅ Inventory filtering test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during inventory filtering test: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    setup()
    create_sample_inventory()
    test_inventory_filtering()
