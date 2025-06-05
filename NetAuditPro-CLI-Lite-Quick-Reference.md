# NetAuditPro CLI Lite - Quick Reference Guide

## 🚀 Quick Start
```bash
# Basic usage
python3 rr4-router-complete-enhanced-v3-cli-lite.py

# With custom inventory
python3 rr4-router-complete-enhanced-v3-cli-lite.py --inventory mydevices.csv

# Configure credentials
python3 rr4-router-complete-enhanced-v3-cli-lite.py --config
```

## 📋 Command-Line Options
| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message |
| `--version` | | Show version information |
| `--inventory FILE` | `-i` | Use custom inventory file |
| `--config` | `-c` | Configure credentials only |
| `--quiet` | `-q` | Minimal output (errors only) |
| `--verbose` | `-v` | Detailed debug output |

## 🔧 Default Configuration
```
Jump Host: 172.16.39.128
Jump Username: root
Jump Password: eve
Device Username: cisco
Device Password: cisco
Inventory: routers01.csv
```

## 📊 Inventory Format
```csv
ip_address,hostname,cisco_model,description
172.16.39.100,RTR-CORE-01,Cisco 2911,Core Router
172.16.39.101,RTR-EDGE-02,Cisco 2921,Edge Router
```

## 🔍 Audit Commands
1. `show line` - Line status
2. `show running-config | include ^hostname|^line aux|^ transport input` - AUX audit
3. `show running-config | include ^line vty|^ transport input` - VTY audit
4. `show running-config | include ^line con|^ transport input` - Console audit
5. `show version` - Device version
6. `show running-config` - Full configuration

## 📈 Output Files
```
REPORTS/
├── audit_results_YYYYMMDD_HHMMSS.csv    # CSV summary
├── audit_results_YYYYMMDD_HHMMSS.json   # Detailed JSON
└── audit_summary_YYYYMMDD_HHMMSS.txt    # Executive summary

COMMAND-LOGS/
└── hostname_ip_timestamp.txt            # Command outputs
```

## 🚨 Security Findings
- **AUX Telnet**: `transport input telnet` on AUX line
- **VTY Telnet**: `transport input telnet` on VTY lines
- **Console Telnet**: `transport input telnet` on console
- **Risk Levels**: LOW (0 violations), MEDIUM (1), HIGH (2+)

## 📋 Exit Codes
- **0**: Success
- **1**: Error (config/inventory/audit failure)
- **130**: Interrupted (Ctrl+C)

## 🐛 Troubleshooting
```bash
# Install dependencies
pip3 install paramiko colorama python-dotenv

# Test connectivity
ping 172.16.39.128

# Debug mode
python3 rr4-router-complete-enhanced-v3-cli-lite.py --verbose

# Check inventory format
head -5 routers01.csv
```

## 🔄 Integration Examples
```bash
# Automated script
#!/bin/bash
cd /path/to/netauditpro
python3 rr4-router-complete-enhanced-v3-cli-lite.py --quiet
if [ $? -eq 0 ]; then
    echo "Audit completed successfully"
else
    echo "Audit failed or found violations"
fi

# Cron job (daily at 2 AM)
0 2 * * * cd /path/to/netauditpro && python3 rr4-router-complete-enhanced-v3-cli-lite.py --quiet
```

## 📊 Sample Output
```
Progress: [████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 33.3% (2/6) RTR-EDGE-02

📊 AUDIT SUMMARY STATISTICS
════════════════════════════════════════════════════════════════════════════════
📋 Total Devices Processed: 6
✅ Successful Audits: 2
❌ Failed Audits: 4
⚠️ Telnet Violations: 0
🚨 High Risk Devices: 0
📈 Success Rate: 100.0%
⏱️ Total Duration: 35.2s
```

---
*NetAuditPro CLI Lite v3.0.0-CLI-LITE - Quick Reference* 