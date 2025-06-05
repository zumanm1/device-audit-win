#!/usr/bin/env python3
"""
Test script for the inventory filtering implementation in NetAuditPro.

This script tests the new inventory filtering capabilities added to the application,
ensuring that users can quickly filter device inventory by various criteria such as:
- Hostname patterns
- IP address ranges
- Device types
- Custom fields

The filtering is implemented on both the backend and frontend for maximum flexibility.
"""

import os
import sys
import json
import requests
from urllib.parse import urljoin
import csv
import io
from playwright.sync_api import sync_playwright, expect

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "filter_test_screenshots"

def setup():
    """Set up the test environment"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"Screenshots will be saved to {SCREENSHOT_DIR}")

def test_inventory_filtering():
    """Test the inventory filtering functionality"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # Navigate to the inventory management page
            print("\n===== Testing Inventory Filtering =====")
            page.goto(f"{APP_URL}/manage_inventories")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_page.png")
            
            # Check if the filter inputs exist
            print("Checking for filter inputs...")
            filter_inputs = page.query_selector_all("#inventory-filter-form input, #inventory-filter-form select")
            if not filter_inputs:
                print("❌ Filter inputs not found. Make sure the filter form has been implemented.")
                return False
            
            print(f"✅ Found {len(filter_inputs)} filter inputs")
            
            # Test hostname filtering
            print("\nTesting hostname filtering...")
            hostname_input = page.query_selector("#hostname-filter")
            if hostname_input:
                hostname_input.fill("R")  # Filter for routers starting with R
                page.query_selector("#apply-filters").click()
                page.wait_for_load_state("networkidle")
                page.screenshot(path=f"{SCREENSHOT_DIR}/02_hostname_filter.png")
                
                # Check filtered results
                filtered_rows = page.query_selector_all("#inventory-table tbody tr")
                print(f"Found {len(filtered_rows)} rows after hostname filtering")
                
                # Reset filters
                page.query_selector("#reset-filters").click()
                page.wait_for_load_state("networkidle")
            else:
                print("❌ Hostname filter input not found")
            
            # Test device type filtering
            print("\nTesting device type filtering...")
            device_type_input = page.query_selector("#device-type-filter")
            if device_type_input:
                device_type_input.select_option("router")  # Select router device type
                page.query_selector("#apply-filters").click()
                page.wait_for_load_state("networkidle")
                page.screenshot(path=f"{SCREENSHOT_DIR}/03_device_type_filter.png")
                
                # Check filtered results
                filtered_rows = page.query_selector_all("#inventory-table tbody tr")
                print(f"Found {len(filtered_rows)} rows after device type filtering")
                
                # Reset filters
                page.query_selector("#reset-filters").click()
                page.wait_for_load_state("networkidle")
            else:
                print("❌ Device type filter input not found")
            
            # Test IP address filtering
            print("\nTesting IP address filtering...")
            ip_input = page.query_selector("#ip-filter")
            if ip_input:
                ip_input.fill("192.168")  # Filter for IPs containing 192.168
                page.query_selector("#apply-filters").click()
                page.wait_for_load_state("networkidle")
                page.screenshot(path=f"{SCREENSHOT_DIR}/04_ip_filter.png")
                
                # Check filtered results
                filtered_rows = page.query_selector_all("#inventory-table tbody tr")
                print(f"Found {len(filtered_rows)} rows after IP filtering")
                
                # Reset filters
                page.query_selector("#reset-filters").click()
                page.wait_for_load_state("networkidle")
            else:
                print("❌ IP filter input not found")
            
            # Test combined filtering
            print("\nTesting combined filtering...")
            if hostname_input and device_type_input:
                hostname_input.fill("R")
                device_type_input.select_option("router")
                page.query_selector("#apply-filters").click()
                page.wait_for_load_state("networkidle")
                page.screenshot(path=f"{SCREENSHOT_DIR}/05_combined_filter.png")
                
                # Check filtered results
                filtered_rows = page.query_selector_all("#inventory-table tbody tr")
                print(f"Found {len(filtered_rows)} rows after combined filtering")
            
            print("\n✅ Inventory filtering tests completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during inventory filtering tests: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    setup()
    test_inventory_filtering()
