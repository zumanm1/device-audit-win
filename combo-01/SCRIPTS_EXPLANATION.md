# Network Audit Tool v3.11 - Scripts Explanation

This document provides a detailed explanation of each script in the Network Audit Tool v3.11 framework. The framework is designed with a modular architecture that allows each component to function independently or work together as part of a comprehensive network audit solution.

## Table of Contents
1. [Core Module](#1-core-module-audit_corepy)
2. [Connectivity Audit Module](#2-connectivity-audit-module-connectivity_auditpy)
3. [Security Audit Module](#3-security-audit-module-security_auditpy)
4. [Security Audit Phases](#4-security-audit-phases-security_audit_phasespy)
5. [Telnet Audit Module](#5-telnet-audit-module-telnet_auditpy)
6. [Main Framework](#6-main-framework-network_auditpy)

## 1. Core Module (`audit_core.py`)

### Purpose
Provides the foundation for the entire framework, including shared utilities, logging, credential management, and reporting capabilities.

### Key Components
- **Logging System**: Configures logging with colorized output for better readability
- **Credential Manager**: Securely handles device login credentials with encryption
- **Directory Management**: Creates and manages the directory structure for logs, reports, and data
- **Audit Result Class**: Standard data structure for storing and processing audit findings
- **Audit Report Class**: Generates consistent reports across all audit types

### How It's Used
- Imported by all other modules
- Handles cross-cutting concerns that are common to all audit types
- Ensures consistent behavior and output across the framework

## 2. Connectivity Audit Module (`connectivity_audit.py`)

### Purpose
Performs basic network connectivity tests to verify device reachability before deeper security audits.

### Key Components
- **ICMP Ping Testing**: Checks basic network connectivity to devices
- **TCP Port Checking**: Verifies if specific ports are open on target devices
- **DNS Resolution**: Tests if hostnames can be properly resolved
- **Parallel Processing**: Uses multi-threading for efficient testing of multiple devices

### How It's Used
- Can be run independently for basic connectivity audits
- Often used as the first step in the security audit process
- Integrates with the main framework for comprehensive audits

## 3. Security Audit Module (`security_audit.py`)

### Purpose
Orchestrates the 5-phase security audit process, manages device connections, and coordinates the audit workflow.

### Key Components
- **Phased Audit Process**: Implements a systematic approach to security auditing
- **Device Connection Management**: Handles secure connections to network devices
- **Jump Host Support**: Can route connections through a jump host for secure access
- **Credential Handling**: Works with the Credential Manager for secure authentication
- **Reporting**: Collects and consolidates findings from all audit phases

### How It's Used
- Can be run independently for full security audits
- Coordinates with the security_audit_phases.py module to execute each phase
- Integrates with the main framework for comprehensive audits

## 4. Security Audit Phases (`security_audit_phases.py`)

### Purpose
Implements the individual phases of the security audit process, defining the specific checks and analyses for each phase.

### Key Components
- **Phase 1 - Connectivity Verification**: Verifies basic connectivity to the device
- **Phase 2 - Authentication Testing**: Tests login credentials and authentication mechanisms
- **Phase 3 - Configuration Audit**: Examines device configurations for security issues
- **Phase 4 - Risk Assessment**: Analyzes findings to determine security risks
- **Phase 5 - Reporting**: Generates detailed security recommendations

### How It's Used
- Called by the security_audit.py module
- Each phase builds on the results of previous phases
- Follows a structured methodology for comprehensive security assessment

## 5. Telnet Audit Module (`telnet_audit.py`)

### Purpose
Specializes in detecting telnet-related vulnerabilities, which are common security issues in network devices.

### Key Components
- **Telnet Service Detection**: Identifies telnet enabled on VTY lines
- **Insecure Authentication**: Checks for weak or missing authentication on telnet access
- **AUX Port Analysis**: Specifically checks for telnet enabled on auxiliary ports
- **ACL Verification**: Examines access control lists applied to telnet services

### How It's Used
- Can be run independently for focused telnet security assessments
- Provides detailed recommendations for securing telnet access
- Integrates with the main framework for comprehensive audits

## 6. Main Framework (`network_audit.py`)

### Purpose
Serves as the unified entry point for the entire framework, allowing users to select which audit types to run.

### Key Components
- **Command-line Interface**: Provides options for selecting audit types and parameters
- **Audit Orchestration**: Coordinates the execution of different audit modules
- **Unified Reporting**: Combines results from all audit types into comprehensive reports
- **Resource Management**: Manages shared resources and ensures proper initialization

### How It's Used
- Primary entry point for users of the framework
- Allows flexible selection of audit types based on requirements
- Produces consolidated reports covering all selected audit types

## Running the Scripts

### Basic Usage
```bash
# Run all audit types
python network_audit.py --csv devices.csv

# Run specific audit types
python network_audit.py --connectivity --csv devices.csv
python network_audit.py --security --csv devices.csv
python network_audit.py --telnet --csv devices.csv

# Run in test mode with simulated responses
python network_audit.py --test
```

### Running Individual Modules
Each module can also be executed directly:
```bash
python connectivity_audit.py --csv devices.csv
python security_audit.py --csv devices.csv
python telnet_audit.py --csv devices.csv
```

## Design Philosophy

The Network Audit Tool v3.11 is designed with the following principles:

1. **Modularity**: Each component can function independently or as part of the whole
2. **Reusability**: Common functions are centralized in the core module
3. **Consistency**: Standardized interfaces and reporting across all modules
4. **Flexibility**: Different audit types can be combined as needed
5. **Security**: Built-in credential encryption and secure handling of sensitive data

This architecture allows for easy maintenance, extension, and customization of the framework to meet specific network auditing requirements.
