# Router Audit CLI Tool v3.8

## Overview

The Router Audit CLI Tool is a command-line utility designed to audit the security configuration of Cisco routers via a jump server. This version (v3.8) focuses on CLI-only functionality, providing a streamlined experience for automated audits without the need for a web interface.

## Key Features

- **Jump Server Integration**: Connects to routers through a centralized jump server
- **Multi-Router Support**: Audits multiple routers in sequence from a CSV inventory
- **AUX Port Security Analysis**: Focuses on identifying telnet security vulnerabilities
- **Comprehensive Reporting**: Generates detailed CSV and JSON reports
- **Risk Assessment**: Evaluates security posture with clear risk levels
- **Detailed Logging**: Captures all steps of the audit process for troubleshooting

## Requirements

- Python 3.6 or higher
- Required packages:
  - netmiko
  - paramiko

## Installation

1. Clone this repository or download the script
2. Install required packages:
   ```
   pip install netmiko paramiko
   ```

## Configuration

### Environment Variables

Create a `.env` file in the same directory as the script with the following variables:
```
JUMP_HOST=172.16.39.128
JUMP_USERNAME=root
JUMP_PASSWORD=your_password
INVENTORY_FILE=inventories/router.csv
```

### Router Inventory

Create a CSV file with the following columns:
```
hostname,ip,device_type,username,password,secret,ios_version,notes
R0,172.16.39.100,cisco_ios,cisco,cisco,cisco,15.7,Production router
```

## Usage

Run the script from the command line:
```
python rr4-router-complete-enchanced-v3.8-cli-only.py
```

The script will:
1. Connect to the jump server using credentials from the .env file
2. Read the router inventory from the CSV file
3. Connect to each router through the jump server
4. Audit the AUX port configuration
5. Assess security risks
6. Generate detailed reports

## Reports

After a successful audit, the following reports are generated:

- **CSV Report**: `router_audit_results_YYYYMMDD_HHMMSS.csv`
- **JSON Report**: `router_audit_results_YYYYMMDD_HHMMSS.json`
- **Log File**: `audit.log`

## Risk Levels

The tool categorizes security risks into the following levels:

- **HIGH**: Serious security vulnerabilities detected
- **MEDIUM**: Potential security issues identified
- **LOW**: Minor security concerns found
- **SECURE**: No security issues detected
- **UNKNOWN**: Unable to assess security posture

## Troubleshooting

If you encounter issues:

1. Check the `audit.log` file for detailed error messages
2. Verify jump server connectivity and credentials
3. Ensure router inventory information is correct
4. Confirm network accessibility between jump server and target routers

## Security Note

This tool handles sensitive credentials. Always:
- Use environment variables rather than hardcoding credentials
- Protect access to the .env file
- Consider using a password manager for credential storage
- Audit usage of the tool itself in security-sensitive environments
