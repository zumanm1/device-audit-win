# RR5 Router Auditing Framework

## Overview

The **RR5 Router Auditing Framework** is a comprehensive three-phase network change validation system designed to ensure router upgrades and configuration changes proceed safely. Built with lessons learned from NetAuditPro, it provides systematic pre/post change validation with automated comparison and reporting.

## Features

### 🔍 **Phase 1: Hardware Health Checks**
- **CPU, Memory & Storage**: Monitor utilization and available resources
- **Environmental**: Temperature, fan speeds, PSU voltages and status
- **Chassis & Modules**: Platform health, installed cards, firmware versions
- **Automated Thresholds**: Configurable health baselines with pass/fail criteria

### 📊 **Phase 2: Data Collection (L3VPN/MPLS/IP/OSPF/BGP)**
- **Interface Metrics**: Status, IP addresses, MTU, error counters, packet drops
- **Routing Protocols**: OSPF neighbors, BGP sessions, route counts per VRF
- **MPLS Operations**: LDP sessions, label bindings, L3VPN route metrics
- **Sample Route Tracking**: Random route selection for path change detection
- **Reachability Tests**: Automated ping tests to key destinations

### 🔄 **Phase 3: Post-Check & Comparison**
- **Automated Diff Engine**: Numeric deltas, state changes, threshold violations
- **Intelligent Alerting**: PASS/WARN/FAIL status with configurable thresholds
- **Change Detection**: Interface status, route path changes, session state changes
- **Comprehensive Reporting**: CLI, JSON, CSV, HTML formats with detailed analysis

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    Phase 1 & 2      │    │      Phase 3        │    │    Phase 3          │
│   Pre-Check         │────▶   Post-Check       │────▶   Comparison          │
│                     │    │                     │    │                     │
│ • Hardware Health   │    │ • Same Health       │    │ • Automated Diff    │
│ • Data Collection   │    │ • Same Data         │    │ • Threshold Check   │
│ • Baseline Storage  │    │ • Results Storage   │    │ • Report Generation │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### Core Components

1. **NetworkConnector**: Enhanced connection management with Netmiko/Paramiko fallback
2. **CommandExecutor**: Robust command execution with comprehensive error handling
3. **DataParser**: Intelligent parsing of command outputs into structured data
4. **HealthChecker**: Phase 1 hardware and environmental validation
5. **DataCollector**: Phase 2 comprehensive network state collection
6. **Comparator**: Phase 3 automated comparison and analysis engine
7. **ReportGenerator**: Multi-format reporting (CLI, JSON, CSV, HTML)
8. **WebInterface**: Optional real-time monitoring via Flask/SocketIO

## Installation

### Prerequisites
- Python 3.8+
- Network access to target routers
- SSH connectivity (jump host supported)

### Setup
```bash
# Clone or download the framework
git clone <repository-url>
cd rr5-router-auditing

# Install dependencies
pip install -r requirements-rr5.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables
Create a `.env` file or set environment variables:
```bash
JUMP_HOST=172.16.39.128
JUMP_USERNAME=cisco
JUMP_PASSWORD=cisco
DEVICE_USERNAME=cisco
DEVICE_PASSWORD=cisco
DEVICE_ENABLE=cisco
```

## Configuration

### Config File (config-rr5.yaml)
```yaml
# Connection settings
jump_host: "172.16.39.128"
device_username: "cisco"
device_password: "cisco"

# Health thresholds
health_thresholds:
  cpu_max: 70          # CPU < 70%
  memory_min: 30       # Memory > 30% free
  bgp_prefix_delta: 2  # BGP changes ≤ 2
```

### Inventory File (CSV format)
```csv
device_name,ip_address,device_type,description,location,group
PE01,10.0.1.1,cisco_ios_xe,PE Router 1,DC1,pe_routers
PE02,10.0.1.2,cisco_ios_xe,PE Router 2,DC1,pe_routers
P01,10.0.2.1,cisco_ios_xr,P Router 1,DC1,p_routers
```

## Usage

### Command Line Interface

#### Pre-Check Phase
```bash
# Basic pre-check
python rr5-router-new-new.py --phase pre --devices inventory.csv

# Custom output directory
python rr5-router-new-new.py --phase pre --devices inventory.csv --output pre_upgrade_20241225

