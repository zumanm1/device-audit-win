# Async Line Auditing Guide - NetAuditPro Extension

## Overview

This guide covers the specialized async line auditing functionality designed to focus on specific slot/port-adapter patterns where slot/PA numbers vary but channel indices remain consistent (0-22).

### Target Patterns
- **Slot 0 / PA 1 / channels 0-22** (`line 0/1/*`)
- **Slot 1 / PA 0 / channels 0-22** (`line 1/0/*`)

### Key Features
- 🔍 **Focused extraction** using Cisco IOS section commands
- 🌐 **Telnet enablement detection** with security analysis  
- 🔒 **Security risk assessment** for each async line
- 📋 **Compliance validation** for channel numbering and configuration
- 🛡️ **Credential sanitization** (usernames → `****`, passwords → `####`)

## Files Created

### 1. `async_line_auditor.py`
**Standalone async line auditor script**
- Simulates Cisco IOS commands on dummy-router-configs
- Provides comprehensive async line analysis
- Exports JSON results with detailed findings
- Exit code 0 = PASS, 1 = ISSUES_FOUND

### 2. `cisco_commands_demo.py`  
**Command simulation and demonstration**
- Shows exact router console output
- Demonstrates the three key commands
- Provides practical usage scenarios
- Analyzes command results

### 3. `async_line_integration.py`
**NetAuditPro integration module**
- Integrates with existing audit workflow
- Provides security scoring for async lines
- Generates formatted reports
- Maintains credential sanitization

### 4. `dummy-router-configs` (Enhanced)
**Sample router configuration with async lines**
- 46 total async lines (23 per slot/PA)
- Mixed security configurations
- Telnet and SSH transport options
- Various authentication methods

## Cisco IOS Commands Used

### Command 1: Extract Slot 0/PA 1 lines
```bash
Router# show running-config | section ^line 0\/1\/
```
**Purpose:** Extracts all async line configurations for slot 0, PA 1

### Command 2: Extract Slot 1/PA 0 lines  
```bash
Router# show running-config | section ^line 1\/0\/
```
**Purpose:** Extracts all async line configurations for slot 1, PA 0

### Command 3: Quick line count verification
```bash
Router# show run | include ^line [01]\/[01]\/
```
**Purpose:** Lists just the line headers for quick validation (should show 46 lines total)

## Usage Examples

### Standalone Auditing
```bash
# Run the async line auditor
python3 async_line_auditor.py

# Expected output: Detailed analysis with telnet-enabled lines identified
# Creates: async_line_audit_YYYYMMDD_HHMMSS.json
```

### Command Simulation Demo
```bash
# See what the router commands would return
python3 cisco_commands_demo.py

# Shows exact IOS command output and analysis
```

### NetAuditPro Integration
```python
from async_line_integration import collect_async_line_data, format_async_line_summary

# In the audit workflow
async_data = collect_async_line_data(net_connect, device_name, sanitize_func, log_func)
summary = format_async_line_summary(async_data)
```

## Sample Output Analysis

### From our dummy-router-configs:

#### Summary Statistics
- **Total async lines found:** 46 (23 per slot/PA) ✅
- **Telnet-enabled lines:** 34
- **High-risk lines:** 20 (telnet without authentication)
- **Security issues:** 32 compliance violations

#### Telnet-Enabled Lines by Type
```
🌐 TELNET-ENABLED LINES:
   • 0/1/0 (Management) - Login: local, ACL: MGT-IN
   • 0/1/1 (Console Server) - Login: none, ACL: none  ⚠️ HIGH RISK
   • 0/1/2 (Management) - Login: ASYNC-AUTH, ACL: none
   • 1/0/0 (Management) - Login: local, ACL: LAB2-MGT
   • 1/0/1 (Console Server) - Login: none, ACL: none  ⚠️ HIGH RISK
   [... additional lines ...]
```

#### Compliance Issues Found
```
⚠️ COMPLIANCE ISSUES:
   • Security Risk: 0/1/1 has telnet enabled but no login required
   • Security Risk: 1/0/6 has telnet enabled but no login required
   • Flow Control Warning: 0/1/11 has speed configured but no flow control
   [... additional issues ...]
```

## Security Analysis Features

### Risk Scoring System
Each async line receives a security score based on:
- **Base transport (+10):** Any transport input configured
- **Telnet risk (+20):** Telnet protocol enabled
- **No authentication (+30):** Telnet without login requirement
- **Missing ACL (+15):** Authenticated lines without access-class
- **High privilege (+10):** Privilege level without ACL protection

### Risk Levels
- **LOW (0-19):** SSH-only or transport disabled
- **MEDIUM (20-39):** Telnet with proper authentication/ACLs  
- **HIGH (40+):** Telnet without authentication or missing ACLs

### Security Summary Types
- `Console Server Port (Rotary X)` - Expected for reverse-telnet
- `SECURITY RISK: Telnet with no authentication` - Requires immediate attention
- `Security Warning: Telnet without ACL protection` - Should add access-class
- `Secure Telnet: method auth, ACL: name` - Properly configured
- `Transport disabled or SSH-only` - Secure configuration

## Audit Checklist

