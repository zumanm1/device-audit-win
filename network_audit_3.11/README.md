# Network Audit Tool v3.11

A modular network device audit framework designed for comprehensive network security auditing. This tool combines multiple audit capabilities into a cohesive framework while ensuring each module can operate independently.

## Features

- **Modular Architecture**: Each audit module can operate independently or as part of the full framework
- **Multi-phase Security Auditing**: Implements a systematic 5-phase approach to network security
- **Comprehensive Telnet Vulnerability Detection**: Specialized module for identifying telnet-related security issues
- **Basic Connectivity Testing**: Verify network reachability before deeper security audits
- **Secure Credential Management**: Built-in encryption for sensitive credentials
- **Unified Reporting**: Consistent reporting across all audit types
- **Test Mode**: Simulate audit functions without connecting to actual devices

## Modules

### Core Module (`audit_core.py`)
- Centralized logging and utilities
- Secure credential management
- Shared data structures and reporting

### Connectivity Audit (`connectivity_audit.py`)
- ICMP ping testing
- TCP port checks
- DNS resolution
- Device reachability verification

### Security Audit (`security_audit.py` & `security_audit_phases.py`)
Implements the 5-phase security audit approach:
1. Connectivity Verification
2. Authentication Testing
3. Configuration Audit
4. Risk Assessment
5. Reporting and Recommendations

### Telnet Audit (`telnet_audit.py`)
- Detection of telnet service on VTY lines
- Identification of insecure authentication on telnet access
- Discovery of AUX ports with telnet enabled
- Analysis of telnet access control lists

### Main Framework (`network_audit.py`)
- Unified entry point for all audit types
- Combines results into comprehensive reports
- Command-line interface for selecting audit options

## Installation

1. Clone the repository or extract the files to your preferred location
2. Install required dependencies:
   ```
   pip install netmiko cryptography colorama
   ```
3. Ensure proper permissions:
   ```
   chmod +x network_audit.py
   ```

## Usage

### Basic Usage

Run a complete network audit:
```
python network_audit.py --csv your_devices.csv
```

### Command-line Options

```
usage: network_audit.py [-h] [-a] [-c] [-s] [-n] [-t] [--csv CSV] [-j JUMP_HOST]

Network Audit Tool v3.11

options:
  -h, --help            show this help message and exit
  -t, --test            Run in test mode with simulated responses
  --csv CSV             CSV file with device details (default: devices.csv)
  -j JUMP_HOST, --jump-host JUMP_HOST
                        Jump host IP for accessing devices

Audit Types:
  -a, --all             Run all audit types (default)
  -c, --connectivity    Run connectivity audit
  -s, --security        Run security audit
  -n, --telnet          Run telnet audit
```

### Running Individual Modules

Each module can be run independently:

```
# Run just the connectivity audit
python connectivity_audit.py --csv your_devices.csv

# Run just the security audit
python security_audit.py --csv your_devices.csv

# Run just the telnet audit
python telnet_audit.py --csv your_devices.csv
```

## Device CSV Format

Create a CSV file with the following columns:
- `hostname`: Device hostname
- `ip`: IP address
- `device_type`: Device type (e.g., cisco_ios, cisco_asa)
- `username`: SSH username
- `password`: SSH password
- `secret`: Enable secret
- `model`: Device model (optional)

Example:
```
hostname,ip,device_type,username,password,secret,model
router1,192.168.1.1,cisco_ios,admin,password,enable_pass,Cisco 2901
switch1,192.168.1.10,cisco_ios,admin,password,enable_pass,Cisco 3560
```

## Test Mode

All modules support a test mode with simulated responses:
```
python network_audit.py --test
```

This creates sample device data and simulates responses without connecting to real devices.

## Output and Reports

Reports are generated in multiple formats in the `reports` directory:
- JSON reports for programmatic use
- Text reports for easy reading
- CSV reports for import into spreadsheets

## Directory Structure

```
network_audit_3.11/
├── audit_core.py             # Core functionality and shared utilities
├── connectivity_audit.py     # Connectivity verification module
├── security_audit.py         # Main security audit orchestration
├── security_audit_phases.py  # Individual security audit phases
├── telnet_audit.py           # Telnet vulnerability detection
├── network_audit.py          # Unified entry point for all modules
├── README.md                 # This documentation
├── config/                   # Configuration files
├── data/                     # Device data and CSV files
├── logs/                     # Log files from audit runs
└── reports/                  # Generated audit reports
```

## License

This software is provided as-is, with no warranties or guarantees.

## Author

Network Audit Tool v3.11
