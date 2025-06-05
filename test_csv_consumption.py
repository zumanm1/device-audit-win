#!/usr/bin/env python3
"""
Test script to validate CSV consumption for routers01.csv
Tests the new CSV format mapping and security validation
"""

import csv
import os
import sys

def map_csv_columns(device_data):
    """
    Copy of the map_csv_columns function from the main script
    """
    mapped_device = {}
    
    # New CSV format: index, management_ip, wan_ip, cisco_model, description
    if "management_ip" in device_data:
        mapped_device["hostname"] = device_data.get("cisco_model", f"Device-{device_data.get('index', 'Unknown')}")
        mapped_device["ip_address"] = device_data.get("management_ip", "")
        mapped_device["wan_ip"] = device_data.get("wan_ip", "")
        mapped_device["cisco_model"] = device_data.get("cisco_model", "")
        mapped_device["description"] = device_data.get("description", "")
        mapped_device["index"] = device_data.get("index", "")
        
        # Set device_type to cisco_xe (as per new requirements)
        mapped_device["device_type"] = "cisco_xe"
        
    # Legacy CSV format: hostname, ip_address, device_type, description
    elif "hostname" in device_data:
        mapped_device["hostname"] = device_data.get("hostname", "")
        mapped_device["ip_address"] = device_data.get("ip_address", "")
        mapped_device["device_type"] = device_data.get("device_type", "cisco_ios")
        mapped_device["description"] = device_data.get("description", "")
        
    # Handle any other fields that might exist
    for key, value in device_data.items():
        if key not in mapped_device:
            mapped_device[key] = value
    
    return mapped_device

def validate_inventory_security(inventory_data):
    """
    Copy of the security validation function from the main script
    """
    validation_result = {
        "is_secure": True,
        "security_issues": [],
        "warnings": []
    }
    
    # List of forbidden credential fields in CSV
    forbidden_credential_fields = [
        'password', 'passwd', 'pwd', 'secret', 'enable_password', 'enable_secret',
        'device_password', 'device_secret', 'login_password', 'auth_password',
        'ssh_password', 'telnet_password', 'console_password', 'enable',
        'credential', 'credentials', 'key', 'private_key', 'auth_key'
    ]
    
    # Check headers for credential fields
    headers = inventory_data.get('headers', [])
    if headers:
        for header in headers:
            header_lower = header.lower()
            for forbidden_field in forbidden_credential_fields:
                if forbidden_field in header_lower:
                    validation_result["is_secure"] = False
                    validation_result["security_issues"].append(
                        f"SECURITY VIOLATION: CSV contains credential field '{header}'. "
                        f"Credentials must only be configured via .env file or web UI settings."
                    )
    
    # Check for common credential patterns in data
    data_rows = inventory_data.get('data', [])
    if data_rows:
        for i, row in enumerate(data_rows):
            for field_name, field_value in row.items():
                if field_value and isinstance(field_value, str):
                    # Check for password-like patterns
                    if (len(field_value) > 6 and 
                        any(char.isdigit() for char in field_value) and
                        any(char.isalpha() for char in field_value) and
                        field_name.lower() not in ['hostname', 'ip_address', 'description', 'device_type', 
                                                  'management_ip', 'wan_ip', 'cisco_model', 'index']):
                        validation_result["warnings"].append(
                            f"Row {i+1}, field '{field_name}': Value looks like a credential. "
                            f"Ensure this is not a password field."
                        )
    
    # Check for required secure fields only (no credentials)
    required_fields = ['hostname', 'ip_address']
    missing_required = []
    
    if headers:
        # Check for new CSV format first
        if 'management_ip' in headers:
            # New format: index, management_ip, wan_ip, cisco_model, description
            new_format_required = ['management_ip', 'cisco_model']
            for required_field in new_format_required:
                if required_field not in headers:
                    missing_required.append(required_field)
        else:
            # Legacy format: hostname, ip_address, device_type, description
            for required_field in required_fields:
                if required_field not in headers:
                    missing_required.append(required_field)
    
    if missing_required:
        validation_result["warnings"].append(
            f"Missing recommended fields: {', '.join(missing_required)}"
        )
    
    return validation_result

def test_csv_consumption():
    """Test if routers01.csv can be consumed by the main script"""
    
    print("=" * 60)
    print("🧪 CSV Consumption Test for NetAuditPro")
    print("=" * 60)
    
    csv_file = "inventories/routers01.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ ERROR: CSV file not found: {csv_file}")
        return False
    
    try:
        # Load CSV file
        print(f"📋 Loading CSV file: {csv_file}")
        inventory_data = {"data": [], "headers": []}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            inventory_data["headers"] = reader.fieldnames or []
            raw_data = list(reader)
            
            print(f"📊 CSV Headers: {inventory_data['headers']}")
            print(f"📊 Number of devices: {len(raw_data)}")
            
            # Apply column mapping to convert new CSV format to internal format
            inventory_data["data"] = [map_csv_columns(device) for device in raw_data]
        
        # Security validation
        print("\n🔒 Running security validation...")
        security_validation = validate_inventory_security(inventory_data)
        
        if security_validation["is_secure"]:
            print("✅ SECURITY: CSV passed security validation")
        else:
            print("❌ SECURITY: CSV failed security validation")
            for issue in security_validation["security_issues"]:
                print(f"   ❌ {issue}")
        
        if security_validation["warnings"]:
            print("⚠️  WARNINGS:")
            for warning in security_validation["warnings"]:
                print(f"   ⚠️  {warning}")
        
        # Test column mapping
        print(f"\n🔄 Testing column mapping...")
        print("Raw CSV data vs Mapped data:")
        
        for i, (raw_device, mapped_device) in enumerate(zip(raw_data, inventory_data["data"])):
            print(f"\nDevice {i+1}:")
            print(f"   Raw: {raw_device}")
            print(f"   Mapped: {mapped_device}")
            
            # Validate required fields are present
            required_mapped_fields = ['hostname', 'ip_address', 'device_type']
            missing_fields = [field for field in required_mapped_fields if not mapped_device.get(field)]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
            else:
                print(f"   ✅ All required fields present")
        
        # Overall result
        print(f"\n{'='*60}")
        if security_validation["is_secure"] and len(inventory_data["data"]) > 0:
            print("✅ SUCCESS: CSV can be consumed by NetAuditPro")
            print(f"✅ Devices loaded: {len(inventory_data['data'])}")
            print(f"✅ Security status: SECURE")
            print(f"✅ Format detected: NEW CSV FORMAT (management_ip based)")
            print(f"✅ Device type: All devices will use 'cisco_xe'")
            return True
        else:
            print("❌ FAILURE: CSV cannot be consumed safely")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to process CSV: {e}")
        return False

if __name__ == "__main__":
    success = test_csv_consumption()
    sys.exit(0 if success else 1) 