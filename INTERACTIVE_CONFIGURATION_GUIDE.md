# RR4 CLI Interactive Configuration Guide

## Overview

The RR4 Complete Enhanced v4 CLI now includes interactive configuration capabilities that allow users to easily set up jump host and device credentials without manually editing configuration files. This feature ensures proper credential management and provides a user-friendly setup experience.

## New Commands

### 1. `configure-env` - Initial Setup
```bash
python3 rr4-complete-enchanced-v4-cli.py configure-env
```

**Purpose**: Set up initial configuration for jump host and device credentials.

**When to use**:
- First time setup
- When .env-t file doesn't exist
- When you want to create a new configuration from scratch

### 2. `update-env` - Update Existing Configuration
```bash
python3 rr4-complete-enchanced-v4-cli.py update-env
```

**Purpose**: Update existing configuration with new values.

**When to use**:
- When you need to change jump host IP, username, or password
- When device credentials have changed
- When you want to modify connection settings

## Interactive Configuration Process

### Step 1: Jump Host Configuration
The system will prompt for:
- **Jump Host IP**: Default is 172.16.39.128 (can be changed)
- **Jump Host Username**: Default is 'root' (can be changed)
- **Jump Host Password**: Secure input (hidden while typing)
- **Jump Host SSH Port**: Default is 22 (can be changed)

### Step 2: Device Credentials
The system will prompt for:
- **Device Username**: Default is 'cisco' (for IOS/IOS-XE/IOS-XR devices)
- **Device Password**: Default is 'cisco' (secure input, hidden while typing)

### Step 3: Optional Settings
The system will prompt for:
- **Inventory File**: Default is 'routers01.csv'
- **Max Concurrent Connections**: Default is 15
- **Command Timeout**: Default is 60 seconds
- **Connection Retry Attempts**: Default is 3

### Step 4: Configuration Summary & Confirmation
The system displays a summary of all settings (with passwords masked) and asks for confirmation before saving.

## Security Features

### Password Protection
- All password inputs are hidden during typing
- Passwords are masked with asterisks in configuration summaries
- Existing passwords show as "current: ****" without revealing the actual value

### File Permissions
- The .env-t file is automatically set to 600 permissions (readable only by owner)
- Sensitive credentials are clearly marked in the file with security warnings

### Default Values
- Sensible defaults are provided for all settings
- Users can press Enter to accept defaults
- Current values are shown as defaults when updating existing configuration

## Generated Configuration File

The interactive setup creates a `.env-t` file with the following structure:

```bash
# NetAuditPro CLI Lite Configuration File
# This file contains sensitive credentials - keep secure
# Generated: 2025-05-29 12:49:08

# Jump Host Configuration
JUMP_HOST_IP=172.16.39.128
JUMP_HOST_USERNAME=root
JUMP_HOST_PASSWORD=eve
JUMP_HOST_PORT=22

# Device Credentials
DEVICE_USERNAME=cisco
DEVICE_PASSWORD=cisco

# Inventory Configuration
INVENTORY_FILE=routers01.csv

# Connection Settings
MAX_CONCURRENT_CONNECTIONS=15
COMMAND_TIMEOUT=60
CONNECTION_RETRY_ATTEMPTS=3
```

## Usage Examples

### First Time Setup
```bash
# Run interactive configuration
python3 rr4-complete-enchanced-v4-cli.py configure-env

# Validate the setup
python3 rr4-complete-enchanced-v4-cli.py show-config

# Test connectivity
python3 rr4-complete-enchanced-v4-cli.py collect-all --dry-run
```

### Updating Jump Host IP
```bash
# Update existing configuration
python3 rr4-complete-enchanced-v4-cli.py update-env

# When prompted for Jump Host IP, enter new value: 172.16.39.140
# Press Enter for other values to keep them unchanged
```

### Changing Device Credentials
```bash
# Update configuration
python3 rr4-complete-enchanced-v4-cli.py update-env

# Keep jump host settings the same (press Enter)
# Update device username/password when prompted
```

## Error Handling

### Missing Configuration File
If you try to run collection commands without a .env-t file:

```bash
✗ Error: Environment file .env-t not found. Please run 'python3 rr4-complete-enchanced-v4-cli.py configure-env' to set up your credentials.
```

### Cancelled Configuration
If you cancel the configuration process (Ctrl+C):

```bash
❌ Configuration cancelled by user
```

### Invalid Input
The system validates input and provides helpful error messages for invalid values.

## Integration with Existing Commands

### Automatic Configuration Loading
All collection commands automatically load configuration from .env-t:
- `collect-all`
- `collect-devices` 
- `collect-group`
- `validate-inventory`

### Configuration Display
Use `show-config` to view current configuration with masked passwords:

```bash
python3 rr4-complete-enchanced-v4-cli.py show-config
```

## Best Practices

### Security
1. **Never commit .env-t files to version control**
2. **Use strong passwords for jump host and devices**
3. **Regularly rotate credentials**
4. **Keep .env-t file permissions restrictive (600)**

### Configuration Management
1. **Use configure-env for initial setup**
2. **Use update-env for changes**
3. **Test connectivity after configuration changes**
4. **Backup .env-t file before major changes**

### Troubleshooting
1. **Use show-config to verify settings**
2. **Use validate-inventory to check device inventory**
3. **Use --dry-run to test connectivity without collection**
4. **Check logs for detailed error information**

## Quick Start Workflow

```bash
# 1. Configure credentials
python3 rr4-complete-enchanced-v4-cli.py configure-env

# 2. Validate inventory
python3 rr4-complete-enchanced-v4-cli.py validate-inventory

# 3. Test connectivity
python3 rr4-complete-enchanced-v4-cli.py collect-all --dry-run

# 4. Collect data
python3 rr4-complete-enchanced-v4-cli.py collect-all
```

## Updated Device Inventory

The inventory has been cleaned up to include only working devices:

| Hostname | IP Address | Platform | Device Type | Groups |
|----------|------------|----------|-------------|---------|
| R0 | 172.16.39.100 | ios | cisco_ios | core_routers |
| R1 | 172.16.39.101 | iosxe | cisco_xe | edge_routers |
| R2 | 172.16.39.102 | ios | cisco_ios | branch_routers |
| R7 | 172.16.39.107 | iosxr | cisco_xr | pe_routers |

## Validation Results

```bash
Inventory Validation Results:
==================================================
Total devices found: 4

Platform Distribution:
  - ios: 2 devices
  - iosxe: 1 devices  
  - iosxr: 1 devices

Group Distribution:
  - core_routers: 1 devices
  - all_devices: 4 devices
  - edge_routers: 1 devices
  - branch_routers: 1 devices
  - pe_routers: 1 devices

✓ Inventory validation passed
```

## Conclusion

The interactive configuration feature makes the RR4 CLI much more user-friendly by:

1. **Eliminating manual file editing** for credential setup
2. **Providing secure password input** with hidden typing
3. **Offering sensible defaults** for all settings
4. **Validating configuration** before saving
5. **Providing clear error messages** and guidance
6. **Maintaining security** with proper file permissions

This enhancement significantly improves the user experience while maintaining the security and functionality of the network automation tool. 