# With custom config
python rr5-router-new-new.py --phase pre --devices inventory.csv --config config-rr5.yaml
```

#### Post-Check Phase
```bash
# Post-check after maintenance
python rr5-router-new-new.py --phase post --devices inventory.csv --output post_upgrade_20241225
```

#### Comparison Phase
```bash
# Compare pre and post data
python rr5-router-new-new.py --phase compare \
  --pre pre_upgrade_20241225/pre_data_20241225_100000.json \
  --post post_upgrade_20241225/post_data_20241225_140000.json
```

#### Web Interface
```bash
# Start web monitoring interface
python rr5-router-new-new.py --web --port 5015
# Access: http://localhost:5015
```

### Complete Workflow Example

```bash
# 1. Pre-check before maintenance
python rr5-router-new-new.py --phase pre --devices routers.csv --output pre_maintenance

# 2. Perform your maintenance/upgrade work
# ... upgrade routers, change configs, etc ...

# 3. Post-check after maintenance
python rr5-router-new-new.py --phase post --devices routers.csv --output post_maintenance

# 4. Compare and generate reports
python rr5-router-new-new.py --phase compare \
  --pre pre_maintenance/pre_data_*.json \
  --post post_maintenance/post_data_*.json
```

## Output Files and Reports

### Data Files
```
RR5-AUDIT-RESULTS/
├── pre_data_20241225_100000.json     # Pre-check structured data
├── post_data_20241225_140000.json    # Post-check structured data
├── audit.log                         # Detailed execution log
└── reports/
    ├── audit_results.json            # Comparison results (JSON)
    ├── audit_results.csv             # Comparison results (CSV)
    ├── audit_results.html            # Comparison results (HTML)
    └── cli_summary.txt               # Console output summary
```

### Report Formats

#### CLI Summary
```
================================================================================
RR5 ROUTER AUDIT RESULTS SUMMARY
================================================================================

OVERALL SUMMARY:
  ✅ PASS: 45
  ⚠️  WARN: 3
  ❌ FAIL: 1
  📊 Total checks: 49

CATEGORY BREAKDOWN:
  HEALTH:
    ✅ PASS: 12
    ⚠️ WARN: 1
  INTERFACE:
    ✅ PASS: 24
    ❌ FAIL: 1
  ROUTING:
    ✅ PASS: 9
    ⚠️ WARN: 2

DETAILED RESULTS:
--------------------------------------------------------------------------------
❌ PE01_GigabitEthernet0/0/1_status
    Pre:  up
    Post: down
    Δ:    Status changed
    Threshold: up
    Message: Interface GigabitEthernet0/0/1 status changed: up → down
```

#### JSON Report Structure
```json
{
  "timestamp": "2024-12-25T14:30:00Z",
  "summary": {
    "total": 49,
    "pass": 45,
    "warn": 3,
    "fail": 1
  },
  "results": [
    {
      "check_name": "PE01_cpu_usage",
      "category": "health",
      "pre_value": "15.2%",
      "post_value": "18.7%",
      "delta": "+3.5%",
      "status": "PASS",
      "threshold": "<70%, Δ<10%",
      "message": "CPU usage: 15.2% → 18.7% (Δ+3.5%)"
    }
  ]
}
```

## Health Check Thresholds

### Default Thresholds
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | < 70% | FAIL if exceeded |
| Free Memory | > 30% | FAIL if below |
| CPU Delta | ≤ 10% | WARN if exceeded |
| BGP Prefix Changes | ≤ 2 | WARN/FAIL based on magnitude |
| CRC Errors | Δ = 0 | FAIL if increased |
| Interface Status | Must remain UP | FAIL if DOWN |

### Customizable Thresholds
All thresholds are configurable via `config-rr5.yaml`:

```yaml
health_thresholds:
  cpu_max: 70          # Adjust based on environment
  memory_min: 30       # Adjust based on router capacity
  disk_min: 20         # Minimum free disk space
  temperature_max: 75  # Maximum temperature (°C)
  bgp_prefix_delta: 2  # Acceptable BGP route changes
  cpu_delta: 10        # Acceptable CPU change
  crc_error_delta: 0   # CRC errors must not increase
