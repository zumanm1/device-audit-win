#!/usr/bin/env python3
"""
Test script to demonstrate NetAuditPro Enhanced Down Device Reporting
"""

import os
import csv
import subprocess
from datetime import datetime
from typing import Dict, Any

# Enhanced tracking for down devices
DOWN_DEVICES: Dict[str, Dict[str, Any]] = {}
DEVICE_STATUS_TRACKING: Dict[str, str] = {}

def ping_local(host: str) -> bool:
    """Ping a host from the local machine."""
    if not host:
        print(f"Invalid host address: empty")
        return False
        
    if host in ['localhost', '127.0.0.1']:
        return True
        
    command = ["ping", "-c", "1", "-W", "1", host]
    try:
        print(f"Pinging {host}...")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        success = result.returncode == 0
        if success:
            print(f"✅ Ping to {host} successful.")
        else:
            print(f"❌ Ping to {host} failed with return code {result.returncode}.")
        return success
    except subprocess.TimeoutExpired:
        print(f"❌ Local ping to {host} timed out.")
        return False
    except Exception as e:
        print(f"❌ Local ping to {host} error: {e}")
        return False

def generate_placeholder_config_for_down_device(device_name: str, device_ip: str, failure_reason: str, base_report_dir: str) -> str:
    """Generate a placeholder configuration file for devices that are down/unreachable."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    placeholder_content = f"""!
! ========================================
! DEVICE STATUS: DOWN / UNREACHABLE
! ========================================
!
! Device Name: {device_name}
! IP Address: {device_ip}
! Status: UNREACHABLE
! Failure Reason: {failure_reason}
! Audit Timestamp: {timestamp}
! 
! This device was unreachable during the network audit.
! Configuration could not be retrieved.
!
! Recommended Actions:
! 1. Verify physical connectivity
! 2. Check power status
! 3. Verify IP configuration
! 4. Test SSH connectivity manually
! 5. Check firewall rules
!
! ========================================
! END PLACEHOLDER CONFIG
! ========================================
!
"""
    
    # Create device-specific report folder
    device_folder = os.path.join(base_report_dir, f"{timestamp.replace(':', '').replace(' ', '_')}")
    os.makedirs(device_folder, exist_ok=True)
    
    # Write placeholder config
    placeholder_path = os.path.join(device_folder, f"{device_name}-DEVICE_DOWN.txt")
    try:
        with open(placeholder_path, 'w') as f:
            f.write(placeholder_content)
        print(f"📄 Generated placeholder config for {device_name}: {placeholder_path}")
        return placeholder_path
    except Exception as e:
        print(f"❌ Error generating placeholder config for {device_name}: {e}")
        return ""

def track_device_status(device_name: str, status: str, failure_reason: str = None):
    """Track device status for enhanced reporting."""
    global DEVICE_STATUS_TRACKING, DOWN_DEVICES
    
    DEVICE_STATUS_TRACKING[device_name] = status
    
    if status in ['DOWN', 'ICMP_FAIL', 'SSH_FAIL', 'COLLECTION_FAIL']:
        DOWN_DEVICES[device_name] = {
            'status': status,
            'failure_reason': failure_reason or 'Unknown failure',
            'timestamp': datetime.now().isoformat(),
            'ip': '',  # Will be filled by calling function
        }
        print(f"📊 Device {device_name} marked as DOWN: {failure_reason}")

def get_device_status_summary() -> Dict[str, Any]:
    """Get a summary of device statuses for reporting."""
    status_counts = {
        'total_devices': 0,
        'up_devices': 0,
        'down_devices': 0,
        'up_device_list': [],
        'down_device_list': [],
        'status_details': DEVICE_STATUS_TRACKING.copy(),
        'down_device_details': DOWN_DEVICES.copy()
    }
    
    for device, status in DEVICE_STATUS_TRACKING.items():
        status_counts['total_devices'] += 1
        if status == 'UP':
            status_counts['up_devices'] += 1
            status_counts['up_device_list'].append(device)
        else:
            status_counts['down_devices'] += 1
            status_counts['down_device_list'].append(device)
    
    return status_counts

def generate_enhanced_summary_report(base_report_dir: str):
    """Generate enhanced summary report with detailed down device information."""
    device_summary = get_device_status_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_content = f"""
==== NetAuditPro Enhanced Audit Summary Report ====
Timestamp: {timestamp}
Inventory File: network-inventory-current-status.csv
Format: CSV Enhanced

=== DEVICE STATUS OVERVIEW ===
Total Devices: {device_summary['total_devices']}
UP Devices: {device_summary['up_devices']}
DOWN Devices: {device_summary['down_devices']}
Success Rate: {(device_summary['up_devices'] / device_summary['total_devices'] * 100):.1f}% if device_summary['total_devices'] > 0 else 0

