#!/usr/bin/env python3
"""
Script to diagnose and fix the inventory display issue in NetAuditPro.

This script:
1. Analyzes the current inventory data structure
2. Checks the JavaScript console for errors 
3. Tests the inventory filtering functionality with direct DOM manipulation
"""

import os
import time
import asyncio
from playwright.async_api import async_playwright, expect

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "inventory_debug"

# Create screenshot directory
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def test_inventory_display():
    """Test and fix the inventory display in the web UI"""
    async with async_playwright() as p:
        # Launch browser with DevTools enabled to capture console logs
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        
        # Create a page and set up console log capture
        page = await context.new_page()
        console_logs = []
        
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        
        try:
            print("\n===== Testing Inventory Display =====")
            
            # Navigate to inventory management page
            print("Navigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_inventory_page.png")
            
            # Check the raw CSV view first
            print("\nExamining raw CSV content...")
            raw_tab = await page.query_selector('#raw-tab')
            if raw_tab:
                await raw_tab.click()
                await page.wait_for_timeout(1000)
                
                raw_content = await page.query_selector('#raw_inventory_content_edit')
                if raw_content:
                    content = await raw_content.inner_text()
                    if content:
                        print(f"✅ Raw CSV content found: {len(content)} characters")
                        first_few_lines = content.split('\n')[:3]
                        print(f"First few lines:")
                        for line in first_few_lines:
                            print(f"  {line}")
                        
                        # Switch back to table view
                        table_tab = await page.query_selector('#csv-tab')
                        if table_tab:
                            await table_tab.click()
                            await page.wait_for_timeout(1000)
                        
                        # Check for console errors
                        print("\nChecking browser console logs...")
                        errors = [log for log in console_logs if 'error' in log.lower()]
                        if errors:
                            print(f"❌ Found {len(errors)} console errors:")
                            for error in errors[:5]:  # Show the first 5 errors
                                print(f"  - {error}")
                        else:
                            print("✅ No console errors found")
                        
                        # Inject JavaScript to fix the table display
                        print("\nInjecting JavaScript to diagnose CSV parsing...")
                        # First, try to get the raw CSV content
                        raw_csv = await page.evaluate("""() => {
                            const textarea = document.getElementById('raw_inventory_content_edit');
                            return textarea ? textarea.value : null;
                        }""")
                        
                        if raw_csv:
                            print(f"✅ Retrieved raw CSV content via JavaScript: {len(raw_csv)} characters")
                            
                            # Try to parse and display the CSV data using our enhanced functions
                            await page.evaluate("""(csvContent) => {
                                console.clear();
                                console.log("Manual CSV parsing test");
                                
                                // Get the raw CSV content
                                const csvString = csvContent;
                                console.log(`CSV string length: ${csvString.length}`);
                                
                                // Parse CSV manually
                                const lines = csvString.trim().split('\\n');
                                console.log(`CSV contains ${lines.length} lines`);
                                
                                if (lines.length > 0) {
                                    // Get headers
                                    const headers = lines[0].split(',');
                                    console.log(`Headers: ${headers.join(', ')}`);
                                    
                                    // Create data array
                                    const data = [];
                                    data.push(headers);
                                    
                                    // Process data rows
                                    for (let i = 1; i < lines.length; i++) {
                                        const row = lines[i].split(',');
                                        if (row.length > 0) {
                                            data.push(row);
                                        }
                                    }
                                    
                                    console.log(`Parsed ${data.length} rows`);
                                    
                                    // Clear table
                                    const tableHeader = document.getElementById('csvTableHeader');
                                    const tableBody = document.getElementById('csvTableBody');
                                    
                                    if (tableHeader && tableBody) {
                                        tableHeader.innerHTML = '';
                                        tableBody.innerHTML = '';
                                        
                                        // Create header row
                                        let headerRow = document.createElement('tr');
                                        for (let i = 0; i < headers.length; i++) {
                                            let th = document.createElement('th');
                                            th.contentEditable = "true";
                                            th.textContent = headers[i];
                                            headerRow.appendChild(th);
                                        }
                                        tableHeader.appendChild(headerRow);
                                        
                                        // Create data rows
                                        for (let i = 1; i < data.length; i++) {
                                            let tr = document.createElement('tr');
                                            for (let j = 0; j < data[i].length; j++) {
                                                let td = document.createElement('td');
                                                td.contentEditable = "true";
                                                td.textContent = data[i][j] || '';
                                                
                                                // Add special classes for filter-targeted columns
                                                if (headers[j] === 'hostname') {
                                                    td.classList.add('hostname-cell');
                                                } else if (headers[j] === 'ip') {
                                                    td.classList.add('ip-cell');
                                                } else if (headers[j] === 'device_type') {
                                                    td.classList.add('device-type-cell');
                                                }
                                                
                                                tr.appendChild(td);
                                            }
                                            
                                            // Add delete row button
                                            let deleteCell = document.createElement('td');
                                            let deleteBtn = document.createElement('button');
                                            deleteBtn.className = "btn btn-sm btn-danger";
                                            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                                            deleteBtn.addEventListener('click', function() {
                                                tr.remove();
                                            });
                                            deleteCell.appendChild(deleteBtn);
                                            tr.appendChild(deleteCell);
                                            
                                            tableBody.appendChild(tr);
                                        }
                                        
                                        console.log("Table populated successfully");
                                        
                                        // Initialize filters
                                        if (typeof initializeInventoryFiltering === 'function') {
                                            console.log("Initializing inventory filtering");
                                            initializeInventoryFiltering();
                                        } else {
                                            console.log("initializeInventoryFiltering function not found");
                                        }
                                        
                                        return `Successfully populated table with ${data.length-1} rows`;
                                    } else {
                                        return "Table header or body not found";
                                    }
                                } else {
                                    return "No CSV lines found";
                                }
                            }""", raw_csv)
                            
                            # Take a screenshot after our manual intervention
                            await page.wait_for_timeout(1000)
                            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_after_js_fix.png")
                            
                            # Now test the filtering functionality
                            print("\nTesting inventory filtering after fix...")
                            
                            # Check filter UI elements
                            filter_form = await page.query_selector("#inventory-filter-form")
                            if filter_form:
                                print("✅ Filter form found")
                                
                                # Count total devices in inventory
                                rows = await page.query_selector_all("#csvTableBody tr")
                                total_devices = len(rows)
                                print(f"Total devices in inventory after fix: {total_devices}")
                                
                                if total_devices > 0:
                                    # Test hostname filtering
                                    hostname_filter = await page.query_selector("#hostname-filter")
                                    apply_button = await page.query_selector("#apply-filters")
                                    
                                    if hostname_filter and apply_button:
                                        await hostname_filter.fill("R")  # Filter for routers
                                        await apply_button.click()
                                        await page.wait_for_timeout(1000)
                                        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_hostname_filter.png")
                                        
                                        # Check filtered results
                                        visible_rows = await page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
                                        filtered_count = len(visible_rows)
                                        print(f"Devices matching hostname filter 'R': {filtered_count}")
                                        
                                        # Test filter reset
                                        reset_button = await page.query_selector("#reset-filters")
                                        if reset_button:
                                            await reset_button.click()
                                            await page.wait_for_timeout(1000)
                                            
                                            # Verify all rows are visible again
                                            visible_rows = await page.query_selector_all("#csvTableBody tr:not([style*='display: none'])")
                                            reset_count = len(visible_rows)
                                            if reset_count == total_devices:
                                                print(f"✅ Filter reset working correctly, showing all {reset_count} devices")
                                            else:
                                                print(f"❌ Filter reset not working correctly. Expected {total_devices}, got {reset_count}")
                                    else:
                                        print("❌ Filter controls not found")
                            else:
                                print("❌ Filter form not found")
                    else:
                        print("❌ Raw CSV content is empty")
                else:
                    print("❌ Raw CSV content element not found")
            else:
                print("❌ Raw tab not found")
            
            print("\n===== Recommendations =====")
            print("1. Update the parseCSV function to handle the raw CSV content correctly")
            print("2. Fix the escape sequences for newlines (\\n vs \\\\n)")
            print("3. Ensure populateCSVTable correctly processes the parsed data")
            
            return True
        except Exception as e:
            print(f"❌ Error during inventory display test: {e}")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            await browser.close()

async def main():
    await test_inventory_display()

if __name__ == "__main__":
    asyncio.run(main())