### ✅ Channel Number Validation
- Confirms channels 0-22 present on each slot/PA
- Identifies missing or unexpected channel numbers
- Validates slot/PA patterns (0/1/* vs 1/0/*)

### ✅ Security Configuration Review
- **AAA Methods:** `login local`, `login authentication X`, `no login`
- **Access Control:** `access-class ACL-NAME in`
- **Transport Security:** `transport input ssh` vs `transport input telnet`
- **Console Server Ports:** `no exec` + `rotary X` configuration

### ✅ Rotary Group Analysis  
- Unique rotary groups per slot/PA (avoids conflicts)
- Logical grouping (1,2 on first NM; 3,4 on second NM)
- Reverse-telnet port number predictability

### ✅ Speed & Flow Control
- Matching speed settings for connected devices
- Hardware flow control for reliable connections
- Consistent configuration across similar lines

## Integration with NetAuditPro

### Audit Workflow Integration
The async line auditing integrates seamlessly with the existing NetAuditPro workflow:

1. **Collection Phase:** Runs during device data gathering
2. **Analysis Phase:** Processes async line configurations  
3. **Reporting Phase:** Includes async line findings in reports
4. **Web UI Phase:** Displays async line status in dashboard

### Sanitization Integration
All async line data respects the existing credential sanitization:
- **Usernames** → `****`
- **Passwords** → `####`  
- **Autocommand targets** → Sanitized IP addresses
- **Raw configurations** → Cleaned of sensitive data

### Report Integration
Async line findings integrate into existing report formats:
- **PDF Reports:** New async line section with charts
- **Excel Reports:** Async line worksheet with details
- **JSON Data:** Structured async line analysis
- **Web Dashboard:** Real-time async line status

## Practical Use Cases

### 🎯 Use Case 1: Security Audit
**Scenario:** Quarterly security compliance review
**Commands:** Run section commands to identify insecure configurations
**Focus Areas:**
- Lines with telnet but no authentication
- Missing access-class ACLs  
- Inconsistent security policies between similar lines

### 🎯 Use Case 2: Console Server Verification
**Scenario:** Validating console server infrastructure
**Commands:** Extract async lines and verify console server setup
**Focus Areas:**
- `no exec` + rotary group configuration
- Consistent speed/flow control settings
- Reverse-telnet port mapping accuracy

### 🎯 Use Case 3: Capacity Planning
**Scenario:** Verifying all expected async ports are configured
**Commands:** Use include command for quick line count
**Focus Areas:**
- 23 lines per slot/PA (channels 0-22)
- No missing or extra channel numbers
- Proper slot/PA numbering scheme

### 🎯 Use Case 4: Troubleshooting
**Scenario:** Diagnosing async line connectivity issues
**Commands:** Section extraction for detailed analysis
**Focus Areas:**
- Speed mismatches between devices
- Missing flow control causing data corruption
- Conflicting rotary groups

## Command Output Examples

### Router Console Output (Section Command)
```
R3625-Lab# show running-config | section ^line 0\/1\/
line 0/1/0
 login local
 exec-timeout 10 0
 access-class MGT-IN in
 transport input telnet
 flowcontrol hardware
 speed 9600
!
line 0/1/1
 no exec
 rotary 1
 transport input telnet
 flowcontrol hardware
!
[... continues for all 0/1/* lines ...]
```

### Include Command Output
```
R3625-Lab# show run | include ^line [01]\/[01]\/
line 0/1/0
line 0/1/1
line 0/1/2
[... all 46 line headers ...]
line 1/0/20
line 1/0/21
line 1/0/22
```

## JSON Export Format

### Audit Results Structure
```json
{
  "timestamp": "2024-01-15T14:30:25",
  "summary": {
    "slot_0_pa_1_lines": 23,
    "slot_1_pa_0_lines": 23,
    "total_async_lines": 46,
    "telnet_enabled_count": 34,
    "compliance_issues_count": 32,
    "audit_status": "ISSUES_FOUND"
  },
  "telnet_enabled_lines": [
    {
      "line_id": "0/1/0",
      "slot_pa": "0/1", 
      "channel": 0,
      "transport_input": ["telnet"],
      "login_method": "local",
      "access_class": "MGT-IN",
      "is_console_server": false
    }
  ],
  "compliance_issues": [
    "Security Risk: 0/1/1 has telnet enabled but no login required"
  ],
  "detailed_configs": {
    "slot_0_pa_1": { /* AsyncLineConfig objects */ },
    "slot_1_pa_0": { /* AsyncLineConfig objects */ }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. No Async Lines Found
**Symptom:** Zero lines detected  
**Cause:** Config file missing or incorrect pattern
**Solution:** Verify dummy-router-configs exists and contains async line configs

#### 2. Parsing Errors
**Symptom:** Configuration blocks not parsed correctly
**Solution:** Check for malformed config blocks, ensure proper `!` delimiters

#### 3. High Security Scores
**Symptom:** Many lines flagged as high-risk
**Solution:** Review telnet configurations, add authentication and ACLs

#### 4. Missing Channels
**Symptom:** Compliance issues about missing channels 0-22
**Solution:** Verify all expected async ports are configured in config file

## Best Practices

### 1. Security Configuration
- Always require authentication for telnet lines
- Apply access-class ACLs to restrict access
- Use SSH-only transport where possible
- Implement proper TACACS+ authentication

### 2. Console Server Configuration  
- Use `no exec` for pure console server ports
- Configure logical rotary groups
- Ensure consistent speed/flow control
- Document reverse-telnet port mappings

### 3. Regular Auditing
- Run async line audits quarterly
- Monitor for configuration drift
- Validate after any async line changes
- Include in security compliance reporting

### 4. Integration Practices
- Use sanitization functions for all logging
- Integrate with existing audit workflows
- Export results for compliance tracking
- Include in automated report generation

## Conclusion

The async line auditing solution provides focused, security-aware analysis of router async line configurations. By targeting the specific slot/PA patterns mentioned (0/1/* and 1/0/* with channels 0-22), it delivers actionable insights for network security and compliance while integrating seamlessly with the existing NetAuditPro application. 