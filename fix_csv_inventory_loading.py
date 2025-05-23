#!/usr/bin/env python3
"""
Script to verify and fix CSV inventory loading in NetAuditPro.

This script checks how the application is loading CSV inventory data 
and ensures it properly populates the ACTIVE_INVENTORY_DATA structure.
"""

import os
import io
import csv
import json
import requests
from urllib.parse import urljoin

# Configuration
APP_URL = "http://localhost:5007"
SAMPLE_INVENTORY_PATH = "/root/za-con/inventories/sample-inventory.csv"

def verify_sample_inventory():
    """Verify the sample inventory file exists and has valid content"""
    if not os.path.exists(SAMPLE_INVENTORY_PATH):
        print(f"❌ Sample inventory file not found at {SAMPLE_INVENTORY_PATH}")
        return False
        
    try:
        with open(SAMPLE_INVENTORY_PATH, 'r') as f:
            content = f.read()
            if not content.strip():
                print(f"❌ Sample inventory file is empty")
                return False
                
            # Check if it has valid CSV format
            f.seek(0)
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                print(f"❌ Sample inventory file has no headers")
                return False
                
            rows = list(reader)
            if not rows:
                print(f"❌ Sample inventory file has no data rows")
                return False
                
            print(f"✅ Sample inventory file exists with {len(rows)} rows and headers: {headers}")
            return True
    except Exception as e:
        print(f"❌ Error reading sample inventory file: {e}")
        return False

def check_inventory_api():
    """Check if the application's inventory API is working"""
    try:
        # Try to get the active inventory information
        response = requests.get(f"{APP_URL}/get_active_inventory_info")
        if response.status_code != 200:
            print(f"❌ Failed to get active inventory info. Status code: {response.status_code}")
            return False
            
        data = response.json()
        print(f"Active inventory info: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error checking inventory API: {e}")
        return False

def analyze_raw_inventory_content():
    """Analyze the raw inventory content"""
    try:
        # Get the inventory management page
        response = requests.get(f"{APP_URL}/manage_inventories")
        if response.status_code != 200:
            print(f"❌ Failed to get inventory management page. Status code: {response.status_code}")
            return False
            
        html_content = response.text
        
        # Find the raw inventory content (this is a simple approach and might need refinement)
        textarea_start = html_content.find('<textarea class="form-control" id="raw_inventory_content_edit"')
        if textarea_start == -1:
            print(f"❌ Raw inventory textarea not found in the HTML")
            return False
            
        content_start = html_content.find('>', textarea_start) + 1
        content_end = html_content.find('</textarea>', content_start)
        
        if content_start == -1 or content_end == -1:
            print(f"❌ Could not extract raw inventory content")
            return False
            
        raw_content = html_content[content_start:content_end].strip()
        print(f"Raw inventory content (first 200 chars): {raw_content[:200]}")
        
        # Parse the CSV content
        if not raw_content:
            print(f"❌ Raw inventory content is empty")
            return False
            
        f = io.StringIO(raw_content)
        reader = csv.reader(f)
        headers = next(reader, None)
        if not headers:
            print(f"❌ Raw inventory has no headers")
            return False
            
        rows = list(reader)
        print(f"✅ Raw inventory has {len(rows)} rows and headers: {headers}")
        
        return True
    except Exception as e:
        print(f"❌ Error analyzing raw inventory content: {e}")
        return False

def main():
    """Main function to verify and fix CSV inventory loading"""
    print("\n===== Verifying Sample Inventory =====")
    verify_sample_inventory()
    
    print("\n===== Checking Inventory API =====")
    check_inventory_api()
    
    print("\n===== Analyzing Raw Inventory Content =====")
    analyze_raw_inventory_content()
    
    print("\n===== Recommendations =====")
    print("1. Ensure the ACTIVE_INVENTORY_DATA structure follows the expected format:")
    print("   {'data': [{'hostname': 'router1', 'ip': '1.1.1.1'}, ...], 'headers': ['hostname', 'ip', ...]}")
    print("2. Verify that the inventory data is properly loaded and displayed in the CSV table")
    print("3. Check the JavaScript code for table population to ensure it handles the data structure correctly")

if __name__ == "__main__":
    main()
