# 📦 Installation Guide - RR4 Complete Enhanced v4 CLI

This comprehensive installation guide covers all aspects of setting up the RR4 Complete Enhanced v4 CLI network data collection tool in various environments.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation](#detailed-installation)
4. [Environment Configuration](#environment-configuration)
5. [Platform-Specific Instructions](#platform-specific-instructions)
6. [Verification and Testing](#verification-and-testing)
7. [Troubleshooting Installation](#troubleshooting-installation)
8. [Advanced Configuration](#advanced-configuration)

## 🖥️ System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.8+ (3.9+ recommended) |
| **Memory** | 2GB RAM minimum, 4GB recommended |
| **Storage** | 1GB free space (more for large collections) |
| **Network** | SSH access to target devices |
| **OS** | Linux, macOS, Windows (WSL recommended) |

### Network Requirements

- **SSH Access**: Port 22 to target devices or jump host
- **Jump Host**: SSH access to bastion host (if required)
- **DNS Resolution**: Ability to resolve device hostnames (optional)
- **Bandwidth**: Sufficient for command output transfer

### Supported Platforms

- **Target Devices**: Cisco IOS, IOS XE, IOS XR
- **Operating Systems**: 
  - Ubuntu 18.04+
  - CentOS/RHEL 7+
  - macOS 10.15+
  - Windows 10+ (with WSL)

## ⚡ Quick Installation

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository_url>
cd V4codercli

# Or download and extract ZIP
wget <zip_url>
unzip V4codercli.zip
cd V4codercli
```

### 2. Install Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Verify installation
python3 rr4-complete-enchanced-v4-cli.py --help
```

### 3. Configure Environment

```bash
# Run environment configuration
python3 rr4-complete-enchanced-v4-cli.py configure-env

# Test connectivity (optional)
python3 rr4-complete-enchanced-v4-cli.py test-connectivity --inventory your_inventory.csv
```

## 🔧 Detailed Installation

### Step 1: Python Environment Setup

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python 3.9+
sudo apt install python3.9 python3.9-pip python3.9-venv

# Install additional dependencies
sudo apt install python3.9-dev build-essential libffi-dev libssl-dev

# Create symbolic link (if needed)
sudo ln -sf /usr/bin/python3.9 /usr/bin/python3
```

#### CentOS/RHEL

```bash
# Install EPEL repository
sudo yum install epel-release

# Install Python 3.9+
sudo yum install python39 python39-pip python39-devel

# Install development tools
sudo yum groupinstall "Development Tools"
sudo yum install openssl-devel libffi-devel
```

#### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.9+
brew install python@3.9

# Update PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows (WSL)

```bash
# Enable WSL and install Ubuntu
wsl --install -d Ubuntu

# Inside WSL, follow Ubuntu instructions above
sudo apt update
sudo apt install python3.9 python3.9-pip python3.9-venv
```

### Step 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv rr4-venv

# Activate virtual environment
# Linux/macOS:
source rr4-venv/bin/activate

# Windows (WSL):
source rr4-venv/bin/activate

# Verify activation
which python3
# Should show path in rr4-venv directory
```

### Step 3: Install Dependencies

#### Core Dependencies

```bash
# Install main requirements
pip3 install -r requirements.txt

# Verify core packages
pip3 list | grep -E "(netmiko|nornir|paramiko)"
```

#### Optional Dependencies

```bash
# Enhanced parsing capabilities (pyATS/Genie)
pip3 install pyats[full] genie

# Development dependencies
pip3 install pytest pytest-cov black flake8

# Jupyter notebook support
pip3 install jupyter ipykernel
```

### Step 4: Download and Setup

```bash
# Download project
git clone <repository_url>
cd V4codercli

# Make script executable
chmod +x rr4-complete-enchanced-v4-cli.py

# Verify installation
python3 rr4-complete-enchanced-v4-cli.py --version
```

## 🔧 Environment Configuration

### Configuration Methods

#### Method 1: Interactive Configuration

```bash
# Run interactive configuration
python3 rr4-complete-enchanced-v4-cli.py configure-env

# Follow prompts to configure:
# - Jump host settings
# - Device credentials
# - Collection preferences
```

#### Method 2: Manual Configuration

Create environment file manually:

```bash
# Create environment file
cat > rr4-complete-enchanced-v4-cli.env-t << 'EOF'
# Jump Host Configuration
JUMP_HOST_IP=172.16.39.128
JUMP_HOST_USERNAME=root
JUMP_HOST_PASSWORD=eve
JUMP_HOST_PORT=22

# Device Credentials
DEVICE_USERNAME=cisco
DEVICE_PASSWORD=cisco

# Collection Settings
MAX_WORKERS=4
COMMAND_TIMEOUT=120
CONNECTION_TIMEOUT=30
DEBUG_MODE=false

# Output Configuration
OUTPUT_DIRECTORY=rr4-complete-enchanced-v4-cli-output
SAVE_RAW_OUTPUT=true
SAVE_PARSED_OUTPUT=true
EOF
```

#### Method 3: Environment Variables

```bash
# Set environment variables
export JUMP_HOST_IP=172.16.39.128
export JUMP_HOST_USERNAME=root
export JUMP_HOST_PASSWORD=eve
export DEVICE_USERNAME=cisco
export DEVICE_PASSWORD=cisco

# Persist in shell profile
echo 'export JUMP_HOST_IP=172.16.39.128' >> ~/.bashrc
source ~/.bashrc
```

## 🖥️ Platform-Specific Instructions

### Ubuntu 18.04/20.04 LTS

```bash
# Complete setup script
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9 and dependencies
sudo apt install -y python3.9 python3.9-pip python3.9-venv python3.9-dev
sudo apt install -y build-essential libffi-dev libssl-dev git

# Create virtual environment
python3.9 -m venv rr4-venv
source rr4-venv/bin/activate

# Clone and setup project
git clone <repository_url>
cd V4codercli
pip3 install -r requirements.txt

# Configure environment
python3 rr4-complete-enchanced-v4-cli.py configure-env

echo "Installation complete! Activate environment with: source rr4-venv/bin/activate"
```

### CentOS 8/RHEL 8

```bash
#!/bin/bash

# Install Python 3.9
sudo dnf install -y python39 python39-pip python39-devel
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y openssl-devel libffi-devel git

# Create virtual environment
python3.9 -m venv rr4-venv
source rr4-venv/bin/activate

# Setup project
git clone <repository_url>
cd V4codercli
pip3 install -r requirements.txt

# Configure environment
python3 rr4-complete-enchanced-v4-cli.py configure-env
```

### macOS

```bash
#!/bin/bash

# Install Homebrew dependencies
brew install python@3.9 git

# Create virtual environment
python3.9 -m venv rr4-venv
source rr4-venv/bin/activate

# Setup project
git clone <repository_url>
cd V4codercli
pip3 install -r requirements.txt

# Configure environment
python3 rr4-complete-enchanced-v4-cli.py configure-env
```

### Docker Installation

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash rr4user
RUN chown -R rr4user:rr4user /app
USER rr4user

# Set entrypoint
ENTRYPOINT ["python3", "rr4-complete-enchanced-v4-cli.py"]
```

```bash
# Build and run container
docker build -t rr4-enhanced-cli .

# Run with volume mount for output
docker run -v $(pwd)/output:/app/output rr4-enhanced-cli collect-all --inventory inventory.csv
```

## ✅ Verification and Testing

### Basic Verification

```bash
# Test Python version
python3 --version
# Should show 3.8+

# Test package imports
python3 -c "import netmiko; print('Netmiko:', netmiko.__version__)"
python3 -c "import nornir; print('Nornir:', nornir.__version__)"
python3 -c "import paramiko; print('Paramiko:', paramiko.__version__)"

# Test script execution
python3 rr4-complete-enchanced-v4-cli.py --help
```

### Environment Testing

```bash
# Test environment configuration
python3 rr4-complete-enchanced-v4-cli.py check-env

# Test jump host connectivity (if configured)
python3 rr4-complete-enchanced-v4-cli.py check-jumphost

# Validate inventory format
python3 rr4-complete-enchanced-v4-cli.py validate-inventory --inventory sample_inventory.csv
```

### Connectivity Testing

```bash
# Test device connectivity
python3 rr4-complete-enchanced-v4-cli.py test-connectivity --inventory inventory.csv

# Test single device
python3 rr4-complete-enchanced-v4-cli.py test-connectivity --devices R1 --inventory inventory.csv

# Test with debug output
python3 rr4-complete-enchanced-v4-cli.py --debug test-connectivity --inventory inventory.csv
```

### Sample Collection Test

```bash
# Create test inventory
cat > test_inventory.csv << 'EOF'
hostname,management_ip,platform,device_type,username,password,groups,model_name,os_version,vendor,wan_ip
R1,192.168.1.1,ios,cisco_ios,cisco,cisco,test_devices,2911,15.1,cisco,
EOF

# Test small collection
python3 rr4-complete-enchanced-v4-cli.py collect-devices --devices R1 --layers health --inventory test_inventory.csv
```

## 🔧 Troubleshooting Installation

### Common Issues

#### Python Version Issues

```bash
# Check Python version
python3 --version

# If wrong version, create alias
alias python3='/usr/bin/python3.9'

# Or update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
```

#### Package Installation Failures

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install with verbose output
pip3 install -v netmiko

# Install from source
pip3 install git+https://github.com/ktbyers/netmiko.git
```

#### Permission Issues

```bash
# Fix file permissions
chmod +x rr4-complete-enchanced-v4-cli.py

# Fix directory permissions
chmod -R 755 V4codercli/

# Install packages for user only
pip3 install --user -r requirements.txt
```

#### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf rr4-venv
python3 -m venv rr4-venv
source rr4-venv/bin/activate
pip3 install -r requirements.txt
```

### Dependency Conflicts

```bash
# Check for conflicts
pip3 check

# Create fresh environment
python3 -m venv clean-rr4-env
source clean-rr4-env/bin/activate
pip3 install --no-cache-dir -r requirements.txt
```

### Network Issues

```bash
# Test network connectivity
ping 172.16.39.128

# Test SSH connectivity
ssh root@172.16.39.128

# Test with verbose SSH
ssh -v root@172.16.39.128
```

## 🚀 Advanced Configuration

### Performance Tuning

```bash
# Create performance configuration
cat > performance.conf << 'EOF'
# Performance Settings
MAX_WORKERS=8
CONNECTION_TIMEOUT=60
COMMAND_TIMEOUT=300
BUFFER_SIZE=65535

# Memory Settings
MAX_MEMORY_PER_WORKER=512MB
GARBAGE_COLLECTION=aggressive

# Network Settings
TCP_KEEPALIVE=true
SSH_COMPRESSION=true
EOF
```

### Development Setup

```bash
# Install development dependencies
pip3 install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
python3 -m pytest tests/

# Code formatting
black V4codercli/
flake8 V4codercli/
```

### Production Deployment

```bash
# Create systemd service
sudo cat > /etc/systemd/system/rr4-collector.service << 'EOF'
[Unit]
Description=RR4 Enhanced v4 CLI Network Collector
After=network.target

[Service]
Type=simple
User=rr4user
WorkingDirectory=/opt/rr4-enhanced-cli
ExecStart=/opt/rr4-enhanced-cli/rr4-venv/bin/python3 rr4-complete-enchanced-v4-cli.py collect-all --inventory /etc/rr4/inventory.csv
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable rr4-collector
sudo systemctl start rr4-collector
```

### Logging Configuration

```bash
# Create logging configuration
cat > logging.conf << 'EOF'
[loggers]
keys=root,rr4_collector

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_rr4_collector]
level=DEBUG
handlers=fileHandler
qualname=rr4_collector
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('rr4-collector.log',)

[formatter_simpleFormatter]
format=%(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
EOF
```

## 📚 Post-Installation Steps

### 1. Create Inventory File

```bash
# Copy sample inventory
cp sample_inventory.csv my_inventory.csv

# Edit with your devices
nano my_inventory.csv
```

### 2. Run First Collection

```bash
# Test with single device
python3 rr4-complete-enchanced-v4-cli.py collect-devices --devices R1 --layers health --inventory my_inventory.csv

# Full collection
python3 rr4-complete-enchanced-v4-cli.py collect-all --inventory my_inventory.csv
```

### 3. Review Output

```bash
# Check output directory
ls -la rr4-complete-enchanced-v4-cli-output/

# View collection report
cat rr4-complete-enchanced-v4-cli-output/*/collection_report.json
```

## 🎯 Next Steps

After successful installation:

1. **Read the [README.md](README.md)** for usage instructions
2. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common issues
3. **Review [ARCHITECTURE.md](ARCHITECTURE.md)** for technical details
4. **See [CONTRIBUTING.md](CONTRIBUTING.md)** for development guidelines

## 📞 Support

If you encounter installation issues:

1. **Check the [troubleshooting section](#troubleshooting-installation)**
2. **Review the [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** guide
3. **Run with `--debug` flag** for detailed logs
4. **Check system requirements** and compatibility
5. **Verify network connectivity** to target devices

Installation complete! 🎉 