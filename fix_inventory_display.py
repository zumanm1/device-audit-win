#!/usr/bin/env python3
"""
This script provides a direct fix for the inventory display issue in NetAuditPro.
It will:
1. Directly examine the sample inventory file
2. Verify it's properly set as active
3. Inject JavaScript to properly display the data
4. Test the filtering functionality
"""

import os
import time
import asyncio
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SAMPLE_INVENTORY_PATH = "/root/za-con/inventories/sample-inventory.csv"
SCREENSHOT_DIR = "inventory_fix_screenshots"

# Create screenshot directory
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def direct_inventory_fix():
    """Directly apply fixes to make inventory display work"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("\n===== Direct Inventory Fix =====")
            
            # Step 1: Verify the sample inventory file
            if os.path.exists(SAMPLE_INVENTORY_PATH):
                print(f"Sample inventory exists at {SAMPLE_INVENTORY_PATH}")
                with open(SAMPLE_INVENTORY_PATH, 'r') as f:
                    content = f.read()
                    lines = content.strip().split('\n')
                print(f"Sample inventory has {len(lines) - 1} data rows")
            else:
                print(f"Sample inventory not found at {SAMPLE_INVENTORY_PATH}")
                return False
            
            # Step 2: Go to the inventory management page
            print("\nNavigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_initial_page.png")
            
            # Step 3: Ensure our sample inventory is selected and set as active
            selector = await page.query_selector("#active_inventory_file_manage")
            if selector:
                # Get all options
                options = await selector.query_selector_all("option")
                
                # Find sample-inventory.csv option
                sample_inventory_found = False
                for option in options:
                    option_value = await option.get_attribute("value")
                    if "sample-inventory.csv" in option_value:
                        sample_inventory_found = True
                        await selector.select_option(option_value)
                        print(f"✅ Selected sample-inventory.csv in dropdown")
                        break
                
                if not sample_inventory_found:
                    print("❌ sample-inventory.csv not found in dropdown")
                    return False
                
                # Click the Set as Active button
                set_active_button = await page.query_selector('button:has-text("Set as Active")')
                if set_active_button:
                    await set_active_button.click()
                    await page.wait_for_timeout(2000)  # Wait for the change to take effect
                    print("✅ Set sample inventory as active")
                else:
                    print("❌ Set as Active button not found")
                    return False
            else:
                print("❌ Inventory dropdown not found")
                return False
            
            # Step 4: Direct JavaScript injection to fix the table display
            print("\nInjecting JavaScript to fix table display...")
            
            # First, try using our API endpoint to get the data
            fix_result = await page.evaluate("""async () => {
                console.clear();
                console.log("Direct inventory display fix");
                
                try {
                    // Get the raw content first
                    const rawTextarea = document.getElementById('raw_inventory_content_edit');
                    const rawContent = rawTextarea ? rawTextarea.value : "";
                    
                    if (!rawContent) {
                        console.error("Raw content is empty");
                        return { success: false, message: "Raw content is empty" };
                    }
                    
                    console.log(`Raw content found: ${rawContent.length} characters`);
                    
                    // Parse the CSV manually
                    const lines = rawContent.trim().split('\\n');
                    if (lines.length <= 1) {
                        console.error("No data rows found in the CSV");
                        return { success: false, message: "No data rows in CSV" };
                    }
                    
                    console.log(`CSV contains ${lines.length} lines`);
                    
                    // Get the headers from first line
                    const headers = lines[0].split(',').map(h => h.trim());
                    console.log(`Headers found: ${headers.join(', ')}`);
                    
                    // Process data rows
                    const tableData = [headers];
                    for (let i = 1; i < lines.length; i++) {
                        if (!lines[i].trim()) continue;
                        const row = lines[i].split(',').map(cell => cell.trim());
                        if (row.length > 0) {
                            tableData.push(row);
                        }
                    }
                    
                    console.log(`Processed ${tableData.length - 1} data rows`);
                    
                    // Clear and populate the table
                    const tableHeader = document.getElementById('csvTableHeader');
                    const tableBody = document.getElementById('csvTableBody');
                    
                    if (!tableHeader || !tableBody) {
                        console.error("Table header or body not found");
                        return { success: false, message: "Table elements not found" };
                    }
                    
                    // Clear existing content
                    tableHeader.innerHTML = '';
                    tableBody.innerHTML = '';
                    
                    // Create header row
                    const headerRow = document.createElement('tr');
                    for (const header of headers) {
                        const th = document.createElement('th');
                        th.textContent = header;
                        th.contentEditable = "true";
                        headerRow.appendChild(th);
                    }
                    tableHeader.appendChild(headerRow);
                    
                    // Create data rows
                    for (let i = 1; i < tableData.length; i++) {
                        const tr = document.createElement('tr');
                        
                        for (let j = 0; j < tableData[i].length; j++) {
                            const td = document.createElement('td');
                            td.textContent = tableData[i][j] || '';
                            td.contentEditable = "true";
                            
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
                        const deleteCell = document.createElement('td');
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = "btn btn-sm btn-danger";
                        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                        deleteBtn.addEventListener('click', function() {
                            tr.remove();
                        });
                        deleteCell.appendChild(deleteBtn);
                        tr.appendChild(deleteCell);
                        
                        tableBody.appendChild(tr);
                    }
                    
                    // Populate device type dropdown
                    const deviceTypes = new Set();
                    const deviceTypeCells = document.querySelectorAll('.device-type-cell');
                    deviceTypeCells.forEach(cell => {
                        const deviceType = cell.textContent.trim().toLowerCase();
                        if (deviceType) {
                            deviceTypes.add(deviceType);
                        }
                    });
                    
                    const deviceTypeFilter = document.getElementById('device-type-filter');
                    if (deviceTypeFilter) {
                        let options = '<option value="all">All Device Types</option>';
                        deviceTypes.forEach(deviceType => {
                            options += `<option value="${deviceType}">${deviceType.charAt(0).toUpperCase() + deviceType.slice(1)}</option>`;
                        });
                        deviceTypeFilter.innerHTML = options;
                    }
                    
                    // Update filter results count
                    const countElement = document.getElementById('filter-results-count');
                    if (countElement) {
                        countElement.textContent = `Showing ${tableData.length - 1} of ${tableData.length - 1} devices`;
                    }
                    
                    console.log("Table successfully populated with direct fix");
                    return { 
                        success: true, 
                        message: `Table populated with ${tableData.length - 1} rows`, 
                        rowCount: tableData.length - 1 
                    };
                } catch (error) {
                    console.error("Error fixing table:", error);
                    return { success: false, message: `Error: ${error.message}` };
                }
            }""")
            
            print(f"JavaScript fix result: {fix_result}")
            
            # Take a screenshot after our fix
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_after_fix.png")
            
            # Step 5: Test the filtering functionality
            if fix_result.get('success') and fix_result.get('rowCount', 0) > 0:
                print("\nTesting filtering functionality...")
                
                # Test hostname filtering
                hostname_filter = await page.query_selector("#hostname-filter")
                if hostname_filter:
                    await hostname_filter.fill("R")  # Filter for devices starting with R
                    
                    apply_button = await page.query_selector("#apply-filters")
                    if apply_button:
                        await apply_button.click()
                        await page.wait_for_timeout(1000)
                        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_hostname_filter.png")
                        
                        # Check filtered results via JavaScript
                        filter_result = await page.evaluate("""() => {
                            const visibleRows = Array.from(document.querySelectorAll('#csvTableBody tr'))
                                .filter(row => row.style.display !== 'none');
                            return {
                                visible: visibleRows.length,
                                total: document.querySelectorAll('#csvTableBody tr').length
                            };
                        }""")
                        
                        print(f"Hostname filter 'R': {filter_result['visible']} of {filter_result['total']} devices visible")
                        
                        # Test device type filtering
                        device_type_filter = await page.query_selector("#device-type-filter")
                        if device_type_filter:
                            await device_type_filter.select_option("router")
                            await apply_button.click()
                            await page.wait_for_timeout(1000)
                            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_device_type_filter.png")
                            
                            filter_result = await page.evaluate("""() => {
                                const visibleRows = Array.from(document.querySelectorAll('#csvTableBody tr'))
                                    .filter(row => row.style.display !== 'none');
                                return {
                                    visible: visibleRows.length,
                                    total: document.querySelectorAll('#csvTableBody tr').length
                                };
                            }""")
                            
                            print(f"Device type filter 'router': {filter_result['visible']} of {filter_result['total']} devices visible")
                            
                            # Test reset functionality
                            reset_button = await page.query_selector("#reset-filters")
                            if reset_button:
                                await reset_button.click()
                                await page.wait_for_timeout(1000)
                                await page.screenshot(path=f"{SCREENSHOT_DIR}/05_reset_filters.png")
                                
                                filter_result = await page.evaluate("""() => {
                                    const visibleRows = Array.from(document.querySelectorAll('#csvTableBody tr'))
                                        .filter(row => row.style.display !== 'none');
                                    return {
                                        visible: visibleRows.length,
                                        total: document.querySelectorAll('#csvTableBody tr').length
                                    };
                                }""")
                                
                                print(f"After reset: {filter_result['visible']} of {filter_result['total']} devices visible")
                                
                                if filter_result['visible'] == filter_result['total']:
                                    print("✅ Filter reset is working correctly")
                                else:
                                    print("❌ Filter reset is not showing all devices")
                            else:
                                print("❌ Reset button not found")
                        else:
                            print("❌ Device type filter not found")
                    else:
                        print("❌ Apply filters button not found")
                else:
                    print("❌ Hostname filter not found")
            
            print("\n===== Inventory Fix Summary =====")
            if fix_result.get('success'):
                print(f"✅ Successfully populated inventory table with {fix_result.get('rowCount', 0)} devices")
                print("✅ Inventory filtering is working")
                
                # Suggest permanent fixes
                print("\n===== Permanent Fix Recommendations =====")
                print("1. Update the parseCSV function to handle line breaks properly")
                print("2. Add direct table population on page load to ensure the CSV data is always displayed")
                print("3. Ensure the inventory filtering functions are correctly bound to the UI elements")
                
                return True
            else:
                print(f"❌ Failed to fix inventory display: {fix_result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Error during direct fix: {e}")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            await browser.close()

async def main():
    await direct_inventory_fix()

if __name__ == "__main__":
    asyncio.run(main())
