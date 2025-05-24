# NetAuditPro Requirements Context

## Overview
This document provides the context and usage instructions for the Python requirements files in the NetAuditPro Complete Enhanced Router Auditing Application.

## Requirements Files

### 1. `requirements.txt` - Production Requirements
This is the main requirements file containing all packages needed to run the NetAuditPro application in production.

#### Core Application Components:
- **Flask Web Framework**: Provides the web interface and API endpoints
- **Flask-SocketIO**: Enables real-time communication for progress updates and interactive shell
- **SSH/Network Libraries**: Paramiko and Netmiko for router connectivity via jump host
- **Report Generation**: ReportLab (PDF) and openpyxl (Excel) for audit reports
- **Data Visualization**: matplotlib for generating charts in reports
- **Configuration Management**: python-dotenv for environment variables

#### Main Script Capabilities:
The `rr4-router-complete-enhanced-v2.py` script provides:
- **3-Phase Router Auditing**:
  - Phase 0: Jump host connectivity testing
  - Phase 1: Router ICMP reachability check  
  - Phase 1.5: Router SSH authentication test
  - Phase 2: Data collection & audit (Physical Line Telnet Check)
- **Real-time Web Interface** with SocketIO updates
- **Interactive SSH Shell** for remote device access
- **Comprehensive Reporting** (PDF, Excel, CSV formats)
- **Inventory Management** (CSV/YAML support)
- **Command Logging** with detailed device interaction tracking
- **Enhanced Down Device Reporting** with failure analysis

### 2. `requirements-dev.txt` - Development Requirements  
Includes all production requirements plus testing and development tools.

#### Additional Development Tools:
- **pytest Suite**: Complete testing framework with coverage and mocking
- **Test Utilities**: Factory-boy, faker for test data generation
- **Mock Libraries**: For simulating network devices and SSH connections

## Installation Instructions

### For Production Deployment:
```bash
# Install Python 3.8+ (recommended: Python 3.9+)
python3 -m pip install --upgrade pip

# Install production requirements
pip install -r requirements.txt
```

### For Development Environment:
```bash
# Install development requirements (includes production requirements)
pip install -r requirements-dev.txt
```

### Using Virtual Environment (Recommended):
```bash
# Create virtual environment
python3 -m venv netauditpro-env

# Activate virtual environment
source netauditpro-env/bin/activate  # Linux/Mac
# OR
netauditpro-env\Scripts\activate     # Windows

# Install requirements
pip install -r requirements.txt
```

## Package Versions and Compatibility

### Core Dependencies Explained:

1. **Flask==2.3.3**: Web framework for the application
2. **flask-socketio==5.3.6**: Real-time bidirectional communication
3. **paramiko==3.3.1**: Low-level SSH client for jump host connections
4. **netmiko==4.2.0**: High-level network device automation
5. **colorama==0.4.6**: Cross-platform colored terminal output
6. **python-dotenv==1.0.0**: Load environment variables from .env files
7. **reportlab==4.0.4**: PDF generation for audit reports
8. **openpyxl==3.1.2**: Excel file generation for reports
9. **matplotlib==3.7.2**: Chart generation for visual reports
10. **PyYAML==6.0.1**: YAML configuration file support

### Version Pinning Strategy:
- All versions are pinned to ensure reproducible deployments
- Versions chosen are stable releases compatible with Python 3.8+
- Regular updates should be tested in development environment first

## System Requirements

### Minimum Python Version:
- Python 3.8 or higher (Python 3.9+ recommended)

### Operating System Support:
- Linux (primary target)
- macOS 
- Windows (with some limitations for SSH functionality)

### Network Requirements:
- Access to target routers via jump host
- HTTP/HTTPS connectivity for web interface
- SSH connectivity to jump host (typically port 22)

## Configuration Files

The application uses several configuration methods:

### 1. Environment Variables (.env file):
```bash
JUMP_HOST=your-jump-host-ip
JUMP_USERNAME=your-username
JUMP_PASSWORD=your-password
DEVICE_USERNAME=default-router-username
DEVICE_PASSWORD=default-router-password
```

### 2. Inventory Files:
- **CSV Format**: `inventories/network-inventory-current-status.csv`
- **YAML Format**: `inventories/inventory-list-v1.yaml` (legacy support)

Example CSV inventory structure:
```csv
router_name,router_ip,router_type,router_username,router_password,enable_password,status
R1,172.16.39.101,cisco_ios,admin,password123,,UP
R2,172.16.39.102,cisco_ios,admin,password123,,DOWN
```

## Running the Application

### Basic Startup:
```bash
python3 rr4-router-complete-enhanced-v2.py
```

### Application will start on:
- Default Port: 5009
- Web Interface: http://localhost:5009
- SocketIO: Real-time updates enabled

### Key Features Available:
1. **Home Dashboard**: View current audit status and device overview
2. **Settings**: Configure jump host and device credentials
3. **Inventory Management**: Upload, edit, and manage device inventories
4. **Command Logs**: View detailed logs of device interactions
5. **Interactive Shell**: Direct SSH access to devices via web interface
6. **Report Generation**: Download PDF, Excel, and CSV reports

## Troubleshooting

### Common Installation Issues:

1. **pip install failures**: Upgrade pip and ensure development headers are installed
   ```bash
   sudo apt-get install python3-dev python3-pip build-essential
   ```

2. **matplotlib issues**: Install system dependencies
   ```bash
   sudo apt-get install python3-tk
   ```

3. **SSH connectivity**: Verify jump host access and firewall settings

### Performance Considerations:
- Large inventories (>100 devices) may require increased timeout values
- PDF generation with many charts may need additional memory
- Concurrent audits are limited by jump host connection limits

## Security Notes

### Credential Management:
- Passwords are stored in .env file (not in version control)
- SSH keys are supported for jump host authentication
- Device passwords are sanitized in logs

### Network Security:
- Application runs on localhost by default
- For remote access, configure reverse proxy (nginx/Apache)
- Use HTTPS in production environments

### File Security:
- Upload directory permissions should be restricted
- Log files may contain sensitive information
- Regular cleanup of old reports recommended

## Support and Updates

### Documentation:
- See `NETWORK_AUDIT_TASK_MANAGEMENT.md` for detailed usage
- Check `ENHANCEMENT_SUMMARY.md` for feature descriptions
- Review `PROJECT_ORGANIZATION.md` for architecture details

### Version History:
- v4.2.0: Complete enhanced edition with all original features preserved
- Comprehensive command logging and enhanced down device reporting
- Improved web interface with real-time updates 