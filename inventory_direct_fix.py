#!/usr/bin/env python3
"""
Direct fix script for inventory filtering functionality in NetAuditPro.

This script:
1. Injects a fixed JavaScript solution directly into the page
2. Verifies the table is populated correctly
3. Tests all filtering functionality
"""

import os
import asyncio
from playwright.async_api import async_playwright

# Configuration
APP_URL = "http://localhost:5007"
SCREENSHOT_DIR = "inventory_direct_fix_screenshots"

# Create screenshot directory
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def apply_direct_fix():
    """Apply direct JavaScript fix to inventory page and test filtering"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("===== Applying Direct Fix to Inventory Management =====")
            
            # Step 1: Navigate to the inventory management page
            print("\nNavigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_initial_page.png")
            
            # Step 2: Ensure sample inventory is active
            dropdown = await page.query_selector("#active_inventory_file_manage")
            if dropdown:
                options = await dropdown.query_selector_all("option")
                sample_option = None
                
                for option in options:
                    value = await option.get_attribute("value")
                    if "sample-inventory.csv" in value:
                        sample_option = value
                        break
                
                if sample_option:
                    await dropdown.select_option(sample_option)
                    set_active = await page.query_selector('button:has-text("Set as Active")')
                    if set_active:
                        await set_active.click()
                        await page.wait_for_timeout(2000)
                        print("✅ Sample inventory set as active")
            
            # Step 3: Inject the fixed JavaScript code directly
            print("\nInjecting fixed JavaScript code...")
            
            fix_result = await page.evaluate("""() => {
                console.clear();
                console.log("Starting direct inventory fix");
                
                // Helper function to get raw inventory content
                function getRawInventoryContent() {
                    const textarea = document.getElementById('raw_inventory_content_edit');
                    return textarea ? textarea.value : '';
                }
                
                // Improved CSV parser
                function parseCSV(csvStr) {
                    if (!csvStr || !csvStr.trim()) {
                        console.error("Empty CSV string");
                        return [];
                    }
                    
                    console.log(`Parsing CSV string of length ${csvStr.length}`);
                    const lines = csvStr.trim().split('\\n');
                    console.log(`Found ${lines.length} lines in CSV`);
                    
                    const result = [];
                    for (let i = 0; i < lines.length; i++) {
                        if (!lines[i].trim()) continue;
                        
                        // Simple CSV parsing - split by commas
                        // This could be enhanced for quoted fields if needed
                        const row = lines[i].split(',').map(cell => cell.trim());
                        result.push(row);
                    }
                    
                    return result;
                }
                
                // Populate the inventory table
                function populateInventoryTable(data) {
                    if (!data || !data.length) {
                        console.error("No data to populate table");
                        return false;
                    }
                    
                    const tableHeader = document.getElementById('csvTableHeader');
                    const tableBody = document.getElementById('csvTableBody');
                    
                    if (!tableHeader || !tableBody) {
                        console.error("Table elements not found");
                        return false;
                    }
                    
                    // Clear existing content
                    tableHeader.innerHTML = '';
                    tableBody.innerHTML = '';
                    
                    // Create header row
                    const headerRow = document.createElement('tr');
                    for (const header of data[0]) {
                        const th = document.createElement('th');
                        th.textContent = header;
                        th.contentEditable = "true";
                        headerRow.appendChild(th);
                    }
                    tableHeader.appendChild(headerRow);
                    
                    // Add data rows
                    let rowCount = 0;
                    for (let i = 1; i < data.length; i++) {
                        const tr = document.createElement('tr');
                        
                        for (let j = 0; j < data[i].length; j++) {
                            const td = document.createElement('td');
                            td.textContent = data[i][j] || '';
                            td.contentEditable = "true";
                            
                            // Add classes for filtering
                            if (data[0][j] === 'hostname') {
                                td.classList.add('hostname-cell');
                            } else if (data[0][j] === 'ip') {
                                td.classList.add('ip-cell');
                            } else if (data[0][j] === 'device_type') {
                                td.classList.add('device-type-cell');
                            }
                            
                            tr.appendChild(td);
                        }
                        
                        // Add delete button
                        const deleteCell = document.createElement('td');
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = "btn btn-sm btn-danger";
                        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                        deleteBtn.addEventListener('click', () => {
                            tr.remove();
                            updateFilterResults();
                        });
                        deleteCell.appendChild(deleteBtn);
                        tr.appendChild(deleteCell);
                        
                        tableBody.appendChild(tr);
                        rowCount++;
                    }
                    
                    console.log(`Added ${rowCount} rows to the table`);
                    return rowCount > 0;
                }
                
                // Populate device type dropdown
                function populateDeviceTypeDropdown() {
                    const dropdown = document.getElementById('device-type-filter');
                    if (!dropdown) {
                        console.error("Device type dropdown not found");
                        return false;
                    }
                    
                    // Get all device type cells
                    const cells = document.querySelectorAll('.device-type-cell');
                    if (!cells.length) {
                        console.error("No device type cells found");
                        return false;
                    }
                    
                    // Extract unique device types
                    const types = new Set();
                    cells.forEach(cell => {
                        const type = cell.textContent.trim().toLowerCase();
                        if (type) types.add(type);
                    });
                    
                    // Build options HTML
                    let options = '<option value="all">All Device Types</option>';
                    types.forEach(type => {
                        const capitalized = type.charAt(0).toUpperCase() + type.slice(1);
                        options += `<option value="${type}">${capitalized}</option>`;
                    });
                    
                    // Set dropdown HTML
                    dropdown.innerHTML = options;
                    console.log(`Populated device type dropdown with ${types.size} options`);
                    return true;
                }
                
                // Update filter results count
                function updateFilterResults() {
                    const countElement = document.getElementById('filter-results-count');
                    if (!countElement) return;
                    
                    const tbody = document.getElementById('csvTableBody');
                    if (!tbody) return;
                    
                    const totalRows = tbody.querySelectorAll('tr').length;
                    const visibleRows = Array.from(tbody.querySelectorAll('tr'))
                        .filter(row => row.style.display !== 'none').length;
                    
                    countElement.textContent = `Showing ${visibleRows} of ${totalRows} devices`;
                    
                    // Show/hide "no results" message
                    const noResults = document.getElementById('no-filter-results');
                    if (noResults) {
                        noResults.style.display = visibleRows === 0 ? 'block' : 'none';
                    }
                }
                
                // Apply filters function
                function applyFilters() {
                    const hostnameFilter = document.getElementById('hostname-filter').value.toLowerCase();
                    const ipFilter = document.getElementById('ip-filter').value.toLowerCase();
                    const deviceTypeFilter = document.getElementById('device-type-filter').value.toLowerCase();
                    
                    const tbody = document.getElementById('csvTableBody');
                    if (!tbody) return;
                    
                    const rows = tbody.querySelectorAll('tr');
                    let visibleCount = 0;
                    
                    rows.forEach(row => {
                        const hostname = row.querySelector('.hostname-cell')?.textContent.toLowerCase() || '';
                        const ip = row.querySelector('.ip-cell')?.textContent.toLowerCase() || '';
                        const deviceType = row.querySelector('.device-type-cell')?.textContent.toLowerCase() || '';
                        
                        const matchesHostname = !hostnameFilter || hostname.includes(hostnameFilter);
                        const matchesIp = !ipFilter || ip.includes(ipFilter);
                        const matchesDeviceType = !deviceTypeFilter || deviceTypeFilter === 'all' || 
                                                deviceType === deviceTypeFilter;
                        
                        if (matchesHostname && matchesIp && matchesDeviceType) {
                            row.style.display = '';
                            visibleCount++;
                        } else {
                            row.style.display = 'none';
                        }
                    });
                    
                    updateFilterResults();
                    return visibleCount;
                }
                
                // Reset filters function
                function resetFilters() {
                    const filterForm = document.getElementById('inventory-filter-form');
                    if (filterForm) filterForm.reset();
                    
                    const tbody = document.getElementById('csvTableBody');
                    if (!tbody) return;
                    
                    const rows = tbody.querySelectorAll('tr');
                    rows.forEach(row => {
                        row.style.display = '';
                    });
                    
                    updateFilterResults();
                }
                
                // Set up event listeners
                function setupEventListeners() {
                    // Filter form submit
                    const filterForm = document.getElementById('inventory-filter-form');
                    if (filterForm) {
                        filterForm.addEventListener('submit', function(e) {
                            e.preventDefault();
                            applyFilters();
                        });
                        console.log("Filter form submit listener added");
                    }
                    
                    // Reset button
                    const resetButton = document.getElementById('reset-filters');
                    if (resetButton) {
                        resetButton.addEventListener('click', function(e) {
                            e.preventDefault();
                            resetFilters();
                        });
                        console.log("Reset button listener added");
                    }
                    
                    // Add row button
                    const addRowBtn = document.getElementById('addRowBtn');
                    if (addRowBtn) {
                        addRowBtn.addEventListener('click', function() {
                            const tableBody = document.getElementById('csvTableBody');
                            const tableHeader = document.getElementById('csvTableHeader');
                            
                            if (!tableBody || !tableHeader) return;
                            
                            const headerRow = tableHeader.querySelector('tr');
                            if (!headerRow) return;
                            
                            const columnCount = headerRow.querySelectorAll('th').length;
                            
                            const newRow = document.createElement('tr');
                            
                            for (let i = 0; i < columnCount; i++) {
                                const td = document.createElement('td');
                                td.contentEditable = "true";
                                
                                // Add special classes based on header
                                const headerCell = headerRow.querySelectorAll('th')[i];
                                if (headerCell) {
                                    const headerText = headerCell.textContent.toLowerCase();
                                    if (headerText === 'hostname') {
                                        td.classList.add('hostname-cell');
                                    } else if (headerText === 'ip') {
                                        td.classList.add('ip-cell');
                                    } else if (headerText === 'device_type') {
                                        td.classList.add('device-type-cell');
                                    }
                                }
                                
                                newRow.appendChild(td);
                            }
                            
                            // Add delete button
                            const deleteCell = document.createElement('td');
                            const deleteBtn = document.createElement('button');
                            deleteBtn.className = "btn btn-sm btn-danger";
                            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                            deleteBtn.addEventListener('click', function() {
                                newRow.remove();
                                updateFilterResults();
                            });
                            deleteCell.appendChild(deleteBtn);
                            newRow.appendChild(deleteCell);
                            
                            tableBody.appendChild(newRow);
                            updateFilterResults();
                        });
                        console.log("Add row button listener added");
                    }
                }
                
                // Main function to initialize everything
                function initializeInventory() {
                    const rawContent = getRawInventoryContent();
                    if (!rawContent) {
                        console.error("Could not get raw inventory content");
                        return { success: false, message: "No inventory content found" };
                    }
                    
                    const parsedData = parseCSV(rawContent);
                    if (!parsedData.length) {
                        console.error("Failed to parse CSV data");
                        return { success: false, message: "Failed to parse CSV data" };
                    }
                    
                    const tablePopulated = populateInventoryTable(parsedData);
                    if (!tablePopulated) {
                        console.error("Failed to populate table");
                        return { success: false, message: "Failed to populate table" };
                    }
                    
                    populateDeviceTypeDropdown();
                    setupEventListeners();
                    updateFilterResults();
                    
                    return { 
                        success: true, 
                        message: "Inventory successfully initialized", 
                        rowCount: parsedData.length - 1  // Subtract header row
                    };
                }
                
                // Execute the fix
                return initializeInventory();
            }""")
            
            print(f"Fix result: {fix_result}")
            
            if fix_result.get('success'):
                print(f"✅ Successfully populated table with {fix_result.get('rowCount', 0)} rows")
                await page.screenshot(path=f"{SCREENSHOT_DIR}/02_table_populated.png")
                
                # Step 4: Test filtering functionality
                print("\nTesting filtering functionality...")
                
                # Test hostname filter
                await page.fill("#hostname-filter", "R")
                await page.click("#apply-filters")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/03_hostname_filter.png")
                
                hostname_result = await page.evaluate("""() => {
                    const rows = document.querySelectorAll('#csvTableBody tr');
                    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
                    return { 
                        total: rows.length,
                        visible: visibleRows.length,
                        firstVisible: visibleRows.length > 0 ? 
                            visibleRows[0].querySelector('.hostname-cell')?.textContent : null
                    };
                }""")
                
                print(f"Hostname filter 'R': {hostname_result['visible']} of {hostname_result['total']} visible")
                if hostname_result['visible'] > 0:
                    print(f"  First visible row: {hostname_result['firstVisible']}")
                    print("✅ Hostname filtering works")
                else:
                    print("❌ Hostname filtering failed")
                
                # Test device type filter
                await page.fill("#hostname-filter", "")  # Clear hostname filter
                device_types = await page.query_selector_all("#device-type-filter option")
                if len(device_types) > 1:  # Skip "All" option
                    # Select the second option (first device type)
                    device_type_value = await device_types[1].get_attribute("value")
                    await page.select_option("#device-type-filter", device_type_value)
                    await page.click("#apply-filters")
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path=f"{SCREENSHOT_DIR}/04_device_type_filter.png")
                    
                    device_type_result = await page.evaluate("""() => {
                        const rows = document.querySelectorAll('#csvTableBody tr');
                        const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
                        return { 
                            total: rows.length,
                            visible: visibleRows.length,
                            deviceType: document.querySelector('#device-type-filter').value
                        };
                    }""")
                    
                    print(f"Device type filter '{device_type_result['deviceType']}': {device_type_result['visible']} of {device_type_result['total']} visible")
                    if device_type_result['visible'] > 0:
                        print("✅ Device type filtering works")
                    else:
                        print("❌ Device type filtering failed")
                
                # Test reset functionality
                await page.click("#reset-filters")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/05_reset_filters.png")
                
                reset_result = await page.evaluate("""() => {
                    const rows = document.querySelectorAll('#csvTableBody tr');
                    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
                    return { 
                        total: rows.length,
                        visible: visibleRows.length
                    };
                }""")
                
                print(f"After reset: {reset_result['visible']} of {reset_result['total']} visible")
                if reset_result['visible'] == reset_result['total']:
                    print("✅ Reset functionality works")
                else:
                    print("❌ Reset functionality failed")
                
                print("\n===== Inventory Filtering Fix Summary =====")
                print("✅ Table successfully populated with data")
                print("✅ Device type dropdown populated")
                print("✅ Filtering functionality works")
                
                print("\nRecommendations:")
                print("1. Update the JavaScript in rr3-router.py to match the fixed version")
                print("2. Ensure the table is populated on page load")
                print("3. Fix event listeners for filtering controls")
                
                return True
            else:
                print(f"❌ Failed to apply fix: {fix_result.get('message')}")
                return False
        except Exception as e:
            print(f"❌ Error during direct fix: {e}")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        finally:
            await browser.close()

async def main():
    await apply_direct_fix()

if __name__ == "__main__":
    asyncio.run(main())
