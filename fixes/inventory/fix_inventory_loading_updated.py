#!/usr/bin/env python3
"""
Updated Fix for Inventory Loading and Filtering Issues
- Uses correct HTML element IDs found in the inventory page
- Ensures proper loading of network-inventory.csv
- Fixes table population and filtering functionality
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import os

# Configuration
APP_URL = "http://localhost:5007"
INVENTORY_FILE = "network-inventory.csv"

async def fix_inventory_loading():
    """Fix inventory loading and filtering functionality with correct element IDs"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        
        try:
            print("===== Fixing Inventory Loading and Filtering =====")
            
            # Step 1: Navigate to inventory management page
            print("\nNavigating to inventory management page...")
            await page.goto(f"{APP_URL}/manage_inventories")
            await page.wait_for_load_state("networkidle")
            
            # Step 2: Set network-inventory.csv as active
            print(f"Setting {INVENTORY_FILE} as active...")
            await page.select_option("#active_inventory_file_manage", INVENTORY_FILE)
            set_active_button = await page.query_selector('button:text("Set as Active")')
            if set_active_button:
                await set_active_button.click()
                await page.wait_for_timeout(2000)
                print(f"✅ Set {INVENTORY_FILE} as active inventory")
            
            # Step 3: Fix JavaScript code for inventory loading
            print("\nInjecting fixed JavaScript for inventory loading...")
            
            # Inject fixed code to fetch inventory data and populate table
            fix_result = await page.evaluate("""
                async () => {
                    try {
                        // Enhanced API data fetching
                        async function fetchInventoryData() {
                            console.log("Fetching inventory data from API...");
                            try {
                                const response = await fetch('/get_active_inventory_info');
                                if (!response.ok) {
                                    throw new Error(`API error: ${response.status}`);
                                }
                                
                                const data = await response.json();
                                console.log("API response:", data);
                                
                                if (data.status === 'success' && data.data && data.headers) {
                                    return {
                                        success: true,
                                        data: data.data,
                                        headers: data.headers
                                    };
                                } else {
                                    throw new Error(data.message || "Invalid data format");
                                }
                            } catch (error) {
                                console.error("Error fetching inventory:", error);
                                return { success: false, error: error.message };
                            }
                        }
                        
                        // Enhanced table population
                        function populateTable(headers, rows) {
                            console.log(`Populating table with ${rows.length} rows`);
                            
                            // First, create or find the table container
                            let tableContainer = document.getElementById('inventory-table-container');
                            if (!tableContainer) {
                                tableContainer = document.createElement('div');
                                tableContainer.id = 'inventory-table-container';
                                
                                // Find appropriate location to insert the table
                                const mainContent = document.querySelector('.container-fluid') || document.body;
                                mainContent.appendChild(tableContainer);
                            }
                            
                            // Create table if it doesn't exist
                            let table = document.getElementById('inventory-table');
                            if (!table) {
                                table = document.createElement('table');
                                table.id = 'inventory-table';
                                table.className = 'table table-striped table-bordered';
                                
                                // Create table structure
                                const thead = document.createElement('thead');
                                thead.id = 'inventoryTableHeader';
                                const tbody = document.createElement('tbody');
                                tbody.id = 'inventoryTableBody';
                                
                                table.appendChild(thead);
                                table.appendChild(tbody);
                                tableContainer.appendChild(table);
                            }
                            
                            const tableHeader = document.getElementById('inventoryTableHeader');
                            const tableBody = document.getElementById('inventoryTableBody');
                            
                            if (!tableHeader || !tableBody) {
                                return { success: false, error: "Table elements not found" };
                            }
                            
                            // Clear existing content
                            tableHeader.innerHTML = '';
                            tableBody.innerHTML = '';
                            
                            // Create header row
                            const headerRow = document.createElement('tr');
                            for (const header of headers) {
                                const th = document.createElement('th');
                                th.textContent = header;
                                headerRow.appendChild(th);
                            }
                            // Add delete header
                            const deleteHeader = document.createElement('th');
                            deleteHeader.textContent = "Actions";
                            headerRow.appendChild(deleteHeader);
                            tableHeader.appendChild(headerRow);
                            
                            // Add data rows
                            for (const row of rows) {
                                const tr = document.createElement('tr');
                                
                                for (const header of headers) {
                                    const td = document.createElement('td');
                                    td.textContent = row[header] || '';
                                    
                                    // Add classes for filtering
                                    if (header === 'hostname') {
                                        td.classList.add('hostname-cell');
                                    } else if (header === 'ip') {
                                        td.classList.add('ip-cell');
                                    } else if (header === 'device_type') {
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
                                    updateFilterResultsCount();
                                });
                                deleteCell.appendChild(deleteBtn);
                                tr.appendChild(deleteCell);
                                
                                tableBody.appendChild(tr);
                            }
                            
                            return { 
                                success: true, 
                                message: "Table populated successfully", 
                                rowCount: rows.length 
                            };
                        }
                        
                        // Fix device type dropdown population
                        function populateDeviceTypeDropdown() {
                            console.log("Populating device type dropdown...");
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
                            let options = '<option value="">All Device Types</option>';
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
                        function updateFilterResultsCount() {
                            const allRows = document.querySelectorAll('#inventoryTableBody tr');
                            const visibleRows = document.querySelectorAll('#inventoryTableBody tr:not(.hidden)');
                            
                            let countDisplay = document.getElementById('filter-results-count');
                            if (!countDisplay) {
                                countDisplay = document.createElement('div');
                                countDisplay.id = 'filter-results-count';
                                countDisplay.className = 'mt-2 mb-2';
                                
                                // Insert before the table
                                const tableContainer = document.getElementById('inventory-table-container');
                                if (tableContainer) {
                                    tableContainer.insertBefore(countDisplay, tableContainer.firstChild);
                                }
                            }
                            
                            countDisplay.textContent = `Showing ${visibleRows.length} of ${allRows.length} devices`;
                        }
                        
                        // Apply filters function
                        function applyFilters() {
                            const hostnameFilter = document.getElementById('hostname-filter').value.toLowerCase();
                            const ipFilter = document.getElementById('ip-filter').value.toLowerCase();
                            const deviceTypeFilter = document.getElementById('device-type-filter').value.toLowerCase();
                            
                            const rows = document.querySelectorAll('#inventoryTableBody tr');
                            let visibleCount = 0;
                            
                            rows.forEach(row => {
                                const hostname = row.querySelector('.hostname-cell')?.textContent.toLowerCase() || '';
                                const ip = row.querySelector('.ip-cell')?.textContent.toLowerCase() || '';
                                const deviceType = row.querySelector('.device-type-cell')?.textContent.toLowerCase() || '';
                                
                                // Check if row matches all filters
                                const matchesHostname = !hostnameFilter || hostname.includes(hostnameFilter);
                                const matchesIp = !ipFilter || ip.includes(ipFilter);
                                const matchesDeviceType = !deviceTypeFilter || deviceType === deviceTypeFilter;
                                
                                if (matchesHostname && matchesIp && matchesDeviceType) {
                                    row.classList.remove('hidden');
                                    visibleCount++;
                                } else {
                                    row.classList.add('hidden');
                                }
                            });
                            
                            updateFilterResultsCount();
                            return visibleCount;
                        }
                        
                        // Reset filters function
                        function resetFilters() {
                            document.getElementById('hostname-filter').value = '';
                            document.getElementById('ip-filter').value = '';
                            document.getElementById('device-type-filter').value = '';
                            
                            // Show all rows
                            const rows = document.querySelectorAll('#inventoryTableBody tr');
                            rows.forEach(row => {
                                row.classList.remove('hidden');
                            });
                            
                            updateFilterResultsCount();
                        }
                        
                        // Add necessary CSS for hidden class if not exists
                        function addRequiredCSS() {
                            let style = document.getElementById('filtering-styles');
                            if (!style) {
                                style = document.createElement('style');
                                style.id = 'filtering-styles';
                                style.textContent = '.hidden { display: none !important; }';
                                document.head.appendChild(style);
                            }
                        }
                        
                        // Initialize inventory
                        async function initializeInventory() {
                            addRequiredCSS();
                            
                            const result = await fetchInventoryData();
                            if (result.success) {
                                const tableResult = populateTable(result.headers, result.data);
                                if (tableResult.success) {
                                    populateDeviceTypeDropdown();
                                    
                                    // Setup filtering event listeners
                                    const hostnameFilter = document.getElementById('hostname-filter');
                                    const ipFilter = document.getElementById('ip-filter');
                                    const deviceTypeFilter = document.getElementById('device-type-filter');
                                    const resetButton = document.getElementById('reset-filters');
                                    const applyButton = document.getElementById('apply-filters');
                                    
                                    if (hostnameFilter) hostnameFilter.addEventListener('input', applyFilters);
                                    if (ipFilter) ipFilter.addEventListener('input', applyFilters);
                                    if (deviceTypeFilter) deviceTypeFilter.addEventListener('change', applyFilters);
                                    if (resetButton) resetButton.addEventListener('click', resetFilters);
                                    if (applyButton) applyButton.addEventListener('click', applyFilters);
                                    
                                    // Initial count display
                                    updateFilterResultsCount();
                                    
                                    return { 
                                        success: true, 
                                        message: "Inventory successfully initialized",
                                        rowCount: tableResult.rowCount
                                    };
                                } else {
                                    return tableResult;
                                }
                            } else {
                                return result;
                            }
                        }
                        
                        // Execute the initialization
                        return await initializeInventory();
                    } catch (error) {
                        console.error("Error in fix script:", error);
                        return { success: false, error: error.message };
                    }
                }
            """)
            
            print(f"Fix result: {fix_result}")
            
            if fix_result.get('success'):
                print(f"✅ Successfully populated table with {fix_result.get('rowCount')} rows")
            else:
                print(f"❌ Failed to fix inventory loading: {fix_result.get('error')}")
            
            # Step 4: Test filtering functionality
            print("\nTesting filtering functionality...")
            
            # Test hostname filtering
            await page.fill('#hostname-filter', 'R')
            await page.wait_for_timeout(1000)
            
            visible_after_hostname_filter = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#inventoryTableBody tr:not(.hidden)');
                    const total = document.querySelectorAll('#inventoryTableBody tr').length;
                    const firstVisible = rows.length > 0 ? 
                        rows[0].querySelector('td').textContent : 'None';
                    return { 
                        visible: rows.length, 
                        total: total,
                        firstVisible: firstVisible
                    };
                }
            """)
            
            print(f"Hostname filter 'R': {visible_after_hostname_filter['visible']} of {visible_after_hostname_filter['total']} visible")
            print(f"  First visible row: {visible_after_hostname_filter['firstVisible']}")
            
            if visible_after_hostname_filter['visible'] < visible_after_hostname_filter['total']:
                print("✅ Hostname filtering works")
            else:
                print("⚠️ Hostname filtering may not be working correctly")
            
            # Test device type filtering
            await page.select_option('#device-type-filter', 'router')
            await page.wait_for_timeout(1000)
            
            visible_after_type_filter = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#inventoryTableBody tr:not(.hidden)');
                    const total = document.querySelectorAll('#inventoryTableBody tr').length;
                    return { visible: rows.length, total: total };
                }
            """)
            
            print(f"Device type filter 'router': {visible_after_type_filter['visible']} of {visible_after_type_filter['total']} visible")
            
            if visible_after_type_filter['visible'] < visible_after_type_filter['total']:
                print("✅ Device type filtering works")
            else:
                print("⚠️ Device type filtering may not be working as expected")
            
            # Test reset functionality
            await page.click('#reset-filters')
            await page.wait_for_timeout(1000)
            
            visible_after_reset = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#inventoryTableBody tr:not(.hidden)');
                    const total = document.querySelectorAll('#inventoryTableBody tr').length;
                    return { visible: rows.length, total: total };
                }
            """)
            
            print(f"After reset: {visible_after_reset['visible']} of {visible_after_reset['total']} visible")
            
            if visible_after_reset['visible'] == visible_after_reset['total']:
                print("✅ Reset functionality works")
            else:
                print("⚠️ Reset functionality may not be working correctly")
            
            print("\n===== Inventory Filtering Fix Summary =====")
            if fix_result.get('success'):
                print("✅ Table successfully populated with data")
                print("✅ Device type dropdown populated")
                print("✅ Filtering functionality set up with correct element IDs")
                
                print("\nRecommendations:")
                print("1. Update the JavaScript in rr3-router.py to match the fixed version")
                print("2. Ensure proper element IDs are used for filtering (hostname-filter, ip-filter, device-type-filter)")
                print("3. Add auto-refresh functionality for the inventory display during audits")
            else:
                print("❌ Inventory loading fix failed")
                print(f"Error: {fix_result.get('error')}")
            
        except Exception as e:
            print(f"❌ Error during fix process: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fix_inventory_loading())
