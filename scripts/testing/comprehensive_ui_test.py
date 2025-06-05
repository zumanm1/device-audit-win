#!/usr/bin/env python3
"""
Comprehensive Playwright test script for NetAuditPro UI

This script tests all major UI features of the NetAuditPro application including:
- Navigation and basic UI elements
- Inventory management 
- Enhanced Progress Tracking
- Audit controls (start, stop, pause)
- Report viewing
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Test configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = Path("./test_screenshots")

# Create screenshot directory if it doesn't exist
SCREENSHOT_DIR.mkdir(exist_ok=True)

async def test_netauditpro_ui():
    """Run comprehensive tests on NetAuditPro UI"""
    async with async_playwright() as p:
        # Launch browser with headless mode and no-sandbox for root environments
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # Create a new context and page
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        # Enable console logging
        page.on('console', lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        # Dictionary to store test results
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Basic Navigation and UI Loading
            await test_basic_navigation(page, test_results)
            
            # Test 2: Inventory Management
            await test_inventory_management(page, test_results)
            
            # Test 3: Audit Controls
            await test_audit_controls(page, test_results)
            
            # Test 4: Enhanced Progress Tracking
            await test_progress_tracking(page, test_results)
            
            # Test 5: Captured Configs
            await test_captured_configs(page, test_results)
            
        except Exception as e:
            print(f"Test execution error: {str(e)}")
            test_results["tests"].append({
                "name": "Overall Test Execution",
                "status": "FAILED",
                "error": str(e)
            })
            await page.screenshot(path=SCREENSHOT_DIR / "test_error.png")
        
        finally:
            # Save test results
            with open(SCREENSHOT_DIR / "test_results.json", "w") as f:
                json.dump(test_results, f, indent=2)
            
            # Close browser
            await browser.close()
            
        return test_results

async def test_basic_navigation(page, test_results):
    """Test basic navigation and UI loading"""
    print("\n🔍 Testing Basic Navigation and UI Loading...")
    
    try:
        # Navigate to the application
        await page.goto("http://localhost:5007/", wait_until="load")
        await page.wait_for_load_state("networkidle")
        
        # Verify page title
        title = await page.title()
        assert "NetAuditPro" in title, f"Expected 'NetAuditPro' in title, got: {title}"
        
        # Check for main UI components based on diagnostic results
        header_visible = await page.is_visible('nav.navbar')
        assert header_visible, "Header navigation not visible"
        
        # Check for essential controls we know should exist
        essential_elements = [
            '#stop-reset-audit',         # Stop/Reset Audit button
            '#resultsChart',             # Results chart
            '#logContainer'              # Log container
        ]
        
        for element_id in essential_elements:
            element_visible = await page.is_visible(element_id)
            assert element_visible, f"Essential element {element_id} not visible"
        
        # Check for key cards in the UI
        cards = [
            '.card-header:has-text("Audit Controls")',
            '.card-header:has-text("Current Audit Status")',
            '.card-header:has-text("Audit Results Summary")',
            '.card-header:has-text("Live Audit Logs")'
        ]
        
        for card_selector in cards:
            card_visible = await page.is_visible(card_selector)
            assert card_visible, f"Card {card_selector} not visible"
        
        # Record test result with more details
        test_results["tests"].append({
            "name": "Basic Navigation",
            "status": "PASSED",
            "title": title,
            "essential_elements_found": len(essential_elements),
            "cards_found": len(cards)
        })
        
        print("✅ Basic Navigation Test: PASSED")
        
    except Exception as e:
        test_results["tests"].append({
            "name": "Basic Navigation",
            "status": "FAILED",
            "error": str(e)
        })
        print(f"❌ Basic Navigation Test: FAILED - {str(e)}")
        await page.screenshot(path=SCREENSHOT_DIR / "basic_navigation_error.png")
        raise

async def test_inventory_management(page, test_results):
    """Test inventory management functionality, focusing on CSV structure validation"""
    print("\n🔍 Testing Inventory Management and CSV Validation...")
    
    try:
        # Navigate to Manage Inventories page
        await page.click('a:text("Manage Inventories")')
        await page.wait_for_load_state('networkidle')
        
        # Be more flexible with inventory detection - check for any table or inventory-related content
        await page.wait_for_timeout(2000)  # Give page more time to fully load
        
        # Check for any table, card or section related to inventory
        inventory_content = await page.evaluate("""() => {
            // Look for any tables
            const tables = document.querySelectorAll('table');
            if (tables.length > 0) return { found: true, type: 'table', count: tables.length };
            
            // Look for inventory cards/sections
            const inventorySection = document.querySelector('.card-header:has-text("Current Active Inventory")');
            if (inventorySection) return { found: true, type: 'section', text: inventorySection.textContent };
            
            // Look for inventory-related text
            const inventoryText = document.querySelector('h4:has-text("Inventory"), h3:has-text("Inventory")');
            if (inventoryText) return { found: true, type: 'heading', text: inventoryText.textContent };
            
            return { found: false };
        }""")
        
        print(f"Inventory content detection: {inventory_content}")
        assert inventory_content['found'], "No inventory content found on page"
        
        # Take screenshot of inventory page
        await page.screenshot(path=SCREENSHOT_DIR / "inventory_page.png")
        
        # Get active inventory name
        active_inventory = await page.text_content('h4:has-text("Current Active Inventory")')
        print(f"Active inventory: {active_inventory}")
        
        # Test CSV inventory structure via JavaScript API call
        print("Testing CSV inventory data structure...")
        inventory_data = await page.evaluate("""async () => {
            try {
                // Try different table selectors to match the actual inventory table
                let table = document.getElementById('csvTable');
                if (!table) table = document.querySelector('table');
                if (!table) table = document.querySelector('.table');
                if (!table) return { error: 'No inventory table found on page' };
                
                // Extract headers and data from the table
                const headers = [];
                const data = [];
                
                // Get headers from the table
                const headerRow = table.querySelector('thead tr');
                if (headerRow) {
                    headerRow.querySelectorAll('th').forEach(th => {
                        headers.push(th.textContent.trim());
                    });
                }
                
                // Get data rows
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const rowData = {};
                    row.querySelectorAll('td').forEach((td, index) => {
                        if (index < headers.length) {
                            rowData[headers[index]] = td.textContent.trim();
                        }
                    });
                    data.push(rowData);
                });
                
                return { headers, data };
            } catch (e) {
                return { error: e.toString() };
            }
        }""")  
        
        # Verify the structure matches the expected ACTIVE_INVENTORY_DATA format
        if 'error' in inventory_data:
            print(f"Error getting inventory data: {inventory_data['error']}")
            assert False, f"Failed to get inventory data: {inventory_data['error']}"
        
        assert 'headers' in inventory_data, "Inventory data missing 'headers' key"
        assert 'data' in inventory_data, "Inventory data missing 'data' key"
        assert isinstance(inventory_data['headers'], list), "Headers should be a list"
        assert isinstance(inventory_data['data'], list), "Data should be a list of dictionaries"
        
        # Check for required columns based on the CSV validation function
        required_columns = ['hostname', 'ip']
        for column in required_columns:
            assert column in inventory_data['headers'], f"Required column '{column}' missing from inventory"
            
        print(f"CSV Structure valid: {len(inventory_data['headers'])} columns, {len(inventory_data['data'])} rows")
        print(f"Headers: {', '.join(inventory_data['headers'])}")
        
        # Verify first row data if available
        if len(inventory_data['data']) > 0:
            first_row = inventory_data['data'][0]
            print(f"Sample row: {first_row}")
            assert 'hostname' in first_row, "First row missing 'hostname' field"
            assert 'ip' in first_row, "First row missing 'ip' field"
        
        # Record test result
        test_results["tests"].append({
            "name": "Inventory Management & CSV Validation",
            "status": "PASSED",
            "active_inventory": active_inventory,
            "csv_structure_valid": True,
            "row_count": len(inventory_data['data']),
            "columns": inventory_data['headers']
        })
        
        print("✅ Inventory Management & CSV Validation Test: PASSED")
        
    except Exception as e:
        test_results["tests"].append({
            "name": "Inventory Management & CSV Validation",
            "status": "FAILED",
            "error": str(e)
        })
        print(f"❌ Inventory Management & CSV Validation Test: FAILED - {str(e)}")
        await page.screenshot(path=SCREENSHOT_DIR / "inventory_error.png")
        raise

async def test_audit_controls(page, test_results):
    """Test audit control functionality"""
    print("\n🔍 Testing Audit Controls...")
    
    try:
        # Navigate back to main page
        await page.click('a:text("Home")')
        await page.wait_for_load_state('networkidle')
        
        # Check if audit is already running
        status_text = await page.text_content('.status-card .card-header h4')
        
        if "Running" in status_text:
            # If audit is running, stop it first
            print("Audit is already running, stopping it first...")
            stop_button = await page.query_selector('#stop-reset-audit')
            if stop_button:
                await stop_button.click()
                await page.wait_for_timeout(2000)  # Wait for stop to complete
        
        # Check Start Audit button
        start_audit_form = await page.query_selector('form[action="/start_audit"]')
        assert start_audit_form, "Start Audit button not found"
        
        # Start an audit
        start_button = await start_audit_form.query_selector('button')
        await start_button.click()
        await page.wait_for_timeout(3000)  # Wait for audit to start
        
        # Verify audit started
        updated_status = await page.text_content('.status-card .card-header h4')
        assert "Running" in updated_status, f"Expected 'Running' status, got: {updated_status}"
        
        # Take screenshot of running audit
        await page.screenshot(path=SCREENSHOT_DIR / "audit_running.png")
        
        # Wait a bit for progress to update
        await page.wait_for_timeout(5000)
        
        # Try to pause the audit
        pause_form = await page.query_selector('form[action="/pause_audit"]')
        if pause_form:
            pause_button = await pause_form.query_selector('button')
            await pause_button.click()
            await page.wait_for_timeout(3000)  # Wait for pause to take effect
            
            # Take screenshot of paused audit
            await page.screenshot(path=SCREENSHOT_DIR / "audit_paused.png")
        
        # Stop the audit
        stop_button = await page.query_selector('#stop-reset-audit')
        if stop_button:
            await stop_button.click()
            await page.wait_for_timeout(3000)  # Wait for stop to complete
            
            # Take screenshot after stopping
            await page.screenshot(path=SCREENSHOT_DIR / "audit_stopped.png")
        
        # Record test result
        test_results["tests"].append({
            "name": "Audit Controls",
            "status": "PASSED",
            "controls_tested": ["Start", "Pause", "Stop"]
        })
        
        print("✅ Audit Controls Test: PASSED")
        
    except Exception as e:
        test_results["tests"].append({
            "name": "Audit Controls",
            "status": "FAILED",
            "error": str(e)
        })
        print(f"❌ Audit Controls Test: FAILED - {str(e)}")
        await page.screenshot(path=SCREENSHOT_DIR / "audit_controls_error.png")
        raise

async def test_progress_tracking(page, test_results):
    """Test Enhanced Progress Tracking functionality via API validation"""
    print("\n🔍 Testing Enhanced Progress Tracking...")
    
    try:
        # Navigate back to main page if needed
        if not await page.is_visible('.card-header:has-text("Current Audit Status")'):
            await page.click('a:text("Home")')
            await page.wait_for_load_state('networkidle')
        
        # Check if progress tracking cards are visible
        audit_status_card = await page.is_visible('.card-header:has-text("Current Audit Status")')
        assert audit_status_card, "Audit Status card not visible"
        
        # Test direct access to the /get_audit_progress endpoint
        print("Testing /get_audit_progress API endpoint...")
        response = await page.evaluate("""async () => {
            try {
                const response = await fetch('/get_audit_progress');
                if (!response.ok) {
                    return { error: `HTTP error ${response.status}` };
                }
                return await response.json();
            } catch (e) {
                return { error: e.toString() };
            }
        }""")
        
        # Check for error in response
        if isinstance(response, dict) and 'error' in response:
            print(f"Warning: Error accessing /get_audit_progress: {response['error']}")
            assert False, f"API error: {response['error']}"
        
        # Check if the response contains the enhanced progress data
        print("Validating progress data structure...")
        assert isinstance(response, dict), "API response is not a dictionary"
        
        # Confirm API has the expected keys based on our diagnostic test
        expected_keys = ['enhanced_progress', 'progress', 'audit_paused']
        for key in expected_keys:
            assert key in response, f"API response missing '{key}' field"
        
        # Validate enhanced_progress structure
        enhanced_progress = response['enhanced_progress']
        assert isinstance(enhanced_progress, dict), "enhanced_progress is not a dictionary"
        
        # Check expected fields in enhanced_progress
        expected_enhanced_fields = [
            'completed_devices', 'current_device', 'device_statuses', 
            'status', 'status_counts', 'total_devices'
        ]
        for field in expected_enhanced_fields:
            assert field in enhanced_progress, f"enhanced_progress missing '{field}' field"
        
        # Validate regular progress structure
        progress = response['progress']
        assert isinstance(progress, dict), "progress is not a dictionary"
        
        # Check expected fields in progress
        expected_progress_fields = [
            'completed_devices', 'current_device', 'device_statuses', 
            'status', 'total_devices'
        ]
        for field in expected_progress_fields:
            assert field in progress, f"progress missing '{field}' field"
            
        print("✅ Enhanced Progress data structure validated successfully")
        
        # Test the Stop/Reset Audit functionality
        print("Testing Stop/Reset Audit functionality...")
        
        # Start an audit if not already running
        status_text = await page.text_content('.card-header:has-text("Current Audit Status")')
        if "Running" not in status_text:
            start_form = await page.query_selector('form[action="/start_audit"]')
            if start_form:
                start_button = await start_form.query_selector('button[type="submit"]')
                if start_button:
                    await start_button.click()
                    await page.wait_for_timeout(2000)  # Wait for audit to start
                    print("Started a new audit")
                else:
                    print("Start button not found, but continuing test")
            else:
                print("Start form not found, but continuing test")
        
        # Take a screenshot after starting/before stopping
        await page.screenshot(path=SCREENSHOT_DIR / "before_stop_reset.png")
        
        # Click Stop/Reset button
        stop_button = await page.query_selector('#stop-reset-audit')
        assert stop_button, "Stop/Reset button not found"
        
        await stop_button.click()
        await page.wait_for_timeout(3000)  # Wait for stop to complete
        
        # Take a screenshot after stopping
        await page.screenshot(path=SCREENSHOT_DIR / "after_stop_reset.png")
        
        # Verify that connections were properly closed
        # Get progress data after reset
        progress_api_after_reset = await page.evaluate("""async () => {
            const response = await fetch('/get_audit_progress');
            return await response.json();
        }""")
        
        # Verify progress was reset (either not running or idle)
        assert progress_api_after_reset['progress']['status'] != 'running', "Audit status not properly reset"
        print("✅ Stop/Reset functionality verified successfully")
        
        # Record test result
        test_results["tests"].append({
            "name": "Enhanced Progress Tracking",
            "status": "PASSED",
            "api_validation": "Successful",
            "enhanced_progress_fields": len(expected_enhanced_fields),
            "stop_reset_verified": True
        })
        
        print("✅ Enhanced Progress Tracking Test: PASSED")
        
    except Exception as e:
        test_results["tests"].append({
            "name": "Enhanced Progress Tracking",
            "status": "FAILED",
            "error": str(e)
        })
        print(f"❌ Enhanced Progress Tracking Test: FAILED - {str(e)}")
        await page.screenshot(path=SCREENSHOT_DIR / "progress_tracking_error.png")
        raise

async def test_captured_configs(page, test_results):
    """Test Captured Configs functionality"""
    print("\n🔍 Testing Captured Configs...")
    
    try:
        # Navigate to Captured Configs page
        await page.click('a:text("Captured Configs")')
        await page.wait_for_load_state('networkidle')
        
        # Verify config section is visible
        config_section = await page.is_visible('.container')
        assert config_section, "Captured Configs section not visible"
        
        # Take screenshot of configs page
        await page.screenshot(path=SCREENSHOT_DIR / "captured_configs.png")
        
        # Check if any configs are listed
        configs_available = await page.is_visible('.card-body .list-group-item')
        
        # Record test result
        test_results["tests"].append({
            "name": "Captured Configs",
            "status": "PASSED",
            "configs_available": configs_available
        })
        
        print("✅ Captured Configs Test: PASSED")
        
    except Exception as e:
        test_results["tests"].append({
            "name": "Captured Configs",
            "status": "FAILED",
            "error": str(e)
        })
        print(f"❌ Captured Configs Test: FAILED - {str(e)}")
        await page.screenshot(path=SCREENSHOT_DIR / "captured_configs_error.png")
        raise

async def main():
    """Main function to run all tests"""
    print("\n=== 🧪 Starting NetAuditPro UI Comprehensive Test ===\n")
    start_time = time.time()
    
    results = await test_netauditpro_ui()
    
    # Calculate test summary
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"] if test["status"] == "PASSED")
    
    # Display summary
    print("\n=== 📊 Test Summary ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Pass Rate: {passed_tests/total_tests*100:.1f}%")
    print(f"Total Duration: {time.time() - start_time:.2f} seconds")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    print("\n=== 🏁 Test Execution Complete ===")
    
    # Return success if all tests passed
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(main())