```

## Advanced Features

### Random Route Sampling
- Automatically selects representative routes for path comparison
- Detects next-hop changes, metric changes, or missing routes
- Configurable sampling strategy (first + random selection)

### Multi-Device Type Support
- **Cisco IOS**: Classic IOS routers
- **Cisco IOS XE**: Modern Cisco platforms
- **Cisco IOS XR**: Service provider platforms
- **Extensible**: Easy to add new device types

### Enhanced Error Handling
- **Connection Fallback**: Netmiko → Paramiko → Manual handling
- **Command Timeout**: Configurable timeouts with graceful failure
- **Credential Sanitization**: All logs sanitized for security
- **Progress Tracking**: Real-time status updates

### Web Interface Features
- **Real-time Logs**: Live command execution monitoring
- **Progress Tracking**: Device-by-device audit progress
- **API Endpoints**: RESTful API for integration
- **WebSocket Updates**: Real-time UI updates

## Integration Examples

### Ansible Integration
```yaml
---
- name: Pre-check network before maintenance
  command: python rr5-router-new-new.py --phase pre --devices {{ inventory_file }}
  
- name: Perform maintenance
  # ... maintenance tasks ...
  
- name: Post-check network after maintenance
  command: python rr5-router-new-new.py --phase post --devices {{ inventory_file }}
  
- name: Generate comparison report
  command: python rr5-router-new-new.py --phase compare --pre {{ pre_file }} --post {{ post_file }}
```

### GitLab CI/CD Pipeline
```yaml
stages:
  - pre_check
  - maintenance
  - post_check
  - validation

pre_check:
  stage: pre_check
  script:
    - python rr5-router-new-new.py --phase pre --devices routers.csv
  artifacts:
    paths:
      - RR5-AUDIT-RESULTS/

post_check:
  stage: post_check
  script:
    - python rr5-router-new-new.py --phase post --devices routers.csv
  artifacts:
    paths:
      - RR5-AUDIT-RESULTS/

validation:
  stage: validation
  script:
    - python rr5-router-new-new.py --phase compare --pre $PRE_FILE --post $POST_FILE
  artifacts:
    reports:
      junit: RR5-AUDIT-RESULTS/audit_results.xml
```

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check connectivity
ping <router_ip>

# Test SSH access
ssh <username>@<router_ip>

# Verify credentials in config or environment
```

#### Command Failures
- **Enable Mode**: Ensure enable password is correct
- **Timeouts**: Increase timeout values in config
- **Command Support**: Check device-specific command availability

#### Missing Dependencies
```bash
# Install all requirements
pip install -r requirements-rr5.txt

# Install specific missing packages
pip install netmiko flask-socketio pyyaml
```

### Debug Mode
```bash
# Enable verbose logging
python rr5-router-new-new.py --phase pre --devices routers.csv --verbose

# Check log files
tail -f RR5-AUDIT-RESULTS/audit.log
```

## Lessons Learned from NetAuditPro

### Applied Improvements
1. **Structured Data Storage**: JSON-based with schema validation
2. **Enhanced Error Handling**: Multi-layer fallback mechanisms
3. **Real-time Progress**: WebSocket-based live updates
4. **Comprehensive Logging**: Sanitized, timestamped, categorized
5. **Flexible Reporting**: Multiple output formats for different needs
6. **Configuration-Driven**: YAML-based configuration management
7. **Modular Architecture**: Separated concerns for maintainability

### Security Enhancements
- **Credential Sanitization**: All logs scrubbed of sensitive data
- **Environment Variables**: Secure credential management
- **Connection Security**: SSH with proper authentication
- **Data Protection**: Local storage with appropriate permissions

## Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-rr5.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/

# Code formatting
black rr5-router-new-new.py

# Linting
flake8 rr5-router-new-new.py
```

### Adding New Device Types
1. Add command templates to `config-rr5.yaml`
2. Implement device-specific parsing in `DataParser`
3. Update connection parameters in `NetworkConnector`
4. Add test cases for new device type

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, feature requests, or questions:
1. Check the troubleshooting section
2. Review the audit logs for detailed error information
3. Ensure all dependencies are properly installed
4. Verify network connectivity and credentials

---

**RR5 Router Auditing Framework v1.0.0**  
*Three-Phase Network Change Validation System* 