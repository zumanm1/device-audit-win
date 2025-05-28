#!/usr/bin/env python3
"""
Network Audit Tool - Security Audit Module (v3.11)

This module implements the 5-phase security audit approach:
1. Connectivity Verification
2. Authentication Testing
3. Configuration Audit
4. Risk Assessment
5. Reporting and Recommendations

It can be run independently or as part of the comprehensive audit framework.
"""

import os
import sys
import sqlite3
import csv
import time
import datetime
import argparse
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import core functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from audit_core import (
        VERSION, ensure_directories, setup_logging, CredentialManager,
        prompt_for_master_password, AuditResult, AuditReport,
        Fore, Style, colorama_available, DEFAULT_DB_NAME
    )
except ImportError as e:
    print(f"Error importing audit_core module: {e}")
    print("Make sure audit_core.py is in the same directory.")
    sys.exit(1)

# Required third-party modules
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    netmiko_available = True
except ImportError:
    print(f"Warning: netmiko package not available. SSH connectivity will be limited.")
    netmiko_available = False

# Set up module-specific constants
MODULE_NAME = "Security Audit"
AUDIT_TYPE = "security"

# Configure logger
logger, log_file = setup_logging(f"security_audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
if not logger:
    print("Failed to set up logging. Exiting.")
    sys.exit(1)

def initialize_database():
    """Initialize the SQLite database for storing audit results"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', DEFAULT_DB_NAME)
    
    try:
        # Connect to database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create audit_runs table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_runs (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            audit_type TEXT,
            description TEXT
        )
        ''')
        
        # Create audit_results table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_results (
            id TEXT PRIMARY KEY,
            audit_run_id TEXT,
            device_hostname TEXT,
            device_ip TEXT,
            timestamp TEXT,
            phase_name TEXT,
            status TEXT,
            details TEXT,
            error TEXT,
            FOREIGN KEY (audit_run_id) REFERENCES audit_runs (id)
        )
        ''')
        
        # Create audit_recommendations table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_recommendations (
            id TEXT PRIMARY KEY,
            audit_result_id TEXT,
            recommendation TEXT,
            severity TEXT,
            reference TEXT,
            FOREIGN KEY (audit_result_id) REFERENCES audit_results (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        print(f"{Fore.RED}Error initializing database: {e}{Style.RESET_ALL}")
        return False

def log_to_database(audit_run_id, result):
    """Log audit results to the database"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', DEFAULT_DB_NAME)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert results for each phase
        for phase_name, phase_data in result.phases.items():
            result_id = str(uuid.uuid4())
            cursor.execute(
                '''
                INSERT INTO audit_results 
                (id, audit_run_id, device_hostname, device_ip, timestamp, 
                phase_name, status, details, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    result_id,
                    audit_run_id,
                    result.device_info.get('hostname', 'Unknown'),
                    result.device_info.get('ip', result.device_info.get('host', 'Unknown')),
                    result.timestamp.isoformat(),
                    phase_name,
                    phase_data.get('status', 'Unknown'),
                    json.dumps(phase_data.get('details', {})),
                    phase_data.get('error', None)
                )
            )
            
            # Insert recommendations related to this result
            for recommendation in result.recommendations:
                cursor.execute(
                    '''
                    INSERT INTO audit_recommendations
                    (id, audit_result_id, recommendation, severity, reference)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        str(uuid.uuid4()),
                        result_id,
                        recommendation.get('text', ''),
                        recommendation.get('severity', 'medium'),
                        recommendation.get('reference', None)
                    )
                )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error logging to database: {e}")
        return False