=== UP DEVICES ===
"""
    
    if device_summary['up_device_list']:
        for device in device_summary['up_device_list']:
            summary_content += f"✅ {device} - OPERATIONAL\n"
    else:
        summary_content += "No devices are currently operational.\n"
    
    summary_content += "\n=== DOWN DEVICES ===\n"
    
    if device_summary['down_device_list']:
        for device in device_summary['down_device_list']:
            down_info = DOWN_DEVICES.get(device, {})
            failure_reason = down_info.get('failure_reason', 'Unknown')
            device_ip = down_info.get('ip', 'Unknown IP')
            summary_content += f"❌ {device} ({device_ip}) - {failure_reason}\n"
    else:
        summary_content += "All devices are operational.\n"
    
    summary_content += f"""
=== DETAILED STATUS TRACKING ===
"""
    for device, status in DEVICE_STATUS_TRACKING.items():
        summary_content += f"{device}: {status}\n"
    
    summary_content += f"""
=== AUDIT RECOMMENDATIONS ===
"""
    
    if device_summary['down_devices'] > 0:
        summary_content += f"""
CRITICAL: {device_summary['down_devices']} device(s) are unreachable.
Recommended Actions:
1. Check physical connectivity for down devices
2. Verify power status of affected devices  
3. Test manual SSH connectivity
4. Review firewall rules and network configuration
5. Contact network operations team for device status
"""
    else:
        summary_content += "✅ All devices operational - No immediate action required.\n"
    
    summary_content += f"""
=== REPORT FILES GENERATED ===
- Summary Report: enhanced_summary.txt
- Placeholder Configs: Generated for all down devices
- Enhanced Status Tracking: Completed

==== END REPORT ====
"""
    
    # Write summary to file
    summary_path = os.path.join(base_report_dir, "enhanced_summary.txt")
    try:
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        print(f"📄 Enhanced summary report written to: {summary_path}")
        return summary_path
    except Exception as e:
        print(f"❌ Error writing summary report: {e}")
        return ""

def main():
    """Main enhanced audit logic demonstration."""
    print("🚀 NetAuditPro Enhanced Audit Starting")
    print("Enhanced features: Down device tracking, placeholder configs, improved reporting")
    print("=" * 80)
    
    # Clear previous tracking
    DEVICE_STATUS_TRACKING.clear()
    DOWN_DEVICES.clear()
    
    # Load current inventory
    inventory_path = os.path.join('inventories', 'network-inventory-current-status.csv')
    if os.path.exists(inventory_path):
        with open(inventory_path, 'r') as f:
            reader = csv.DictReader(f)
            devices = list(reader)
            print(f"📋 Loaded {len(devices)} devices from inventory")
            
            # Create reports directory
            base_report_path = "ALL-ROUTER-REPORTS-ENHANCED"
            os.makedirs(base_report_path, exist_ok=True)
            
            # Test each device
            for device in devices:
                device_name = device['hostname']
                device_ip = device['ip']
                expected_status = device.get('status', 'UNKNOWN')
                
                print(f"\n🔍 Testing {device_name} ({device_ip}) - Expected: {expected_status}")
                
                # Test ping connectivity
                ping_ok = ping_local(device_ip)
                
                if not ping_ok:
                    # Device is down - track it and generate placeholder
                    failure_reason = f"ICMP ping failed to {device_ip}"
                    track_device_status(device_name, 'DOWN', failure_reason)
                    DOWN_DEVICES[device_name]['ip'] = device_ip
                    
                    # Generate placeholder config
                    placeholder_path = generate_placeholder_config_for_down_device(
                        device_name, device_ip, failure_reason, base_report_path
                    )
                    
                    print(f"❌ {device_name} is DOWN - Generated placeholder config")
                else:
                    # Device is up
                    track_device_status(device_name, 'UP')
                    print(f"✅ {device_name} is UP")
            
            print("\n" + "=" * 80)
            
            # Generate enhanced summary report
            summary_path = generate_enhanced_summary_report(base_report_path)
            
            # Print device status summary
            device_summary = get_device_status_summary()
            print(f"\n📊 AUDIT SUMMARY:")
            print(f"   Total Devices: {device_summary['total_devices']}")
            print(f"   UP Devices: {device_summary['up_devices']} - {device_summary['up_device_list']}")
            print(f"   DOWN Devices: {device_summary['down_devices']} - {device_summary['down_device_list']}")
            if device_summary['total_devices'] > 0:
                success_rate = (device_summary['up_devices'] / device_summary['total_devices'] * 100)
                print(f"   Success Rate: {success_rate:.1f}%")
            
            print(f"\n🎉 Enhanced Audit Completed Successfully!")
            print(f"📄 Reports saved to: {base_report_path}/")
            
            if summary_path and os.path.exists(summary_path):
                print(f"\n📄 Enhanced Summary Report Content:")
                print("=" * 50)
                with open(summary_path, 'r') as f:
                    print(f.read())
                    
    else:
        print(f"❌ Inventory file not found: {inventory_path}")

if __name__ == '__main__':
    main() 