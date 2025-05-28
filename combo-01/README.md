# Network Audit Tool v3.11

A modular network device audit framework designed for comprehensive network security auditing. This tool combines multiple audit capabilities into a cohesive framework while ensuring each module can operate independently. Fully cross-platform compatible between Windows and Ubuntu systems.

## Features

- **Modular Architecture**: Each audit module can operate independently or as part of the full framework
- **Multi-phase Security Auditing**: Implements a systematic 5-phase approach to network security
- **Comprehensive Telnet Vulnerability Detection**: Specialized module for identifying telnet-related security issues
- **Basic Connectivity Testing**: Verify network reachability before deeper security audits
- **Secure Credential Management**: Built-in encryption for sensitive credentials
- **Unified Reporting**: Consistent reporting across all audit types
- **Test Mode with Auto-Fallback**: Simulate audit functions without connecting to actual devices, with automatic fallback to test mode when real connections fail
- **Cross-Platform Compatibility**: Runs seamlessly on both Windows and Ubuntu systems with no code modifications
- **Portable Deployment**: Self-contained directory structure that can be moved to any location on any machine

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

### On Linux:

1. Copy the entire `combo-01` directory to your preferred location
2. Install required dependencies:
   ```bash
   pip install netmiko cryptography colorama tabulate
   ```
3. Ensure proper permissions:
   ```bash
   chmod +x network_audit.py
   ```

### On Windows:

1. Copy the entire `combo-01` directory to your preferred location
2. Install required dependencies:
   ```powershell
   pip install netmiko cryptography colorama tabulate
   ```

### Portable Deployment

This tool is designed to be completely self-contained. You can copy the `combo-01` directory to any location on any machine (Windows or Linux), and it will function correctly without modification. All paths are resolved relative to the script location, not using absolute paths.

## Usage

### Basic Usage

Run a complete network audit:
```bash
# On Linux
python3 network_audit.py --csv your_devices.csv

# On Windows
python network_audit.py --csv your_devices.csv
```

### Command-line Options

```
usage: network_audit.py [-h] [-a] [-c] [-s] [-n] [-t] [--csv CSV] [-j JUMP_HOST] [--auto-fallback] [--no-fallback]

Network Audit Tool v3.11

options:
  -h, --help            show this help message and exit
  -t, --test            Run in test mode with simulated responses
  --csv CSV             CSV file with device details (default: devices.csv)
  -j JUMP_HOST, --jump-host JUMP_HOST
                        Jump host IP for accessing devices
  --auto-fallback       Automatically fallback to test mode when real connections fail (default)
  --no-fallback         Disable automatic fallback to test mode

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

## Test Mode and Auto-Fallback

### Basic Test Mode

All modules support a test mode with simulated responses:
```bash
python network_audit.py --test
```

This creates sample device data and simulates responses without connecting to real devices.

### Auto-Fallback Feature

The tool includes an intelligent auto-fallback feature that automatically switches to test mode when real device connections fail:

```bash
python network_audit.py --csv your_devices.csv --auto-fallback
```

This allows the tool to demonstrate functionality even when:
- Network devices are unreachable
- Credentials are incorrect
- SSH/Telnet services are unavailable

The fallback is enabled by default. Use `--no-fallback` to disable it if you want to see actual connection errors.

## Output and Reports

Reports are generated in multiple formats in the `reports` directory:
- JSON reports for programmatic use
- Text reports for easy reading
- CSV reports for import into spreadsheets

## Directory Structure

```
combo-01/
├── audit_core.py             # Core functionality and shared utilities
├── connectivity_audit.py     # Connectivity verification module
├── security_audit.py         # Main security audit orchestration
├── security_audit_phases.py  # Individual security audit phases
├── telnet_audit.py           # Telnet vulnerability detection
├── network_audit.py          # Unified entry point for all modules
├── run_all_in_order.py       # Script to run all modules in the correct order
├── README.md                 # This documentation
├── config/                   # Configuration files
├── data/                     # Device data and CSV files
    ├── audit_results.sqlite  # SQLite database for audit results
    └── sample_devices.csv    # Sample device data for test mode
├── logs/                     # Log files from audit runs
└── reports/                  # Generated audit reports
```

All directories are automatically created if they don't exist when the tool is run.

## Cross-Platform Compatibility

### Path Handling

The tool uses Python's `pathlib` module for all path operations, ensuring consistent behavior across operating systems:

```python
from pathlib import Path

# This works on both Windows and Linux
log_dir = Path(__file__).parent / "logs"
```

### Command Execution

The tool detects the operating system and adjusts command syntax automatically:

```python
import platform

if platform.system() == "Windows":
    ping_cmd = ["ping", "-n", "4", ip]
else:  # Linux/Mac
    ping_cmd = ["ping", "-c", "4", ip]
```

### Text File Handling

All file operations specify UTF-8 encoding to ensure consistent behavior across platforms:

```python
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

## Troubleshooting

### Common Issues

1. **Cryptography Deprecation Warnings**
   - Warning: `TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES`
   - Solution: These warnings are from the paramiko library and don't affect functionality

2. **Connection Failures**
   - Check network connectivity with the `--connectivity` flag only
   - Verify device credentials in your CSV file
   - Try running with `--test` to verify the tool works correctly

3. **Platform-Specific Issues**
   - Windows: Ensure Python is in your PATH environment variable
   - Linux: Ensure proper file permissions with `chmod +x *.py`

### Debugging

Check the log files in the `logs` directory for detailed information about any errors.

## License

This software is provided as-is, with no warranties or guarantees.

## Author

Network Audit Tool v3.11 - Cross-Platform Edition
