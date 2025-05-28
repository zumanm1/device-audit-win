# Network Audit Tool v3.11

A modular network device audit framework designed for comprehensive network security auditing. This tool combines multiple audit capabilities into a cohesive framework while ensuring each module can operate independently. Fully cross-platform compatible between Windows and Ubuntu systems with consistent reporting across all modules.

## Features

- **Modular Architecture**: Each audit module can operate independently or as part of the full framework
- **Multi-phase Security Auditing**: Implements a systematic 5-phase approach to network security
- **Comprehensive Telnet Vulnerability Detection**: Specialized module for identifying telnet-related security issues
- **Basic Connectivity Testing**: Verify network reachability before deeper security audits
- **Secure Credential Management**: Built-in encryption for sensitive credentials
- **Unified Reporting**: Consistent reporting across all audit types with consolidated summary reports
- **Synchronized Timestamps**: All audit modules use the same timestamp for consistent report naming and data correlation
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
usage: network_audit.py [-h] [-a] [-c] [-s] [-n] [-t] [--csv CSV] [-j JUMP_HOST] [--auto-fallback] [--no-fallback] [--timestamp TIMESTAMP] [--no-report]

Network Audit Tool v3.11

options:
  -h, --help            show this help message and exit
  -t, --test            Run in test mode with simulated responses
  --csv CSV             CSV file with device details (default: devices.csv)
  -j JUMP_HOST, --jump-host JUMP_HOST
                        Jump host IP for accessing devices
  --auto-fallback       Automatically fallback to test mode when real connections fail (default)
  --no-fallback         Disable automatic fallback to test mode
  --timestamp TIMESTAMP Use specified timestamp for report naming (for consistency across reports)
  --no-report           Skip individual module reports and only generate the unified report

Audit Types:
  -a, --all             Run all audit types (default)
  -c, --connectivity    Run connectivity audit
  -s, --security        Run security audit
  -n, --telnet          Run telnet audit
```

### Running Individual Modules

Each module can be run independently:

```bash
# Run just the connectivity audit
python connectivity_audit.py --csv your_devices.csv

# Run just the security audit
python security_audit.py --csv your_devices.csv

# Run just the telnet audit
python telnet_audit.py --csv your_devices.csv
```

### Running All Modules in Sequence

Use the run_all_in_order.py script to run all modules in the correct sequence with consistent reporting:

```bash
# Run all modules in sequence with consistent reporting
python run_all_in_order.py --csv your_devices.csv

# Run all modules in test mode
python run_all_in_order.py --test
```

The run_all_in_order.py script offers several advantages:
- Ensures all modules are run in the correct order
- Uses a consistent timestamp across all reports
- Generates a single comprehensive report at the end
- Prevents duplicate individual reports
- Manages shared resources consistently

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

## Test Mode and Reporting Features

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

### Consolidated Reporting

When running all modules together, you can use the `--no-report` flag to skip individual module reports and only generate a unified report at the end:

```bash
python network_audit.py --csv your_devices.csv --no-report
```

This is particularly useful when running multiple audit types to avoid duplicate reports with different timestamps.

### Synchronized Timestamps

When running modules separately but wanting consistent report naming, use the `--timestamp` parameter:

```bash
# Set a timestamp for the first module
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Use the same timestamp for all modules
python connectivity_audit.py --csv your_devices.csv --timestamp $TIMESTAMP
python security_audit.py --csv your_devices.csv --timestamp $TIMESTAMP
python telnet_audit.py --csv your_devices.csv --timestamp $TIMESTAMP
```

The run_all_in_order.py script automatically manages timestamp synchronization for you.

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

### Portable Deployment

The tool is completely self-contained within the combo-01 directory. You can:

1. Copy the entire combo-01 directory to any location on any machine
2. Run the scripts from that location without any path modifications
3. Move the directory between Windows and Linux systems seamlessly

No absolute paths are hardcoded, making the tool fully portable.

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

4. **Multiple Reports with Different Timestamps**
   - Use the run_all_in_order.py script to ensure consistent timestamps
   - Or manually specify `--timestamp` parameter for consistent naming
   - Use `--no-report` flag with individual modules when running in sequence

5. **'check_ports' Errors**
   - This typically occurs when the port list is missing or malformed in the CSV
   - Verify your device CSV has the 'check_ports' column or use test mode

### Debugging

Check the log files in the `logs` directory for detailed information about any errors. Each module creates its own log file with a timestamp matching the corresponding report.

## License

This software is provided as-is, with no warranties or guarantees.

## Author

Network Audit Tool v3.11 - Cross-Platform Edition