class SecurityAuditor:
    """Implements the 5-phase security audit for network devices"""
    
    def __init__(self, test_mode=False, jump_host=None):
        """Initialize the security auditor"""
        self.test_mode = test_mode
        self.devices = []
        self.results = []
        self.timestamp = datetime.datetime.now()
        self.audit_run_id = str(uuid.uuid4())
        self.jump_host = jump_host
        self.jump_conn = None
        self.cred_manager = None
        
        # Initialize database
        initialize_database()
        
        # Print banner
        self.print_banner()
    
    def print_banner(self):
        """Print the module banner"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}NETWORK AUDIT TOOL - {MODULE_NAME} v{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}5-PHASE APPROACH: Connectivity, Authentication, Config, Risk, Reporting{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        if self.test_mode:
            print(f"{Fore.YELLOW}Running in TEST MODE with simulated responses{Style.RESET_ALL}")
        print(f"Started at: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Audit Run ID: {self.audit_run_id}")
        print(f"Log file: {log_file}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def load_devices_from_csv(self, csv_file):
        """Load devices from a CSV file"""
        try:
            if not os.path.exists(csv_file):
                logger.error(f"CSV file not found: {csv_file}")
                print(f"{Fore.RED}Error: CSV file not found: {csv_file}{Style.RESET_ALL}")
                return False
            
            with open(csv_file, 'r') as f:
                # Read the first line to check the format
                header = f.readline().strip()
                f.seek(0)  # Reset file position
                
                # Check if this is routers01.csv format
                is_routers01_format = 'management_ip' in header and 'model_name' in header
                
                if is_routers01_format:
                    logger.info(f"Detected routers01.csv format")
                    print(f"{Fore.GREEN}Detected routers01.csv format{Style.RESET_ALL}")
                
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    # For routers01.csv format
                    if is_routers01_format:
                        if 'hostname' not in row or 'management_ip' not in row:
                            logger.warning(f"Skipping row in routers01.csv: missing required fields")
                            continue
                        
                        # Add device with routers01.csv specific field mapping
                        self.devices.append({
                            'hostname': row['hostname'],
                            'ip': row['management_ip'],
                            'device_type': 'cisco_ios',
                            'username': 'admin', 
                            'password': 'cisco123',
                            'secret': 'cisco123',
                            'enable_password': 'cisco123',
                            'model': row.get('model_name', 'Unknown'),
                            'wan_ip': row.get('wan_ip', 'N/A')
                        })
                    # For standard format
                    else:
                        if 'hostname' not in row or 'ip' not in row:
                            logger.warning(f"Skipping row in CSV: missing required fields")
                            continue
                        
                        self.devices.append({
                            'hostname': row['hostname'],
                            'ip': row['ip'],
                            'device_type': row.get('device_type', 'cisco_ios'),
                            'username': row.get('username', 'admin'),
                            'password': row.get('password', 'cisco123'),
                            'secret': row.get('secret', 'cisco123'),
                            'enable_password': row.get('enable_password', 'cisco123'),
                            'model': row.get('model', 'Unknown')
                        })
            
            if not self.devices:
                logger.warning(f"No valid devices found in {csv_file}")
                print(f"{Fore.YELLOW}Warning: No valid devices found in {csv_file}{Style.RESET_ALL}")
                if self.test_mode:
                    self.create_test_devices()
                    return True
                return False
            
            logger.info(f"Loaded {len(self.devices)} devices from {csv_file}")
            print(f"{Fore.GREEN}Successfully loaded {len(self.devices)} devices from {csv_file}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading devices from CSV: {e}")
            print(f"{Fore.RED}Error loading devices from CSV: {e}{Style.RESET_ALL}")
            if self.test_mode:
                self.create_test_devices()
                return True
            return False
    
    def create_test_devices(self):
        """Create sample test devices for test mode"""
        logger.info("Test mode: Creating sample test data for devices")
        print(f"{Fore.YELLOW}Test mode: Creating sample test data{Style.RESET_ALL}")
        
        # Define sample test devices
        self.devices = [
            {'hostname': 'router1.example.com', 'ip': '192.168.1.1', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123'},
            {'hostname': 'router2.example.com', 'ip': '192.168.1.2', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123'},
            {'hostname': 'switch1.example.com', 'ip': '192.168.1.10', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123'},
            {'hostname': 'switch2.example.com', 'ip': '192.168.1.11', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123'},
            {'hostname': 'firewall.example.com', 'ip': '192.168.1.254', 'device_type': 'cisco_asa',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123'}
        ]
        
        # Create a sample CSV file for reference
        sample_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'data', 'sample_devices.csv')
        try:
            with open(sample_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'hostname', 'ip', 'device_type', 'username', 'password', 
                    'secret', 'enable_password', 'jump_host'
                ])
                writer.writeheader()
                for device in self.devices:
                    writer.writerow(device)
            logger.info(f"Created sample device CSV file: {sample_csv}")
            print(f"{Fore.GREEN}Created sample device CSV file: {sample_csv}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Error creating sample CSV: {e}")
        
        print(f"Using {len(self.devices)} sample test devices:")
        for device in self.devices:
            print(f"  - {device['hostname']} ({device['ip']}) - {device['device_type']}")
        
        return True
