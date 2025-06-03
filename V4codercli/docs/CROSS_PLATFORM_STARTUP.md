# RR4 CLI Cross-Platform Startup Guide

## 🌐 Universal Cross-Platform Startup

The RR4 CLI Interactive Startup Manager is designed to work seamlessly across **Windows 10/11**, **Linux**, and **macOS** using Python.

## 🚀 **Primary Startup Method (Recommended)**

### **Universal Command (Works on All Platforms)**

**Windows 10/11:**
```cmd
python start_rr4_cli.py
```

**Linux:**
```bash
python3 start_rr4_cli.py
```

**macOS:**
```bash
python3 start_rr4_cli.py
```

## 📋 **Platform-Specific Instructions**

### 🪟 **Windows 10/11**

#### Option 1: Python Command (Recommended)
```cmd
# Open Command Prompt or PowerShell
cd V4codercli
python start_rr4_cli.py
```

#### Option 2: Batch File (Double-click or command line)
```cmd
# Double-click start_rr4_cli.bat
# Or run in Command Prompt:
start_rr4_cli.bat
```

#### Option 3: Direct Python Script
```cmd
python start_rr4_cli.py
```

### 🐧 **Linux (Ubuntu, RHEL, CentOS, Debian)**

#### Option 1: Python Command (Recommended)
```bash
cd V4codercli
python3 start_rr4_cli.py
```

#### Option 2: Executable Script
```bash
# Make executable (one-time setup)
chmod +x start_rr4_cli.py
# Then run
./start_rr4_cli.py
```

#### Option 3: Shell Script (Alternative)
```bash
./start_rr4.sh
```

### 🍎 **macOS**

#### Option 1: Python Command (Recommended)
```bash
cd V4codercli
python3 start_rr4_cli.py
```

#### Option 2: Executable Script
```bash
# Make executable (one-time setup)
chmod +x start_rr4_cli.py
# Then run
./start_rr4_cli.py
```

#### Option 3: Shell Script (Alternative)
```bash
./start_rr4.sh
```

## 🔧 **Prerequisites by Platform**

### Windows 10/11
- **Python 3.8+** from [python.org](https://python.org) or Microsoft Store
- **Command Prompt** or **PowerShell**
- **Windows Terminal** (recommended for better experience)

### Linux
- **Python 3.8+** (usually pre-installed)
- **Terminal/Shell** access
- Package manager access for dependencies

### macOS
- **Python 3.8+** (install via Homebrew or python.org)
- **Terminal** access
- **Xcode Command Line Tools** (`xcode-select --install`)

## 🎯 **First-Time Setup by Platform**

### Windows Setup
```cmd
# 1. Install Python from python.org
# 2. Open Command Prompt or PowerShell
# 3. Navigate to project directory
cd V4codercli

# 4. Run startup manager
python start_rr4_cli.py

# 5. Select option 1 (First-Time Setup)
```

### Linux Setup
```bash
# 1. Ensure Python 3.8+ is installed
python3 --version

# 2. Navigate to project directory
cd V4codercli

# 3. Run startup manager
python3 start_rr4_cli.py

# 4. Select option 1 (First-Time Setup)
```

### macOS Setup
```bash
# 1. Install Python 3.8+ (if not already installed)
# Via Homebrew: brew install python@3.9
# Or download from python.org

# 2. Navigate to project directory
cd V4codercli

# 3. Run startup manager
python3 start_rr4_cli.py

# 4. Select option 1 (First-Time Setup)
```

## 📱 **Interactive Menu (Same on All Platforms)**

Once you run the startup script, you'll see:

```
🌐 CROSS-PLATFORM STARTUP INFORMATION
================================================================================

Current Platform: [Your Platform]
Python Version: [Your Python Version]

To start this script on different platforms:
  [Platform-specific commands shown here]

Universal command (all platforms):
  [Universal command for your platform]

🚀 STARTUP OPTIONS:
1. 🎯 FIRST-TIME SETUP (Recommended for new users)
2. 🔍 AUDIT ONLY (Quick connectivity and health check)
3. 📊 FULL COLLECTION (Production data collection)
4. 🎛️ CUSTOM COLLECTION (Advanced users)
5. 🔧 PREREQUISITES CHECK ONLY
6. 🌐 ENHANCED CONNECTIVITY TEST ONLY
7. 📚 SHOW HELP & OPTIONS
0. 🚪 EXIT

Select option (0-7):
```

## 🛠️ **Troubleshooting by Platform**

### Windows Issues

#### Python Not Found
```cmd
# Install Python from python.org
# Or install from Microsoft Store
# Add Python to PATH during installation
```

#### Permission Issues
```cmd
# Run Command Prompt as Administrator
# Or use PowerShell with appropriate execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Antivirus Blocking
- Add V4codercli directory to antivirus exclusions
- Temporarily disable real-time protection during installation

### Linux Issues

#### Python Version
```bash
# Check Python version
python3 --version

# Install Python 3.8+ if needed (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip

# Install Python 3.8+ if needed (RHEL/CentOS/Fedora)
sudo dnf install python3 python3-pip
```

#### Permission Issues
```bash
# Make scripts executable
chmod +x start_rr4_cli.py
chmod +x start_rr4.sh

# Ensure proper file ownership
chown $USER:$USER -R V4codercli/
```

### macOS Issues

#### Python Installation
```bash
# Install via Homebrew (recommended)
brew install python@3.9

# Or download from python.org
# Install Xcode Command Line Tools
xcode-select --install
```

#### SSL Certificate Issues
```bash
# Fix SSL certificates (if needed)
/Applications/Python\ 3.9/Install\ Certificates.command
```

## 🔍 **Verification Steps**

### Verify Python Installation
**Windows:**
```cmd
python --version
python -c "import sys; print(sys.version)"
```

**Linux/macOS:**
```bash
python3 --version
python3 -c "import sys; print(sys.version)"
```

### Verify Script Accessibility
**All Platforms:**
```bash
# Check if script exists
ls -la start_rr4_cli.py

# Check if script is readable
cat start_rr4_cli.py | head -5
```

### Test Dependencies
**All Platforms:**
```bash
# Using the built-in dependency checker
python[3] start_rr4_cli.py
# Select option 5 (Prerequisites Check)
```

## 🚀 **Quick Start Summary**

### For Immediate Use (Any Platform):

1. **Open terminal/command prompt**
2. **Navigate to V4codercli directory**
3. **Run the appropriate command for your platform:**
   - Windows: `python start_rr4_cli.py`
   - Linux: `python3 start_rr4_cli.py`
   - macOS: `python3 start_rr4_cli.py`
4. **Select option 1 for first-time setup**
5. **Follow the guided setup process**

## 📚 **Additional Resources**

- **[README.md](README.md)**: Main documentation
- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)**: Detailed startup guide
- **[INSTALLATION.md](INSTALLATION.md)**: Installation instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Platform-specific troubleshooting

## ✅ **Success Indicators**

You'll know the cross-platform startup is working when you see:
- ✅ Cross-platform startup information displayed
- ✅ Current platform correctly identified
- ✅ Python version shown
- ✅ Interactive menu with 7 options
- ✅ No error messages during startup

---

**Cross-Platform Compatibility**: ✅ **Windows 10/11** | ✅ **Linux** | ✅ **macOS**  
**Python Requirement**: 3.8+  
**Last Updated**: 2025-05-31 