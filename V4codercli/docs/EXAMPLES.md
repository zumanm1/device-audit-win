# 📚 Usage Examples - RR4 Complete Enhanced v4 CLI

This document provides comprehensive examples of how to use the RR4 Complete Enhanced v4 CLI network data collection tool in various scenarios.

## 📋 Table of Contents

1. [Basic Usage Examples](#basic-usage-examples)
2. [Console Line Collection (NEW!)](#console-line-collection-new)
3. [Inventory Management](#inventory-management)
4. [Collection Scenarios](#collection-scenarios)
5. [Advanced Usage](#advanced-usage)
6. [Automation Examples](#automation-examples)
7. [Integration Examples](#integration-examples)
8. [Troubleshooting Examples](#troubleshooting-examples)
9. [Real-World Scenarios](#real-world-scenarios)

## 🚀 Basic Usage Examples

### First Time Setup

```bash
# 1. Configure environment
python3 rr4-complete-enchanced-v4-cli.py configure-env

# Follow prompts:
# Jump Host IP: 172.16.39.128
# Jump Host Username: root
# Jump Host Password: eve
# Device Username: cisco
# Device Password: cisco

# 2. Create inventory file
cat > my_network.csv << 'EOF'
hostname,management_ip,platform,device_type,username,password,groups,model_name,os_version,vendor,wan_ip
R0,172.16.39.100,ios,cisco_ios,cisco,cisco,core_routers;all_devices,3945,15.1,cisco,
R1,172.16.39.101,iosxe,cisco_iosxe,cisco,cisco,edge_routers;all_devices,ASR1001-X,16.9,cisco,
R2,172.16.39.102,ios,cisco_ios,cisco,cisco,branch_routers;all_devices,2911,15.2,cisco,
EOF

# 3. Test connectivity
python3 rr4-complete-enchanced-v4-cli.py test-connectivity --inventory my_network.csv

# 4. Run first collection
python3 rr4-complete-enchanced-v4-cli.py collect-all --inventory my_network.csv
```

### Quick Health Check

```bash
# Collect only health information from all devices
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory my_network.csv \
    --layers health \
    --output health_check_$(date +%Y%m%d)

# Check output
ls -la health_check_*/
```

### Single Device Collection

```bash
# Collect all layers from one device
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices R0 \
    --inventory my_network.csv

# Collect specific layers from one device
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices R1 \
    --layers health,interfaces,bgp \
    --inventory my_network.csv
```

## 🎯 Console Line Collection (NEW!)

### Overview
The console line collection feature is designed for Cisco routers with NM4 console cards, supporting both IOS and IOS XR platforms. It automatically discovers console lines using `show line` and collects individual line configurations.

### Supported Platforms
- **Cisco IOS**: Lines appear in "Int" column as x/y/z format
- **Cisco IOS XE**: Lines appear in "Int" column as x/y/z format  
- **Cisco IOS XR**: Lines appear in "Tty" column as x/y/z format

### Commands Used
- **Discovery**: `show line`
- **IOS/IOS XE Config**: `show running-config | section "line x/y/z"`
- **IOS XR Config**: `show running-config line aux x/y/z`

### Basic Console Collection

```bash
# Collect console lines only from all devices
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory my_network.csv \
    --layers console

# Console collection from specific device
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices R0 \
    --layers console \
    --inventory my_network.csv

# Console with essential layers
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory my_network.csv \
    --layers health,interfaces,console
```

### Console Line Troubleshooting

```bash
# Collect console info for NM4 troubleshooting
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices ROUTER1,ROUTER2 \
    --layers console,health \
    --inventory routers_with_nm4.csv \
    --output console_troubleshooting_$(date +%Y%m%d)

# Check for console connectivity issues
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices BRANCH-RTR-01 \
    --layers console \
    --debug
```

### Console Collection for Audit

```bash
#!/bin/bash
# console_audit.sh - Audit console line configurations

DATE=$(date +%Y%m%d)
OUTPUT_DIR="console_audit_${DATE}"

echo "Starting console line audit..."

# Collect console configurations from all routers
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory production_routers.csv \
    --layers console \
    --output "${OUTPUT_DIR}" \
    --workers 4

# Generate summary report
echo "Console Line Audit - $DATE" > "${OUTPUT_DIR}/audit_summary.txt"
echo "================================" >> "${OUTPUT_DIR}/audit_summary.txt"

# Find devices with console lines configured
find "${OUTPUT_DIR}" -name "*_console_lines.json" -exec basename {} \; | \
    cut -d'_' -f1 | sort > "${OUTPUT_DIR}/devices_with_console.txt"

echo "Devices with console lines:" >> "${OUTPUT_DIR}/audit_summary.txt"
cat "${OUTPUT_DIR}/devices_with_console.txt" >> "${OUTPUT_DIR}/audit_summary.txt"

echo "Console audit completed: $OUTPUT_DIR"
```

### Console Output Examples

#### JSON Output Structure
```json
{
  "device": "172.16.39.100",
  "timestamp": "2025-01-27T01:00:00Z",
  "platform": "ios",
  "show_line_output": "Router#show line\n   Tty Line Typ     Tx/Rx...",
  "console_lines": {
    "0/0/0": {
      "line_type": "aux",
      "status": "available",
      "configuration": "line 0/0/0\n session-timeout 0\n exec-timeout 0 0\n transport input all\n transport output all\n stopbits 1",
      "command_used": "show running-config | section \"line 0/0/0\"",
      "success": true
    }
  },
  "discovered_lines": ["0/0/0", "0/0/1", "0/0/2"],
  "configured_lines": ["0/0/0", "0/0/1"],
  "summary": {
    "total_lines_discovered": 46,
    "total_lines_configured": 2,
    "configuration_success_rate": 100.0
  }
}
```

#### Text Output Example
```
Console Line Configuration Report
==================================
Device: 172.16.39.100
Platform: ios
Timestamp: 2025-01-27T01:00:00Z
Total Lines Discovered: 46
Total Lines Configured: 2
Success Rate: 100.0%

Discovered Console Lines:
--------------------------
  - 0/0/0
  - 0/0/1
  - 0/0/2
  - 0/0/3
  ...

Individual Line Configurations:
-------------------------------

Line 0/0/0:
Command: show running-config | section "line 0/0/0"
Success: True
Configuration:
line 0/0/0
 session-timeout 0
 exec-timeout 0 0
 transport input all
 transport output all
 stopbits 1
```

### Console Collection Scenarios

#### NM4 Card Validation
```bash
# Validate NM4 console cards are properly configured
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices $(cat nm4_routers.txt) \
    --layers console \
    --inventory network_inventory.csv \
    --output nm4_validation_$(date +%Y%m%d_%H%M%S)

# Expected: x/y/z lines where x:0-1, y:0-1, z:0-22 (46 lines per card)
```

#### Console Security Audit
```bash
# Check console line security configurations
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory security_audit_devices.csv \
    --layers console,health \
    --output console_security_audit_$(date +%Y%m%d) \
    --debug

# Review outputs for:
# - Exec timeouts
# - Session timeouts  
# - Transport settings
# - Access control lists
```

#### Pre/Post Change Console Verification
```bash
#!/bin/bash
# console_change_verification.sh

CHANGE_ID=$1
PHASE=$2  # "pre" or "post"

if [ -z "$CHANGE_ID" ] || [ -z "$PHASE" ]; then
    echo "Usage: $0 <change_id> <pre|post>"
    exit 1
fi

OUTPUT_DIR="${PHASE}_change_console_${CHANGE_ID}_$(date +%Y%m%d_%H%M%S)"

echo "Collecting ${PHASE}-change console baseline for Change ID: $CHANGE_ID"

python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices $(cat affected_nm4_devices.txt) \
    --layers console \
    --inventory production_inventory.csv \
    --output "${OUTPUT_DIR}"

echo "Console ${PHASE}-change collection completed: $OUTPUT_DIR"

# Compare if this is post-change
if [ "$PHASE" = "post" ]; then
    echo "Compare with pre-change baseline to identify configuration differences"
fi
```

## 📊 Inventory Management

### Creating Inventory Files

#### Small Network Example

```csv
hostname,management_ip,platform,device_type,username,password,groups,model_name,os_version,vendor,wan_ip
R1,192.168.1.1,ios,cisco_ios,admin,password,core,2911,15.1,cisco,
SW1,192.168.1.10,ios,cisco_ios,admin,password,access,2960,12.2,cisco,
FW1,192.168.1.254,asa,cisco_asa,admin,password,security,5506-X,9.8,cisco,
```

#### Enterprise Network Example

```csv
hostname,management_ip,platform,device_type,username,password,groups,model_name,os_version,vendor,wan_ip
DC1-CORE-01,10.1.1.1,iosxe,cisco_iosxe,svc-collector,SecureP@ss123,datacenter;core,ASR9000,16.12,cisco,203.0.113.1
DC1-CORE-02,10.1.1.2,iosxe,cisco_iosxe,svc-collector,SecureP@ss123,datacenter;core,ASR9000,16.12,cisco,203.0.113.2
DC1-DIST-01,10.1.2.1,iosxe,cisco_iosxe,svc-collector,SecureP@ss123,datacenter;distribution,Catalyst6500,16.9,cisco,
DC1-DIST-02,10.1.2.2,iosxe,cisco_iosxe,svc-collector,SecureP@ss123,datacenter;distribution,Catalyst6500,16.9,cisco,
WAN-RTR-01,10.2.1.1,iosxr,cisco_iosxr,svc-collector,SecureP@ss123,wan;provider_edge,ASR9001,7.3.2,cisco,203.0.113.10
WAN-RTR-02,10.2.1.2,iosxr,cisco_iosxr,svc-collector,SecureP@ss123,wan;provider_edge,ASR9001,7.3.2,cisco,203.0.113.11
BRANCH-01,10.3.1.1,ios,cisco_ios,svc-collector,SecureP@ss123,branch;remote,2911,15.7,cisco,203.0.113.20
BRANCH-02,10.3.2.1,ios,cisco_ios,svc-collector,SecureP@ss123,branch;remote,2911,15.7,cisco,203.0.113.21
```

#### Multi-Vendor Example

```csv
hostname,management_ip,platform,device_type,username,password,groups,model_name,os_version,vendor,wan_ip
R1-CISCO,192.168.1.1,iosxe,cisco_iosxe,admin,cisco123,core,ASR1001-X,16.9,cisco,
R2-JUNIPER,192.168.1.2,junos,juniper,admin,juniper123,core,MX204,20.4R1,juniper,
SW1-ARISTA,192.168.1.10,eos,arista_eos,admin,arista123,access,7050SX-64,4.24,arista,
```

### Inventory Validation

```bash
# Validate inventory format
python3 rr4-complete-enchanced-v4-cli.py validate-inventory --inventory my_network.csv

# Check for duplicate entries
python3 rr4-complete-enchanced-v4-cli.py check-duplicates --inventory my_network.csv

# Test credentials
python3 rr4-complete-enchanced-v4-cli.py test-credentials --inventory my_network.csv
```

## 🎯 Collection Scenarios

### Scenario 1: Daily Health Monitoring

```bash
#!/bin/bash
# daily_health_check.sh

DATE=$(date +%Y%m%d)
OUTPUT_DIR="daily_health_${DATE}"

echo "Starting daily health check..."

python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory production_devices.csv \
    --layers health,interfaces \
    --output "${OUTPUT_DIR}" \
    --workers 6 \
    --timeout 90

# Check for failures
if [ $? -eq 0 ]; then
    echo "Health check completed successfully"
    # Send success notification
    echo "Daily health check completed" | mail -s "Network Health OK" admin@company.com
else
    echo "Health check failed"
    # Send failure notification
    echo "Daily health check failed - check logs" | mail -s "Network Health ALERT" admin@company.com
fi
```

### Scenario 2: Pre-Change Assessment

```bash
#!/bin/bash
# pre_change_collection.sh

CHANGE_ID=$1
if [ -z "$CHANGE_ID" ]; then
    echo "Usage: $0 <change_id>"
    exit 1
fi

OUTPUT_DIR="pre_change_${CHANGE_ID}_$(date +%Y%m%d_%H%M%S)"

echo "Collecting pre-change baseline for Change ID: $CHANGE_ID"

python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory affected_devices.csv \
    --layers health,interfaces,igp,bgp,mpls \
    --output "${OUTPUT_DIR}" \
    --debug

# Create baseline report
echo "Change ID: $CHANGE_ID" > "${OUTPUT_DIR}/change_info.txt"
echo "Collection Date: $(date)" >> "${OUTPUT_DIR}/change_info.txt"
echo "Baseline captured in: $OUTPUT_DIR" >> "${OUTPUT_DIR}/change_info.txt"

echo "Pre-change baseline completed: $OUTPUT_DIR"
```

### Scenario 3: Incident Response

```bash
#!/bin/bash
# incident_response_collection.sh

INCIDENT_ID=$1
AFFECTED_DEVICES=$2

if [ -z "$INCIDENT_ID" ] || [ -z "$AFFECTED_DEVICES" ]; then
    echo "Usage: $0 <incident_id> <device1,device2,device3>"
    exit 1
fi

OUTPUT_DIR="incident_${INCIDENT_ID}_$(date +%Y%m%d_%H%M%S)"

echo "Starting incident response collection for: $INCIDENT_ID"

# Collect comprehensive data from affected devices
python3 rr4-complete-enchanced-v4-cli.py collect-devices \
    --devices "$AFFECTED_DEVICES" \
    --inventory all_devices.csv \
    --layers health,interfaces,igp,bgp,mpls,vpn \
    --output "${OUTPUT_DIR}" \
    --workers 8 \
    --timeout 180 \
    --debug

# Collect neighbor devices for context
echo "Collecting neighbor device information..."
python3 rr4-complete-enchanced-v4-cli.py collect-groups \
    --groups neighbor_devices \
    --inventory all_devices.csv \
    --layers health,interfaces \
    --output "${OUTPUT_DIR}_neighbors"

echo "Incident response collection completed: $OUTPUT_DIR"
```

### Scenario 4: Weekly Configuration Backup

```bash
#!/bin/bash
# weekly_config_backup.sh

WEEK_NUMBER=$(date +%V)
YEAR=$(date +%Y)
OUTPUT_DIR="weekly_backup_${YEAR}W${WEEK_NUMBER}"

echo "Starting weekly configuration backup..."

python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory production_devices.csv \
    --layers health,static_routes \
    --output "${OUTPUT_DIR}" \
    --workers 4

# Compress and archive
tar -czf "${OUTPUT_DIR}.tar.gz" "${OUTPUT_DIR}/"
mv "${OUTPUT_DIR}.tar.gz" /backup/network_configs/

# Cleanup old backups (keep 12 weeks)
find /backup/network_configs/ -name "weekly_backup_*.tar.gz" -mtime +84 -delete

echo "Weekly backup completed and archived"
```

## 🔧 Advanced Usage

### Custom Layer Selection

```bash
# Infrastructure assessment
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory core_devices.csv \
    --layers health,interfaces,igp \
    --exclude-layers vpn,static_routes

# Routing protocol focus
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory all_devices.csv \
    --layers igp,bgp,mpls \
    --output routing_audit_$(date +%Y%m%d)

# Security audit focus
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory security_devices.csv \
    --layers health,interfaces,static_routes \
    --output security_audit_$(date +%Y%m%d)
```

### Performance Optimization

```bash
# High-performance collection for large networks
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory large_network.csv \
    --workers 12 \
    --timeout 300 \
    --no-parallel-layers \
    --output large_network_collection

# Memory-optimized collection
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory memory_limited.csv \
    --workers 2 \
    --timeout 180 \
    --chunk-size 5

# Quick assessment (minimal layers)
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory quick_check.csv \
    --layers health \
    --workers 8 \
    --timeout 60
```

### Group-Based Collection

```bash
# Collect by device groups
python3 rr4-complete-enchanced-v4-cli.py collect-groups \
    --groups core_routers,distribution_switches \
    --inventory enterprise.csv \
    --layers health,interfaces,igp

# Exclude specific groups
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory all_devices.csv \
    --exclude-groups test_devices,maintenance \
    --layers health,interfaces

# Multiple group collection
python3 rr4-complete-enchanced-v4-cli.py collect-groups \
    --groups "datacenter;wan;branch" \
    --inventory network.csv \
    --output multi_site_collection
```

## 🤖 Automation Examples

### Cron Job Setup

```bash
# Add to crontab for automated collections
crontab -e

# Daily health check at 6 AM
0 6 * * * /usr/local/bin/daily_health_check.sh >> /var/log/network_collection.log 2>&1

# Weekly full collection on Sundays at 2 AM
0 2 * * 0 /usr/local/bin/weekly_full_collection.sh >> /var/log/network_collection.log 2>&1

# Monthly configuration backup on 1st at midnight
0 0 1 * * /usr/local/bin/monthly_config_backup.sh >> /var/log/network_collection.log 2>&1
```

### Ansible Integration

```yaml
# ansible-playbook network-collection.yml
---
- hosts: collection_servers
  tasks:
    - name: Run network data collection
      command: >
        python3 rr4-complete-enchanced-v4-cli.py collect-all
        --inventory {{ inventory_file }}
        --layers {{ collection_layers | default('health,interfaces') }}
        --output {{ output_directory }}
      register: collection_result
      
    - name: Check collection status
      fail:
        msg: "Network collection failed"
      when: collection_result.rc != 0
      
    - name: Archive collection results
      archive:
        path: "{{ output_directory }}"
        dest: "/backup/{{ output_directory }}.tar.gz"
        format: gz
        
    - name: Send notification
      mail:
        to: network-team@company.com
        subject: "Network Collection Completed"
        body: "Collection completed successfully in {{ output_directory }}"
      when: collection_result.rc == 0
```

### Python Integration

```python
#!/usr/bin/env python3
# network_collection_automation.py

import subprocess
import json
import datetime
import smtplib
from email.mime.text import MIMEText

class NetworkCollectionAutomator:
    def __init__(self, script_path, inventory_file):
        self.script_path = script_path
        self.inventory_file = inventory_file
        
    def run_collection(self, layers=None, devices=None, output_dir=None):
        """Run network collection with specified parameters."""
        cmd = [
            'python3', self.script_path, 'collect-all',
            '--inventory', self.inventory_file
        ]
        
        if layers:
            cmd.extend(['--layers', ','.join(layers)])
        if devices:
            cmd.extend(['--devices', ','.join(devices)])
        if output_dir:
            cmd.extend(['--output', output_dir])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {'success': True, 'output': result.stdout}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': e.stderr}
    
    def scheduled_health_check(self):
        """Perform scheduled health check."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f'health_check_{timestamp}'
        
        result = self.run_collection(
            layers=['health', 'interfaces'],
            output_dir=output_dir
        )
        
        if result['success']:
            self.send_notification(
                'Health Check Completed',
                f'Network health check completed successfully.\nOutput: {output_dir}'
            )
        else:
            self.send_notification(
                'Health Check Failed',
                f'Network health check failed.\nError: {result["error"]}'
            )
            
        return result
    
    def send_notification(self, subject, body):
        """Send email notification."""
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'network-automation@company.com'
        msg['To'] = 'network-team@company.com'
        
        try:
            smtp = smtplib.SMTP('localhost')
            smtp.send_message(msg)
            smtp.quit()
        except Exception as e:
            print(f"Failed to send notification: {e}")

# Usage example
if __name__ == "__main__":
    automator = NetworkCollectionAutomator(
        '/opt/network-tools/rr4-complete-enchanced-v4-cli.py',
        '/etc/network-inventory/production.csv'
    )
    
    # Run scheduled health check
    result = automator.scheduled_health_check()
    print(f"Collection result: {result}")
```

## 🔗 Integration Examples

### SIEM Integration

```bash
#!/bin/bash
# siem_integration.sh

# Collect network data
OUTPUT_DIR="siem_data_$(date +%Y%m%d_%H%M%S)"

python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory security_devices.csv \
    --layers health,interfaces \
    --output "$OUTPUT_DIR" \
    --format json

# Convert to SIEM format
python3 convert_to_siem.py "$OUTPUT_DIR" > siem_feed.json

# Send to SIEM
curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $SIEM_API_TOKEN" \
    -d @siem_feed.json \
    https://siem.company.com/api/v1/network-data
```

### Monitoring System Integration

```python
# monitoring_integration.py

import requests
import json
from datetime import datetime

class MonitoringIntegration:
    def __init__(self, prometheus_gateway, grafana_api):
        self.prometheus_gateway = prometheus_gateway
        self.grafana_api = grafana_api
    
    def push_metrics(self, collection_results):
        """Push collection metrics to Prometheus."""
        metrics = []
        
        for device, results in collection_results.items():
            # Convert collection results to Prometheus metrics
            if results.get('success'):
                metrics.append(f'network_collection_success{{device="{device}"}} 1')
                
                # CPU utilization
                if 'cpu_utilization' in results:
                    cpu = results['cpu_utilization']
                    metrics.append(f'device_cpu_utilization{{device="{device}"}} {cpu}')
                
                # Interface count
                if 'interface_count' in results:
                    count = results['interface_count']
                    metrics.append(f'device_interface_count{{device="{device}"}} {count}')
            else:
                metrics.append(f'network_collection_success{{device="{device}"}} 0')
        
        # Push to Prometheus Gateway
        payload = '\n'.join(metrics)
        response = requests.post(
            f"{self.prometheus_gateway}/metrics/job/network_collection",
            data=payload,
            headers={'Content-Type': 'text/plain'}
        )
        
        return response.status_code == 200
    
    def create_grafana_alert(self, device, metric, threshold):
        """Create Grafana alert for device metrics."""
        alert_config = {
            "title": f"High {metric} on {device}",
            "query": f'{metric}{{device="{device}"}} > {threshold}',
            "condition": "gt",
            "threshold": threshold,
            "frequency": "1m",
            "notifications": ["network-team"]
        }
        
        response = requests.post(
            f"{self.grafana_api}/api/alerts",
            json=alert_config,
            headers={'Authorization': f'Bearer {self.grafana_token}'}
        )
        
        return response.status_code == 201
```

### Database Integration

```python
# database_integration.py

import sqlite3
import json
from datetime import datetime

class NetworkDataDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_hostname TEXT NOT NULL,
                layer TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                data_size INTEGER,
                execution_time REAL,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER,
                device_hostname TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (collection_id) REFERENCES collections (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_collection_results(self, results):
        """Store collection results in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for device, device_results in results.items():
            for layer, layer_data in device_results.items():
                cursor.execute('''
                    INSERT INTO collections 
                    (timestamp, device_hostname, layer, success, data_size, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    device,
                    layer,
                    layer_data.get('success', False),
                    layer_data.get('data_size', 0),
                    layer_data.get('execution_time', 0)
                ))
                
                collection_id = cursor.lastrowid
                
                # Store metrics
                metrics = layer_data.get('metrics', {})
                for metric_name, metric_value in metrics.items():
                    cursor.execute('''
                        INSERT INTO device_metrics
                        (collection_id, device_hostname, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        collection_id,
                        device,
                        metric_name,
                        str(metric_value),
                        datetime.now().isoformat()
                    ))
        
        conn.commit()
        conn.close()
```

## 🔍 Troubleshooting Examples

### Debug Mode Usage

```bash
# Enable debug mode for troubleshooting
python3 rr4-complete-enchanced-v4-cli.py --debug collect-devices \
    --devices R1 \
    --inventory test.csv \
    --layers health

# Save debug output to file
python3 rr4-complete-enchanced-v4-cli.py --debug collect-all \
    --inventory problematic_devices.csv 2>&1 | tee debug_output.log

# Verbose connectivity testing
python3 rr4-complete-enchanced-v4-cli.py --debug test-connectivity \
    --inventory failing_devices.csv
```

### Connection Testing

```bash
# Test specific device connectivity
python3 rr4-complete-enchanced-v4-cli.py test-devices \
    --devices R1,R2,R3 \
    --inventory network.csv

# Test jump host configuration
python3 rr4-complete-enchanced-v4-cli.py check-jumphost

# Validate credentials
python3 rr4-complete-enchanced-v4-cli.py test-credentials \
    --inventory suspicious_devices.csv
```

### Performance Analysis

```bash
# Profile collection performance
time python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory large_network.csv \
    --layers health

# Memory usage monitoring
/usr/bin/time -v python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory memory_test.csv

# Network bandwidth monitoring during collection
iftop -i eth0 &
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory bandwidth_test.csv
```

## 🌍 Real-World Scenarios

### Scenario: Data Center Migration

```bash
#!/bin/bash
# dc_migration_collection.sh

MIGRATION_PHASE=$1  # pre, during, post
DC_NAME=$2          # dc1, dc2, etc.

case $MIGRATION_PHASE in
    "pre")
        echo "Pre-migration baseline collection for $DC_NAME"
        OUTPUT_DIR="pre_migration_${DC_NAME}_$(date +%Y%m%d)"
        
        python3 rr4-complete-enchanced-v4-cli.py collect-groups \
            --groups "datacenter_${DC_NAME}" \
            --inventory dc_migration.csv \
            --layers health,interfaces,igp,bgp,mpls,vpn \
            --output "$OUTPUT_DIR" \
            --workers 6
        ;;
        
    "during")
        echo "Migration monitoring for $DC_NAME"
        OUTPUT_DIR="during_migration_${DC_NAME}_$(date +%Y%m%d_%H%M%S)"
        
        # Quick health checks every 5 minutes during migration
        for i in {1..12}; do
            python3 rr4-complete-enchanced-v4-cli.py collect-groups \
                --groups "datacenter_${DC_NAME}" \
                --inventory dc_migration.csv \
                --layers health \
                --output "${OUTPUT_DIR}_check_${i}" \
                --timeout 60
            
            sleep 300  # Wait 5 minutes
        done
        ;;
        
    "post")
        echo "Post-migration validation for $DC_NAME"
        OUTPUT_DIR="post_migration_${DC_NAME}_$(date +%Y%m%d)"
        
        python3 rr4-complete-enchanced-v4-cli.py collect-groups \
            --groups "datacenter_${DC_NAME}" \
            --inventory dc_migration.csv \
            --layers health,interfaces,igp,bgp,mpls,vpn \
            --output "$OUTPUT_DIR" \
            --workers 6
        
        # Compare with pre-migration baseline
        python3 compare_collections.py \
            "pre_migration_${DC_NAME}_*" \
            "$OUTPUT_DIR" \
            > "migration_comparison_${DC_NAME}.report"
        ;;
esac
```

### Scenario: Security Audit

```bash
#!/bin/bash
# security_audit_collection.sh

AUDIT_ID=$1
AUDITOR=$2

echo "Starting security audit collection - Audit ID: $AUDIT_ID"
echo "Auditor: $AUDITOR"

OUTPUT_DIR="security_audit_${AUDIT_ID}_$(date +%Y%m%d)"

# Collect comprehensive security-relevant data
python3 rr4-complete-enchanced-v4-cli.py collect-all \
    --inventory security_audit_devices.csv \
    --layers health,interfaces,static_routes \
    --output "$OUTPUT_DIR" \
    --workers 4 \
    --timeout 240

# Create audit summary
cat > "${OUTPUT_DIR}/audit_summary.txt" << EOF
Security Audit Collection Summary
==================================
Audit ID: $AUDIT_ID
Auditor: $AUDITOR
Collection Date: $(date)
Output Directory: $OUTPUT_DIR

Devices Collected:
EOF

# List collected devices
find "$OUTPUT_DIR" -maxdepth 1 -type d -name "*" | grep -v "^${OUTPUT_DIR}$" | sed 's|.*/||' >> "${OUTPUT_DIR}/audit_summary.txt"

echo "Security audit collection completed: $OUTPUT_DIR"
```

### Scenario: Network Change Validation

```bash
#!/bin/bash
# change_validation.sh

CHANGE_ID=$1
VALIDATION_TYPE=$2  # pre, post

echo "Change validation - Change ID: $CHANGE_ID, Type: $VALIDATION_TYPE"

case $VALIDATION_TYPE in
    "pre")
        OUTPUT_DIR="pre_change_${CHANGE_ID}_$(date +%Y%m%d_%H%M%S)"
        
        python3 rr4-complete-enchanced-v4-cli.py collect-all \
            --inventory change_affected_devices.csv \
            --output "$OUTPUT_DIR"
        
        # Store change reference
        echo "$CHANGE_ID" > "${OUTPUT_DIR}/change_id.txt"
        echo "$(date)" > "${OUTPUT_DIR}/collection_timestamp.txt"
        
        echo "Pre-change baseline captured: $OUTPUT_DIR"
        ;;
        
    "post")
        OUTPUT_DIR="post_change_${CHANGE_ID}_$(date +%Y%m%d_%H%M%S)"
        
        python3 rr4-complete-enchanced-v4-cli.py collect-all \
            --inventory change_affected_devices.csv \
            --output "$OUTPUT_DIR"
        
        # Find corresponding pre-change collection
        PRE_CHANGE_DIR=$(find . -name "pre_change_${CHANGE_ID}_*" -type d | head -1)
        
        if [ -n "$PRE_CHANGE_DIR" ]; then
            echo "Comparing with pre-change baseline: $PRE_CHANGE_DIR"
            python3 compare_collections.py "$PRE_CHANGE_DIR" "$OUTPUT_DIR" > "${OUTPUT_DIR}/change_validation_report.txt"
        else
            echo "Warning: No pre-change baseline found for Change ID: $CHANGE_ID"
        fi
        
        echo "Post-change validation completed: $OUTPUT_DIR"
        ;;
esac
```

### Scenario: Incident Response Automation

```python
#!/usr/bin/env python3
# incident_response_automation.py

import subprocess
import json
import datetime
import argparse
from pathlib import Path

class IncidentResponseCollector:
    def __init__(self, script_path, inventory_file):
        self.script_path = script_path
        self.inventory_file = inventory_file
    
    def emergency_collection(self, incident_id, affected_devices, priority="high"):
        """Perform emergency data collection for incident response."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"incident_{incident_id}_{timestamp}"
        
        # High priority = more comprehensive collection
        if priority == "high":
            layers = ["health", "interfaces", "igp", "bgp", "mpls", "vpn"]
            workers = 8
            timeout = 300
        else:
            layers = ["health", "interfaces"]
            workers = 4
            timeout = 120
        
        cmd = [
            'python3', self.script_path, 'collect-devices',
            '--devices', ','.join(affected_devices),
            '--inventory', self.inventory_file,
            '--layers', ','.join(layers),
            '--output', output_dir,
            '--workers', str(workers),
            '--timeout', str(timeout),
            '--debug'
        ]
        
        print(f"Starting emergency collection for incident {incident_id}")
        print(f"Affected devices: {', '.join(affected_devices)}")
        print(f"Priority: {priority}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Create incident report
            self.create_incident_report(output_dir, incident_id, affected_devices, priority)
            
            return {
                'success': True,
                'output_dir': output_dir,
                'message': f"Emergency collection completed successfully"
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr,
                'message': f"Emergency collection failed"
            }
    
    def create_incident_report(self, output_dir, incident_id, devices, priority):
        """Create incident response report."""
        report_path = Path(output_dir) / "incident_report.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"INCIDENT RESPONSE COLLECTION REPORT\n")
            f.write(f"====================================\n\n")
            f.write(f"Incident ID: {incident_id}\n")
            f.write(f"Collection Time: {datetime.datetime.now()}\n")
            f.write(f"Priority Level: {priority}\n")
            f.write(f"Affected Devices: {', '.join(devices)}\n")
            f.write(f"Output Directory: {output_dir}\n\n")
            f.write(f"Collection Status: COMPLETED\n")
            f.write(f"Next Steps:\n")
            f.write(f"1. Review device health status\n")
            f.write(f"2. Analyze interface states\n")
            f.write(f"3. Check routing protocol convergence\n")
            f.write(f"4. Compare with baseline if available\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Incident Response Data Collection')
    parser.add_argument('incident_id', help='Incident ID')
    parser.add_argument('devices', help='Comma-separated list of affected devices')
    parser.add_argument('--priority', choices=['high', 'normal'], default='high',
                       help='Collection priority level')
    
    args = parser.parse_args()
    
    collector = IncidentResponseCollector(
        '/opt/network-tools/rr4-complete-enchanced-v4-cli.py',
        '/etc/network-inventory/production.csv'
    )
    
    devices = args.devices.split(',')
    result = collector.emergency_collection(args.incident_id, devices, args.priority)
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"📁 Data collected in: {result['output_dir']}")
    else:
        print(f"❌ {result['message']}")
        print(f"🔍 Error: {result['error']}")
```

These examples provide comprehensive guidance for using the RR4 Complete Enhanced v4 CLI tool in various real-world scenarios, from basic operations to complex enterprise automation workflows. 