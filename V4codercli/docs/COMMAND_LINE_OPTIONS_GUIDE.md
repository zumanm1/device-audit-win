# RR4 CLI Enhanced Command-Line Options Guide

## Overview

The enhanced startup script `start_rr4_cli_enhanced.py` now supports direct command-line execution of all options (0-12), enabling automation and streamlined workflows.

## Key Features

### ✅ **Direct Option Execution**
- Launch any option directly from command line
- Skip interactive menu for automation
- Support for all options 0-12 (excluding option 11)

### ✅ **Automation Support**
- `--quiet` mode for minimal output
- `--no-prereq-check` to skip prerequisites
- Exit codes for scripting integration

### ✅ **Enhanced Help System**
- `--help` shows complete usage information
- `--list-options` displays all available options
- `--version` shows version and platform info

## Command-Line Options

### Basic Usage
```bash
# Interactive menu mode (default)
python3 start_rr4_cli_enhanced.py

# Direct option execution
python3 start_rr4_cli_enhanced.py --option 12

# Quiet mode for automation
python3 start_rr4_cli_enhanced.py --option 2 --quiet
```

### Available Arguments

| Argument | Short | Description |
|----------|--------|-------------|
| `--option N` | `-o N` | Execute option N directly (0-12) |
| `--list-options` | `-l` | List all available options |
| `--version` | `-v` | Show version information |
| `--no-prereq-check` | | Skip prerequisites check |
| `--quiet` | `-q` | Minimize output for automation |
| `--help` | `-h` | Show help message |

## Option Descriptions

| Option | Name | Description |
|--------|------|-------------|
| 0 | 🚪 EXIT | Exit the application |
| 1 | 🎯 FIRST-TIME SETUP | Complete guided setup with prerequisites check |
| 2 | 🔍 AUDIT ONLY | Quick connectivity and health check |
| 3 | 📊 FULL COLLECTION | Production data collection |
| 4 | 🎛️ CUSTOM COLLECTION | Choose specific devices and layers |
| 5 | 🔧 PREREQUISITES CHECK ONLY | Verify system requirements |
| 6 | 🌐 ENHANCED CONNECTIVITY TEST | Comprehensive connectivity test |
| 7 | 📚 SHOW HELP & OPTIONS | Display all available commands |
| 8 | 🎯 CONSOLE AUDIT | Console line discovery and collection |
| 9 | 🌟 COMPLETE COLLECTION | All layers + Console in systematic order |
| 10 | 🔒 CONSOLE SECURITY AUDIT | Transport security analysis |
| 12 | 📊 COMPREHENSIVE STATUS REPORT | All options analysis with device filtering |

## Usage Examples

### Quick Reference Commands
```bash
# Show help
python3 start_rr4_cli_enhanced.py --help

# List all options
python3 start_rr4_cli_enhanced.py --list-options

# Show version
python3 start_rr4_cli_enhanced.py --version
```

### Direct Option Execution
```bash
# Run first-time setup
python3 start_rr4_cli_enhanced.py --option 1

# Run audit only
python3 start_rr4_cli_enhanced.py --option 2

# Run full collection
python3 start_rr4_cli_enhanced.py --option 3

# Run comprehensive status report with device filtering
python3 start_rr4_cli_enhanced.py --option 12
```

### Automation Examples
```bash
# Run prerequisites check only in quiet mode
python3 start_rr4_cli_enhanced.py --option 5 --quiet

# Run audit without prerequisites check (for CI/CD)
python3 start_rr4_cli_enhanced.py --option 2 --no-prereq-check --quiet

# Run complete collection with minimal output
python3 start_rr4_cli_enhanced.py --option 9 --quiet
```

### Scripting Integration
```bash
#!/bin/bash
# Example automation script

echo "Starting RR4 CLI automation..."

# Run prerequisites check
if python3 start_rr4_cli_enhanced.py --option 5 --quiet; then
    echo "Prerequisites OK, running full audit..."
    
    # Run comprehensive audit
    python3 start_rr4_cli_enhanced.py --option 2 --quiet
    
    if [ $? -eq 0 ]; then
        echo "Audit completed successfully"
        
        # Generate comprehensive report
        python3 start_rr4_cli_enhanced.py --option 12 --quiet
        echo "Reports generated"
    else
        echo "Audit failed"
        exit 1
    fi
else
    echo "Prerequisites check failed"
    exit 1
fi
```

## Exit Codes

- **0**: Success
- **1**: Failure or user cancellation

## Platform Support

Works on all supported platforms:
- **Linux**: `python3 start_rr4_cli_enhanced.py`
- **Windows**: `python start_rr4_cli_enhanced.py`
- **macOS**: `python3 start_rr4_cli_enhanced.py`

## Migration from Interactive Mode

### Before (Interactive)
```bash
python3 start_rr4_cli.py
# Then select option 12 from menu
```

### After (Direct)
```bash
python3 start_rr4_cli_enhanced.py --option 12
```

## Benefits

### 🚀 **Automation Ready**
- CI/CD pipeline integration
- Scheduled task execution
- Batch processing support

### ⚡ **Time Saving**
- Skip interactive menu navigation
- Direct option execution
- Streamlined workflows

### 🔧 **Flexible**
- Backward compatible with interactive mode
- Optional prerequisites checking
- Configurable output verbosity

### 📊 **Enterprise Ready**
- Script-friendly exit codes
- Quiet mode for logs
- Version information for tracking

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `start_rr4_cli.py` is in the same directory
2. **Permission Error**: Check file permissions for script execution
3. **Option Not Found**: Use `--list-options` to see available options

### Debug Mode
```bash
# Run with verbose output (default behavior without --quiet)
python3 start_rr4_cli_enhanced.py --option 2

# Check script version
python3 start_rr4_cli_enhanced.py --version
```

## Implementation Notes

- The enhanced script imports functionality from the original `start_rr4_cli.py`
- All original features remain available in interactive mode
- Command-line options extend functionality without breaking existing workflows
- Prerequisites checking can be bypassed for automated environments

---

**Version**: 1.1.0-CrossPlatform-CLI-Enhanced  
**Created**: 2025-06-02  
**Compatible with**: RR4 CLI v2.0.0-Enterprise-Enhanced 