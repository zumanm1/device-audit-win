#!/usr/bin/env python3
"""
Cisco Router Audit Script - Phased Approach
Implements multi-phase audit process with jump host connectivity
"""
import os
import logging
import csv
import json
import os
import sys
import getpass
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import paramiko
from pathlib import Path
import sqlite3
import uuid
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Custom colored formatter for console output
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.ERROR: Fore.RED + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class AuditReporter:
    """Unified reporting class for both simple and advanced audit modes"""
    
    def __init__(self, timestamp=None, report_dir="reports"):
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = report_dir
        self.results = []
        self.report_files = {
            "csv": None,
            "txt": None,
            "html": None,
            "json": None
        }
        
        # Ensure the reports directory exists
        os.makedirs(self.report_dir, exist_ok=True)
    
    def add_result(self, device, phase_results):
        """Add a device's audit results to the report"""
        result = {
            "device": device,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phases": phase_results
        }
        self.results.append(result)
        return result
    
    def generate_csv_report(self):
        """Generate a CSV report of audit results"""
        csv_file = os.path.join(self.report_dir, f"device_audit_report_{self.timestamp}.csv")
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['hostname', 'ip', 'phase', 'status', 'details', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                device = result["device"]
                for phase_name, phase_data in result["phases"].items():
                    writer.writerow({
                        'hostname': device.get('hostname', 'Unknown'),
                        'ip': device.get('host', 'Unknown'),
                        'phase': phase_name,
                        'status': phase_data.get('status', 'Unknown'),
                        'details': phase_data.get('details', ''),
                        'timestamp': result["timestamp"]
                    })
        
        self.report_files["csv"] = csv_file
        logger.info(f"CSV report saved to {csv_file}")
        return csv_file
    
    def generate_text_report(self):
        """Generate a text report with detailed audit results"""
        txt_file = os.path.join(self.report_dir, f"device_audit_report_{self.timestamp}.txt")
        with open(txt_file, 'w') as f:
            f.write(f"==== CISCO ROUTER AUDIT REPORT ====\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in self.results:
                device = result["device"]
                f.write(f"\n{'='*50}\n")
                f.write(f"Device: {device.get('hostname', 'Unknown')} ({device.get('host', 'Unknown')})\n")
                f.write(f"Model: {device.get('model', 'Unknown')}\n")
                f.write(f"Audit Time: {result['timestamp']}\n\n")
                
                # Write phase results
                for phase_name, phase_data in result["phases"].items():
                    status = phase_data.get('status', 'Unknown')
                    status_symbol = "✓" if status == "Success" else "✗"
                    f.write(f"{status_symbol} Phase: {phase_name} - Status: {status}\n")
                    if 'details' in phase_data and phase_data['details']:
                        f.write(f"   Details: {phase_data['details']}\n")
                    if 'recommendations' in phase_data and phase_data['recommendations']:
                        f.write(f"   Recommendations: {phase_data['recommendations']}\n")
                    f.write("\n")
        
        self.report_files["txt"] = txt_file
        logger.info(f"Text report saved to {txt_file}")
        return txt_file
    
    def generate_json_report(self):
        """Generate a JSON report with full audit data"""
        json_file = os.path.join(self.report_dir, f"device_audit_report_{self.timestamp}.json")
        
        # Convert results to serializable format
        serializable_results = []
        for result in self.results:
            serializable_result = {
                "device": {
                    "hostname": result["device"].get('hostname', 'Unknown'),
                    "ip": result["device"].get('host', 'Unknown'),
                    "model": result["device"].get('model', 'Unknown')
                },
                "timestamp": result["timestamp"],
                "phases": result["phases"]
            }
            serializable_results.append(serializable_result)
        
        with open(json_file, 'w') as f:
            json.dump({
                "audit_timestamp": self.timestamp,
                "report_generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "results": serializable_results
            }, f, indent=4)
        
        self.report_files["json"] = json_file
        logger.info(f"JSON report saved to {json_file}")
        return json_file
    
    def generate_all_reports(self):
        """Generate all report formats"""
        self.generate_csv_report()
        self.generate_text_report()
        self.generate_json_report()
        return self.report_files
    
    def print_summary(self):
        """Print a summary of the audit results to the console"""
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}AUDIT SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Count statistics
        total_devices = len(self.results)
        phase_stats = {}
        
        # Initialize phase statistics
        all_phases = set()
        for result in self.results:
            all_phases.update(result["phases"].keys())
        
        for phase in all_phases:
            phase_stats[phase] = {"success": 0, "failure": 0, "total": 0}
        
        # Calculate statistics
        for result in self.results:
            for phase_name, phase_data in result["phases"].items():
                status = phase_data.get('status', 'Unknown')
                phase_stats[phase_name]["total"] += 1
                if status == "Success":
                    phase_stats[phase_name]["success"] += 1
                else:
                    phase_stats[phase_name]["failure"] += 1
        
        # Print device count
        print(f"\nTotal Devices Audited: {total_devices}")
        
        # Print phase statistics
        print("\nPhase Results:")
        for phase_name, stats in phase_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            status_color = Fore.GREEN if success_rate >= 75 else (Fore.YELLOW if success_rate >= 50 else Fore.RED)
            print(f"{status_color}{phase_name}: {stats['success']}/{stats['total']} successful ({success_rate:.1f}%){Style.RESET_ALL}")
        
        # Print report file locations
        print(f"\n{Fore.CYAN}Report Files:{Style.RESET_ALL}")
        for report_type, file_path in self.report_files.items():
            if file_path:
                print(f"  - {report_type.upper()}: {file_path}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

# Set up logging to file and console
def setup_logging():
    """Set up logging configuration"""
    # Create logs directory with full visibility on permissions issues
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    print(f"Creating logs directory at: {log_dir}")
    try:
        os.makedirs(log_dir, exist_ok=True)
        print(f"Successfully created/verified logs directory")
    except Exception as e:
        print(f"ERROR creating logs directory: {e}")
        # Fallback to current directory
        log_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Falling back to current directory for logs: {log_dir}")
    
    # Generate log filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'device_audit_{timestamp}.log')
    print(f"Log file will be: {log_file}")
    
    try:
        # Test if we can write to the log file
        with open(log_file, 'w') as f:
            f.write(f"Log initialized at {timestamp}\n")
        print(f"Successfully created log file")
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add colored console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(ColoredFormatter())
        
        # Configure logger
        logger.handlers = []  # Clear any existing handlers
        logger.addHandler(file_handler)
        logger.addHandler(console)
        
        logger.info(f"Logging configured. Log file: {log_file}")
        print(f"Logging system initialized. Log file: {log_file}")
    except Exception as e:
        print(f"ERROR setting up logging: {e}")
        # Set up console-only logging as fallback
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(ColoredFormatter())
        logger.handlers = [console]
        logger.info("Logging to console only due to file access error")
        print("Logging to console only due to file access error")
        log_file = None
        
    return log_file

# Credential Manager for secure password handling
class CredentialManager:
    """Handles encryption and decryption of sensitive credentials"""
    
    def __init__(self, master_password=None):
        """Initialize with optional master password"""
        self.master_password = master_password
        
    def initialize(self, master_password):
        """Initialize with master password"""
        self.master_password = master_password
    
    def encrypt(self, plaintext):
        """Simulate encryption for development purposes"""
        # In a real implementation, use proper encryption
        logger.debug("Encrypting sensitive data")
        return f"ENCRYPTED_{plaintext}_ENCRYPTED"
    
    def decrypt(self, encrypted_text):
        """Simulate decryption for development purposes"""
        # In a real implementation, use proper decryption
        logger.debug("Decrypting sensitive data")
        if encrypted_text.startswith("ENCRYPTED_") and encrypted_text.endswith("_ENCRYPTED"):
            return encrypted_text[10:-10]  # Remove the prefix and suffix
        return encrypted_text

# Main Device Auditor class
class DeviceAuditor:
    """
    Handles the multi-phase audit process for network devices
    """
    def __init__(self, test_mode=True):
        # Test mode flag
        self.test_mode = test_mode
        
        # Default jump host configuration
        self.jump_host = {
            "device_type": "linux",
            "host": "172.16.39.128",  # Default jump host
            "username": "root",       # Default username
            "password": None          # Will be set during configuration
        }
        
        # Initialize collections
        self.devices = []             # List of devices to audit
        self.results = []             # Audit results for reporting
        self.cred_manager = CredentialManager()
        self.master_password = None
        
        # Timing variables
        self.start_time = None
        self.end_time = None
        self.phase_times = {
            "connectivity": {},       # Device-specific connectivity phase times
            "authentication": {},     # Device-specific authentication phase times
            "config_audit": {},       # Device-specific config audit phase times
            "data_collection": {},    # Device-specific data collection phase times
            "analysis": {}            # Device-specific analysis phase times
        }
        
        # Jump host connection
        self.jump_conn = None
        
        # Create unique run ID for this audit session
        self.run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = f"device-extracted{self.run_id}"
    
    def prompt_for_credentials(self):
        """Prompt user for jump host and router credentials"""
        if self.test_mode:
            print(f"{Fore.YELLOW}[TEST MODE] Using default test credentials{Style.RESET_ALL}")
            logger.info("[TEST MODE] Using default test credentials")
            self.master_password = "temp_master_password_for_testing"
            self.jump_host['password'] = "temp_jump_password_for_testing"
            return
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}CONFIGURATION SETUP{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Ask for master password for credential encryption
        print(f"\n{Fore.YELLOW}Master Password Setup{Style.RESET_ALL}")
        self.master_password = getpass.getpass(f"Enter master password for credential encryption: ")
        self.cred_manager.initialize(self.master_password)
        
        # Jump Host Configuration
        print(f"\n{Fore.YELLOW}Jump Host Configuration{Style.RESET_ALL}")
        print(f"Current Jump Host: {self.jump_host['host']}")
        print(f"Current Username: {self.jump_host['username']}")
        
        # Prompt for new values or keep existing ones
        new_host = input(f"Enter jump host IP [{self.jump_host['host']}]: ").strip()
        if new_host:
            self.jump_host['host'] = new_host
        
        new_username = input(f"Enter jump host username [{self.jump_host['username']}]: ").strip()
        if new_username:
            self.jump_host['username'] = new_username
        
        self.jump_host['password'] = getpass.getpass(f"Enter jump host password: ")
        
        # Default Router Credentials
        print(f"\n{Fore.YELLOW}Default Router Credentials{Style.RESET_ALL}")
        print("These will be used for all routers unless specified in the CSV file")
        
        self.default_router_username = input("Enter default router username [admin]: ").strip() or "admin"
        self.default_router_password = getpass.getpass("Enter default router password [cisco]: ") or "cisco"
        self.default_router_enable = getpass.getpass("Enter default router enable password [enable]: ") or "enable"
        
        print(f"\n{Fore.GREEN}✓ Configuration saved{Style.RESET_ALL}")
        logger.info(f"User configured jump host: {self.jump_host['host']} (user: {self.jump_host['username']})")
        logger.info(f"User configured default router credentials: user={self.default_router_username}")
        
    def load_environment(self):
        """Load or create .env file with jump host configuration"""
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        
        # Initialize with defaults
        self.default_router_username = "admin"
        self.default_router_password = "cisco"
        self.default_router_enable = "enable"
        
        if os.path.exists(env_file) and not self.test_mode:
            logger.info(f"Loading jump host configuration from .env file")
            print(f"{Fore.CYAN}Loading jump host configuration from .env file{Style.RESET_ALL}")
            
            # Load configuration from .env file
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'JUMP_HOST':
                            self.jump_host['host'] = value
                        elif key == 'JUMP_USERNAME':
                            self.jump_host['username'] = value
                        elif key == 'JUMP_HOST_PASSWORD':
                            # Decrypt password if it's encrypted
                            try:
                                # We'll prompt for master password later
                                pass
                            except Exception as e:
                                logger.error(f"Failed to decrypt jump host password: {e}")
                        elif key == 'DEFAULT_ROUTER_USERNAME':
                            self.default_router_username = value
                        elif key == 'DEFAULT_ROUTER_PASSWORD':
                            # Will be decrypted later
                            pass
                        elif key == 'DEFAULT_ROUTER_ENABLE':
                            # Will be decrypted later
                            pass
            
            logger.info(f"Loaded initial jump host configuration from .env: {self.jump_host['host']} (user: {self.jump_host['username']})")
        else:
            # Use defaults for initial setup
            if self.test_mode:
                logger.info(f"[TEST MODE] Using default jump host configuration")
                self.jump_host['password'] = "temp_jump_password_for_testing"
                self.master_password = "temp_master_password_for_testing"
                self.cred_manager.initialize(self.master_password)
            else:
                logger.info(f"No .env file found or using fresh configuration")
                print(f"{Fore.YELLOW}No saved configuration found. You will be prompted for credentials.{Style.RESET_ALL}")
        
        # Always prompt for credentials in interactive mode unless in test mode
        if not self.test_mode:
            self.prompt_for_credentials()
    
    def load_devices_from_csv(self, csv_file="routers01.csv"):
        """Load device configurations from CSV file"""
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_file)
        
        # Handle missing CSV file
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            print(f"{Fore.RED}\u26a0\ufe0f Error: CSV file not found: {csv_path}{Style.RESET_ALL}")
            
            # If we're in test mode and the specified file doesn't exist, use backup test data
            if self.test_mode:
                print(f"{Fore.YELLOW}Test mode: Creating sample test data{Style.RESET_ALL}")
                logger.info("Test mode: Creating sample test data for devices")
                
                # Create test devices directly
                self.devices = [
                    {
                        'hostname': 'RTR-BRANCH-01.xrnet.net',
                        'host': '172.16.39.101',
                        'device_type': 'cisco_ios',
                        'username': self.default_router_username,
                        'password': self.default_router_password,
                        'secret': self.default_router_enable,
                        'model': 'Cisco 2901'
                    },
                    {
                        'hostname': 'RTR-BRANCH-02.xrnet.net',
                        'host': '172.16.39.102',
                        'device_type': 'cisco_ios',
                        'username': self.default_router_username,
                        'password': self.default_router_password,
                        'secret': self.default_router_enable,
                        'model': 'Cisco 2911'
                    },
                    {
                        'hostname': 'RTR-BRANCH-03.xrnet.net',
                        'host': '172.16.39.103',
                        'device_type': 'cisco_ios',
                        'username': self.default_router_username,
                        'password': self.default_router_password,
                        'secret': self.default_router_enable,
                        'model': 'Cisco 3925'
                    },
                    {
                        'hostname': 'RTR-BRANCH-04.xrnet.net',
                        'host': '172.16.39.104',
                        'device_type': 'cisco_ios',
                        'username': self.default_router_username,
                        'password': self.default_router_password,
                        'secret': self.default_router_enable,
                        'model': 'Cisco 2921'
                    },
                    {
                        'hostname': 'RTR-BRANCH-05.xrnet.net',
                        'host': '172.16.39.105',
                        'device_type': 'cisco_ios',
                        'username': self.default_router_username,
                        'password': self.default_router_password,
                        'secret': self.default_router_enable,
                        'model': 'Cisco 3945'
                    }
                ]
                
                # Try to create the CSV file for future use
                try:
                    with open(csv_path, 'w', newline='') as f:
                        fieldnames = ['hostname', 'host', 'device_type', 'username', 'password', 'secret', 'model']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for device in self.devices:
                            writer.writerow(device)
                    print(f"{Fore.GREEN}Created sample device CSV file: {csv_file}{Style.RESET_ALL}")
                    logger.info(f"Created sample device CSV file: {csv_file}")
                except Exception as e:
                    logger.warning(f"Could not create sample CSV file: {e}")
                    print(f"{Fore.YELLOW}Note: Could not create sample CSV file, but test will continue with sample data{Style.RESET_ALL}")
                
                # Display summary of loaded devices
                print(f"{Fore.GREEN}Using {len(self.devices)} sample test devices:{Style.RESET_ALL}")
                for device in self.devices:
                    print(f"  - {device['hostname']} ({device['host']}) - {device['model']}")
                print("")
                
                return True
            return False
        
        try:
            # Check if file is empty
            if os.path.getsize(csv_path) == 0:
                logger.error(f"CSV file is empty: {csv_path}")
                print(f"{Fore.RED}\u26a0\ufe0f Error: CSV file is empty: {csv_path}{Style.RESET_ALL}")
                
                if self.test_mode:
                    # Handle empty file in test mode - same as file not found
                    print(f"{Fore.YELLOW}Test mode: Creating sample test data{Style.RESET_ALL}")
                    return self.load_devices_from_csv("__nonexistent_file__.csv")
                return False
            
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Ensure required fields are present
                    if 'hostname' not in row or 'host' not in row:
                        logger.warning(f"Skipping row in CSV: missing required fields")
                        continue
                    
                    # Add device to list with default credentials if not specified
                    self.devices.append({
                        'hostname': row['hostname'],
                        'host': row['host'],
                        'device_type': row.get('device_type', 'cisco_ios'),
                        'username': row.get('username', self.default_router_username),
                        'password': row.get('password', self.default_router_password),
                        'secret': row.get('secret', self.default_router_enable),
                        'model': row.get('model', 'Unknown')
                    })
            
            # Display summary of loaded devices
            if self.devices:
                print(f"{Fore.GREEN}Successfully loaded {len(self.devices)} devices from {csv_file}:{Style.RESET_ALL}")
                for device in self.devices:
                    print(f"  - {device['hostname']} ({device['host']}) - {device['model']}")
                print("")
            else:
                print(f"{Fore.YELLOW}Warning: No valid devices found in {csv_file}.{Style.RESET_ALL}")
                print(f"Please make sure the CSV file contains at least 'hostname' and 'host' columns.")
                print(f"Other optional columns: device_type, username, password, secret, model\n")
                
                if self.test_mode:
                    # Handle valid but empty CSV in test mode
                    print(f"{Fore.YELLOW}Test mode: Creating sample test data since no devices were found{Style.RESET_ALL}")
                    return self.load_devices_from_csv("__nonexistent_file__.csv")
            
            logger.info(f"Loaded {len(self.devices)} devices from {csv_file}")
            return len(self.devices) > 0
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            print(f"{Fore.RED}\u26a0\ufe0f Error loading CSV file: {e}{Style.RESET_ALL}")
            
            if self.test_mode:
                # Handle errors in test mode
                print(f"{Fore.YELLOW}Test mode: Creating sample test data due to CSV error{Style.RESET_ALL}")
                return self.load_devices_from_csv("__nonexistent_file__.csv")
            return False
    
    def connect_to_jump_host(self):
        """Establish connection to jump host"""
        logger.info(f"Connecting to jump host {self.jump_host['host']}...")
        print(f"{Fore.CYAN}Connecting to jump host {self.jump_host['host']}...{Style.RESET_ALL}")
        
        # If in test mode, simulate a successful connection
        if self.test_mode:
            logger.info(f"[TEST MODE] Simulating connection to jump host {self.jump_host['host']}")
            print(f"{Fore.CYAN}[TEST MODE] Simulating jump host connection{Style.RESET_ALL}")
            
            # Create a simple test object to simulate the connection
            class TestConnection:
                def __init__(self):
                    self.device_type = "linux"
                    self.host = "172.16.39.128"
                    self.username = "root"
                
                def send_command(self, command):
                    # Simulate ping responses
                    if "ping" in command:
                        host = command.split()[-1]
                        # Fail ping for specific test cases (e.g. .104)
                        if host.endswith(".104"):
                            return "PING 172.16.39.104 (172.16.39.104) 56(84) bytes of data.\n0 packets transmitted, 0 received, 100% packet loss"
                        else:
                            return f"PING {host} ({host}) 56(84) bytes of data.\n4 packets transmitted, 4 received, 0% packet loss"
                    return "Command executed successfully"
                
                def write_channel(self, text):
                    # Just store the last command sent
                    self.last_command = text
                    pass
                
                def read_channel(self):
                    # Simulate appropriate responses based on the last command
                    if hasattr(self, 'last_command'):
                        if "ssh" in self.last_command:
                            # SSH command detected, return password prompt
                            return "root@172.16.39.128's password: "
                        elif "assword" in self.last_command:
                            # Password sent, return success prompt
                            if ".105" in self.last_command:
                                # Fail authentication for .105 for testing
                                return "Permission denied, please try again."
                            return "Router#"
                        elif "show line" in self.last_command:
                            # Return sample show line output with some telnet enabled lines
                            sample_output = """Line    Aux   Baud    Modem     Inout     Flow Type
  0/0/0   -      9600    -        -        -    AUX 
* 0/0/1   -      9600    -        telnet    -    AUX  
Line(s) not in async mode -or- with flow control options
1/0/0     Role: Network-Access"""
                            return sample_output
                    return ""
                
                def disconnect(self):
                    # Nothing to do for test mode
                    pass
            
            self.jump_conn = TestConnection()
            logger.info(f"[TEST MODE] Successfully connected to jump host {self.jump_host['host']}")
            print(f"{Fore.GREEN}✓ [TEST MODE] Successfully connected to jump host{Style.RESET_ALL}")
            return True
            
        # Normal mode with actual connection attempt
        try:
            self.jump_conn = ConnectHandler(
                device_type=self.jump_host['device_type'],
                host=self.jump_host['host'],
                username=self.jump_host['username'],
                password=self.jump_host['password']
            )
            
            logger.info(f"Successfully connected to jump host {self.jump_host['host']}")
            print(f"{Fore.GREEN}✓ Successfully connected to jump host{Style.RESET_ALL}")
            return True
        except NetMikoTimeoutException:
            logger.error(f"Connection to jump host timed out")
            print(f"{Fore.RED}⚠️ Connection to jump host timed out{Style.RESET_ALL}")
            return False
        except NetMikoAuthenticationException:
            logger.error(f"Authentication to jump host failed")
            print(f"{Fore.RED}⚠️ Authentication to jump host failed{Style.RESET_ALL}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to jump host: {e}")
            print(f"{Fore.RED}⚠️ Error connecting to jump host: {e}{Style.RESET_ALL}")
            return False
    
    # A1: Ping the device
    def ping_device(self, device):
        """Phase A1: Test connectivity to a device with ping from jump host"""
        host = device['host']
        hostname = device['hostname']
        
        # Record start time for this phase
        start_time = datetime.datetime.now()
        self.phase_times['connectivity'][host] = {'start': start_time}
        
        logger.info(f"A1: Testing connectivity to {hostname} ({host}) with ping...")
        print(f"\n{Fore.CYAN}A1: Testing connectivity to {hostname} ({host}) with ping...{Style.RESET_ALL}")
        
        # Initialize result dictionary for this device if not exists
        device_result = next((r for r in self.results if r['host'] == host), None)
        if not device_result:
            device_result = {
                'hostname': hostname,
                'host': host,
                'connectivity': False,
                'authentication': False,
                'authorization': False,
                'data_collection': False,
                'analysis': False,
                'telnet_enabled': False,
                'aux_lines': [],
                'vty_lines': [],
                'con_lines': [],
                'error': None,
                'commands_executed': []
            }
            self.results.append(device_result)
        
        if not self.jump_conn:
            logger.error(f"Jump host connection not established")
            device_result['error'] = "Jump host connection not established"
            device_result['connectivity'] = False
            self.phase_times['connectivity'][host]['end'] = datetime.datetime.now()
            return False
        
        try:
            # Execute ping command on jump host
            ping_command = f"ping -c 4 {host}"
            output = self.jump_conn.send_command(ping_command)
            
            if '0 received' in output or 'Destination Host Unreachable' in output:
                logger.warning(f"A1: Ping to {hostname} ({host}) failed")
                print(f"{Fore.YELLOW}⚠️ A1: Ping to {hostname} ({host}) failed{Style.RESET_ALL}")
                device_result['connectivity'] = False
                # Record end time and continue to A2 anyway as requested
                self.phase_times['connectivity'][host]['end'] = datetime.datetime.now()
                return False
            else:
                logger.info(f"A1: Ping to {hostname} ({host}) successful")
                print(f"{Fore.GREEN}✓ A1: Ping to {hostname} ({host}) successful{Style.RESET_ALL}")
                device_result['connectivity'] = True
                self.phase_times['connectivity'][host]['end'] = datetime.datetime.now()
                return True
        except Exception as e:
            logger.error(f"A1: Error pinging {hostname} ({host}): {e}")
            print(f"{Fore.RED}✗ A1: Error pinging {hostname} ({host}): {e}{Style.RESET_ALL}")
            device_result['connectivity'] = False
            device_result['error'] = f"Ping error: {str(e)}"
            self.phase_times['connectivity'][host]['end'] = datetime.datetime.now()
            return False
    
    # A2: SSH to the router
    def ssh_to_device(self, device):
        """Phase A2: SSH to the router and authenticate"""
        host = device['host']
        hostname = device['hostname']
        username = device['username']
        password = device['password']
        device_type = device['device_type']
        
        # Record start time for this phase
        start_time = datetime.datetime.now()
        self.phase_times['authentication'][host] = {'start': start_time}
        
        logger.info(f"A2: Authenticating to {hostname} ({host}) via SSH...")
        print(f"\n{Fore.CYAN}A2: Authenticating to {hostname} ({host}) via SSH...{Style.RESET_ALL}")
        
        # Get device result dictionary
        device_result = next((r for r in self.results if r['host'] == host), None)
        if not device_result:
            # This should not happen if ping_device was called first
            logger.error(f"Device result not found for {hostname} ({host})")
            return False, None
        
        if not self.jump_conn:
            logger.error(f"Jump host connection not established")
            device_result['error'] = "Jump host connection not established"
            device_result['authentication'] = False
            self.phase_times['authentication'][host]['end'] = datetime.datetime.now()
            return False, None
        
        try:
            # Create a proxy command through the jump host
            proxy_command = f"ssh {username}@{host}"
            # Send the proxy command
            self.jump_conn.write_channel(f"{proxy_command}\n")
            time.sleep(2)  # Wait for SSH prompt
            
            # Check for password prompt
            output = self.jump_conn.read_channel()
            if 'assword' in output:
                # Send password
                self.jump_conn.write_channel(f"{password}\n")
                time.sleep(2)  # Wait for authentication
                
                # Check for successful login
                output = self.jump_conn.read_channel()
                if '#' in output or '>' in output:
                    logger.info(f"A2: Authentication to {hostname} ({host}) successful")
                    print(f"{Fore.GREEN}✓ A2: Authentication to {hostname} ({host}) successful{Style.RESET_ALL}")
                    device_result['authentication'] = True
                    self.phase_times['authentication'][host]['end'] = datetime.datetime.now()
                    return True, self.jump_conn
                else:
                    logger.error(f"A2: Authentication to {hostname} ({host}) failed")
                    print(f"{Fore.RED}✗ A2: Authentication to {hostname} ({host}) failed{Style.RESET_ALL}")
                    device_result['authentication'] = False
                    device_result['error'] = "Authentication failed"
                    self.phase_times['authentication'][host]['end'] = datetime.datetime.now()
                    return False, None
            else:
                logger.error(f"A2: No password prompt received from {hostname} ({host})")
                print(f"{Fore.RED}✗ A2: No password prompt received from {hostname} ({host}){Style.RESET_ALL}")
                device_result['authentication'] = False
                device_result['error'] = "No password prompt"
                self.phase_times['authentication'][host]['end'] = datetime.datetime.now()
                return False, None
        except Exception as e:
            logger.error(f"A2: Error authenticating to {hostname} ({host}): {e}")
            print(f"{Fore.RED}✗ A2: Error authenticating to {hostname} ({host}): {e}{Style.RESET_ALL}")
            device_result['authentication'] = False
            device_result['error'] = f"Authentication error: {str(e)}"
            self.phase_times['authentication'][host]['end'] = datetime.datetime.now()
            return False, None
    
    # A3-A4: Check authorization and command execution
    def check_authorization(self, device, device_conn):
        """Phase A3-A4: Check authorization by sending 'show line' command"""
        host = device['host']
        hostname = device['hostname']
        
        # Record start time for this phase
        start_time = datetime.datetime.now()
        self.phase_times['config_audit'][host] = {'start': start_time}
        
        logger.info(f"A3: Checking authorization on {hostname} ({host}) with 'show line' command...")
        print(f"\n{Fore.CYAN}A3: Checking authorization on {hostname} ({host}) with 'show line' command...{Style.RESET_ALL}")
        
        # Get device result dictionary
        device_result = next((r for r in self.results if r['host'] == host), None)
        if not device_result:
            logger.error(f"Device result not found for {hostname} ({host})")
            return False, None
        
        if not device_conn:
            logger.error(f"Device connection not established")
            device_result['authorization'] = False
            device_result['error'] = "Device connection not established"
            self.phase_times['config_audit'][host]['end'] = datetime.datetime.now()
            return False, None
        
        try:
            # Send 'show line' command
            command = "show line"
            device_result['commands_executed'].append(command)
            device_conn.write_channel(f"{command}\n")
            
            # A4: Wait 3 seconds as requested before checking response
            print(f"{Fore.CYAN}A4: Waiting 3 seconds for command completion...{Style.RESET_ALL}")
            time.sleep(3)
            
            # Read response
            output = device_conn.read_channel()
            
            if 'Invalid input' in output or 'Error' in output:
                logger.error(f"A3: Command execution failed on {hostname} ({host})")
                print(f"{Fore.RED}✗ A3: Command execution failed on {hostname} ({host}){Style.RESET_ALL}")
                device_result['authorization'] = False
                device_result['error'] = "Command execution failed"
                self.phase_times['config_audit'][host]['end'] = datetime.datetime.now()
                return False, None
            else:
                logger.info(f"A3: Command executed successfully on {hostname} ({host})")
                print(f"{Fore.GREEN}✓ A3: Command executed successfully on {hostname} ({host}){Style.RESET_ALL}")
                device_result['authorization'] = True
                self.phase_times['config_audit'][host]['end'] = datetime.datetime.now()
                return True, output
        except Exception as e:
            logger.error(f"A3: Error executing command on {hostname} ({host}): {e}")
            print(f"{Fore.RED}✗ A3: Error executing command on {hostname} ({host}): {e}{Style.RESET_ALL}")
            device_result['authorization'] = False
            device_result['error'] = f"Command execution error: {str(e)}"
            self.phase_times['config_audit'][host]['end'] = datetime.datetime.now()
            return False, None
    
    # A5: Save collected data
    def save_device_data(self, device, command_output):
        """Phase A5: Save collected data to a unique folder"""
        host = device['host']
        hostname = device['hostname']
        
        # Record start time for this phase
        start_time = datetime.datetime.now()
        self.phase_times['data_collection'][host] = {'start': start_time}
        
        logger.info(f"A5: Saving data for {hostname} ({host})...")
        print(f"\n{Fore.CYAN}A5: Saving data for {hostname} ({host})...{Style.RESET_ALL}")
        
        # Get device result dictionary
        device_result = next((r for r in self.results if r['host'] == host), None)
        if not device_result:
            logger.error(f"Device result not found for {hostname} ({host})")
            return False
        
        if not command_output:
            logger.error(f"No command output to save for {hostname} ({host})")
            device_result['data_collection'] = False
            device_result['error'] = "No command output to save"
            self.phase_times['data_collection'][host]['end'] = datetime.datetime.now()
            return False
        
        try:
            # Create device data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.data_dir)
            os.makedirs(data_dir, exist_ok=True)
            
            # Create a file for this device's data
            filename = f"{hostname}_{host}_lines.txt"
            filepath = os.path.join(data_dir, filename)
            
            # Write command output to file
            with open(filepath, 'w') as f:
                f.write(f"Device: {hostname} ({host})\n")
                f.write(f"Command: show line\n")
                f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write(command_output)
            
            logger.info(f"A5: Data saved to {filepath}")
            print(f"{Fore.GREEN}✓ A5: Data saved to {filepath}{Style.RESET_ALL}")
            device_result['data_collection'] = True
            self.phase_times['data_collection'][host]['end'] = datetime.datetime.now()
            return True
        except Exception as e:
            logger.error(f"A5: Error saving data for {hostname} ({host}): {e}")
            print(f"{Fore.RED}✗ A5: Error saving data for {hostname} ({host}): {e}{Style.RESET_ALL}")
            device_result['data_collection'] = False
            device_result['error'] = f"Data saving error: {str(e)}"
            self.phase_times['data_collection'][host]['end'] = datetime.datetime.now()
            return False
    
    # A6-A7: Process collected data and identify telnet-enabled lines
    def analyze_device_data(self, device):
        """Phase A6-A7: Process collected data and identify telnet-enabled lines"""
        host = device['host']
        hostname = device['hostname']
        
        # Record start time for this phase
        start_time = datetime.datetime.now()
        self.phase_times['analysis'][host] = {'start': start_time}
        
        logger.info(f"A6-A7: Analyzing data for {hostname} ({host})...")
        print(f"\n{Fore.CYAN}A6-A7: Analyzing data for {hostname} ({host})...{Style.RESET_ALL}")
        
        # Get device result dictionary
        device_result = next((r for r in self.results if r['host'] == host), None)
        if not device_result:
            logger.error(f"Device result not found for {hostname} ({host})")
            return False
        
        try:
            # Check if data collection was successful
            if not device_result['data_collection']:
                logger.error(f"Data collection failed for {hostname} ({host})")
                device_result['analysis'] = False
                device_result['error'] = "Data collection failed"
                self.phase_times['analysis'][host]['end'] = datetime.datetime.now()
                return False
            
            # Read the saved data file
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.data_dir)
            filename = f"{hostname}_{host}_lines.txt"
            filepath = os.path.join(data_dir, filename)
            
            if not os.path.exists(filepath):
                logger.error(f"Data file not found for {hostname} ({host})")
                device_result['analysis'] = False
                device_result['error'] = "Data file not found"
                self.phase_times['analysis'][host]['end'] = datetime.datetime.now()
                return False
            
            with open(filepath, 'r') as f:
                lines_data = f.read()
            
            # A7: Identify telnet-enabled lines
            aux_lines = []
            vty_lines = []
            con_lines = []
            telnet_enabled = False
            
            # Parse the output for lines with telnet enabled
            for line in lines_data.split('\n'):
                # Look for AUX lines
                if 'AUX' in line and 'telnet' in line.lower():
                    aux_lines.append(line.strip())
                    telnet_enabled = True
                # Look for VTY lines
                elif 'VTY' in line and 'telnet' in line.lower():
                    vty_lines.append(line.strip())
                    telnet_enabled = True
                # Look for CON lines
                elif 'CON' in line and 'telnet' in line.lower():
                    con_lines.append(line.strip())
                    telnet_enabled = True
            
            # Update device result
            device_result['telnet_enabled'] = telnet_enabled
            device_result['aux_lines'] = aux_lines
            device_result['vty_lines'] = vty_lines
            device_result['con_lines'] = con_lines
            device_result['analysis'] = True
            
            # Log findings
            if telnet_enabled:
                logger.warning(f"A7: Telnet is enabled on {hostname} ({host})")
                print(f"{Fore.YELLOW}⚠️ A7: Telnet is enabled on {hostname} ({host}){Style.RESET_ALL}")
                if aux_lines:
                    logger.warning(f"A7: Telnet enabled on AUX lines: {len(aux_lines)}")
                    print(f"{Fore.YELLOW}⚠️ A7: Telnet enabled on AUX lines: {len(aux_lines)}{Style.RESET_ALL}")
                if vty_lines:
                    logger.warning(f"A7: Telnet enabled on VTY lines: {len(vty_lines)}")
                    print(f"{Fore.YELLOW}⚠️ A7: Telnet enabled on VTY lines: {len(vty_lines)}{Style.RESET_ALL}")
                if con_lines:
                    logger.warning(f"A7: Telnet enabled on CON lines: {len(con_lines)}")
                    print(f"{Fore.YELLOW}⚠️ A7: Telnet enabled on CON lines: {len(con_lines)}{Style.RESET_ALL}")
            else:
                logger.info(f"A7: No telnet-enabled lines found on {hostname} ({host})")
                print(f"{Fore.GREEN}✓ A7: No telnet-enabled lines found on {hostname} ({host}){Style.RESET_ALL}")
            
            self.phase_times['analysis'][host]['end'] = datetime.datetime.now()
            return True
        except Exception as e:
            logger.error(f"A6-A7: Error analyzing data for {hostname} ({host}): {e}")
            print(f"{Fore.RED}✗ A6-A7: Error analyzing data for {hostname} ({host}): {e}{Style.RESET_ALL}")
            device_result['analysis'] = False
            device_result['error'] = f"Analysis error: {str(e)}"
            self.phase_times['analysis'][host]['end'] = datetime.datetime.now()
            return False
    
    # A8: Generate dashboard and reports
    def generate_report(self):
        """Phase A8: Generate reports and dashboard for audit results"""
        logger.info("A8: Generating audit reports and dashboard...")
        print(f"\n{Fore.CYAN}A8: Generating audit reports and dashboard...{Style.RESET_ALL}")
        
        try:
            # Convert device results to the format needed for the reporter
            for device_result in self.results:
                device = {
                    'hostname': device_result['hostname'],
                    'host': device_result['host'],
                    'model': device_result.get('model', 'Unknown')
                }
                
                # Map our phase results to the 5-phase structure
                phase_results = {
                    'connectivity': {
                        'status': 'Success' if device_result['connectivity'] else 'Failed',
                        'details': "ICMP ping successful" if device_result['connectivity'] else "ICMP ping failed"
                    },
                    'authentication': {
                        'status': 'Success' if device_result['authentication'] else 'Failed',
                        'details': "SSH authentication successful" if device_result['authentication'] else "SSH authentication failed"
                    },
                    'authorization': {
                        'status': 'Success' if device_result['authorization'] else 'Failed',
                        'details': "Authorization commands executed successfully" if device_result['authorization'] else "Authorization failed"
                    },
                    'config_audit': {
                        'status': 'Success' if device_result['data_collection'] else 'Failed',
                        'details': "Configuration collected successfully" if device_result['data_collection'] else "Configuration collection failed"
                    },
                    'risk_assessment': {
                        'status': 'Success' if device_result['analysis'] else 'Failed',
                        'details': f"Telnet {'enabled' if device_result['telnet_enabled'] else 'disabled'}",
                        'recommendations': "Disable Telnet and use SSH with strong authentication" if device_result['telnet_enabled'] else ""
                    },
                    'reporting': {
                        'status': 'Success',
                        'details': "Report generated successfully"
                    }
                }
                
                # Add to the reporter
                self.reporter.add_result(device, phase_results)
            
            # Generate all report formats
            report_files = self.reporter.generate_all_reports()
            
            # Print summary to console
            self.reporter.print_summary()
            
            logger.info(f"A8: Reports saved to {self.reporter.report_dir} directory")
            print(f"{Fore.GREEN}✓ A8: Reports saved to {self.reporter.report_dir} directory{Style.RESET_ALL}")
            
            # Return paths to the primary reports
            return report_files['csv'], report_files['txt']
            
        except Exception as e:
            logger.error(f"A8: Error generating reports: {e}")
            print(f"{Fore.RED}✗ A8: Error generating reports: {e}{Style.RESET_ALL}")
            return None, None
    
    def run_audit(self, use_advanced_mode=True):
        """Run the multi-phase audit process for all devices"""
        # Initialize the audit reporter for consistent reporting across modes
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reporter = AuditReporter(timestamp=timestamp)
        
        # Import the phased_audit_tool functions if using advanced mode
        using_phased_tool = False
        if use_advanced_mode:
            try:
                from phased_audit_tool import (
                    perform_phased_audit, CredentialManager, prompt_for_master_password,
                    initialize_database
                )
                logger.info("Successfully imported phased_audit_tool functions")
                using_phased_tool = True
            except ImportError as e:
                logger.error(f"Could not import from phased_audit_tool: {e}")
                print(f"{Fore.YELLOW}Warning: Could not import from phased_audit_tool. Using built-in audit functions.{Style.RESET_ALL}")
                using_phased_tool = False
        
        # Start timer for overall audit
        self.start_time = datetime.datetime.now()
        logger.info(f"Starting device audit at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}CISCO ROUTER AUDIT - PHASED APPROACH{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Starting audit at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Connect to jump host
        if not self.test_mode and not self.connect_to_jump_host():
            logger.error("Failed to connect to jump host, aborting audit")
            return False
            
        # Initialize the database if using phased_audit_tool
        if using_phased_tool:
            initialize_database()
            
            # Prepare the router configurations for phased_audit_tool
            routers_to_audit = []
            for device in self.devices:
                router_config = {
                    'hostname': device['hostname'],
                    'ip': device['host'],
                    'username': device['username'],
                    'password': device['password'],
                    'enable_secret': device['secret'],
                    'device_type': device['device_type'],
                    'model': device['model']
                }
                routers_to_audit.append(router_config)
            
            # Create credential manager with our master password
            cred_manager = None
            if hasattr(self, 'master_password') and self.master_password:
                try:
                    cred_manager = CredentialManager(self.master_password)
                    logger.info("Created credential manager for secure password handling")
                except Exception as e:
                    logger.error(f"Failed to create credential manager: {e}")
            
            # Run the 5-phase audit using phased_audit_tool
            print(f"{Fore.CYAN}Running 5-phase audit using phased_audit_tool...{Style.RESET_ALL}")
            # perform_phased_audit doesn't take a cred_manager parameter - it will prompt for password if needed
            results = perform_phased_audit(routers_to_audit)
            
            # Display summary
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Audit completed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}See the reports directory for detailed audit results{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            return True
        
        # Process each device
        for device in self.devices:
            hostname = device['hostname']
            host = device['host']
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Auditing device: {hostname} ({host}){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            # A1: Ping the device
            ping_success = self.ping_device(device)
            logger.info(f"A1 Ping result for {hostname} ({host}): {'Success' if ping_success else 'Failed'}")
            
            # A2: SSH to the device (proceed even if ping fails)
            ssh_success, device_conn = self.ssh_to_device(device)
            logger.info(f"A2 SSH result for {hostname} ({host}): {'Success' if ssh_success else 'Failed'}")
            
            # A3-A4: Check authorization (only if SSH succeeded)
            command_output = None
            if ssh_success and device_conn:
                auth_success, command_output = self.check_authorization(device, device_conn)
                logger.info(f"A3-A4 Authorization result for {hostname} ({host}): {'Success' if auth_success else 'Failed'}")
            else:
                # Skip authorization if SSH failed
                logger.warning(f"Skipping A3-A4 Authorization for {hostname} ({host}) due to SSH failure")
                device_result = next((r for r in self.results if r['host'] == host), None)
                if device_result:
                    device_result['authorization'] = False
                    device_result['error'] = "SSH connection failed"
            
            # A5: Save collected data (only if authorization succeeded)
            if command_output:
                data_success = self.save_device_data(device, command_output)
                logger.info(f"A5 Data collection result for {hostname} ({host}): {'Success' if data_success else 'Failed'}")
            else:
                # Skip data collection if authorization failed
                logger.warning(f"Skipping A5 Data collection for {hostname} ({host}) due to authorization failure")
                device_result = next((r for r in self.results if r['host'] == host), None)
                if device_result:
                    device_result['data_collection'] = False
                    if not device_result['error']:
                        device_result['error'] = "No command output to save"
            
            # A6-A7: Analyze device data (only if data collection succeeded)
            device_result = next((r for r in self.results if r['host'] == host), None)
            if device_result and device_result.get('data_collection', False):
                analysis_success = self.analyze_device_data(device)
                logger.info(f"A6-A7 Analysis result for {hostname} ({host}): {'Success' if analysis_success else 'Failed'}")
            else:
                # Skip analysis if data collection failed
                logger.warning(f"Skipping A6-A7 Analysis for {hostname} ({host}) due to data collection failure")
                if device_result:
                    device_result['analysis'] = False
                    if not device_result['error']:
                        device_result['error'] = "Data collection failed"
        
        # Disconnect from jump host
        if self.jump_conn:
            self.jump_conn.disconnect()
            logger.info("Disconnected from jump host")
        
        # A8: Generate reports with proper error handling
        try:
            logger.info("Starting generation of unified reports")
            report_file, dashboard_file = self.generate_report()
            logger.info(f"Successfully generated reports: {report_file}, {dashboard_file}")
        except Exception as e:
            logger.error(f"Error generating reports: {str(e)}")
            print(f"{Fore.RED}Error generating reports: {str(e)}{Style.RESET_ALL}")
        
        # End timer for overall audit
        self.end_time = datetime.datetime.now()
        audit_duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Audit completed at {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total audit duration: {audit_duration:.2f} seconds")
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Audit completed at {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total audit duration: {audit_duration:.2f} seconds{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        return True


def main():
    """Main entry point for the script"""
    import argparse
    import sys
    
    # Check if phased_audit_tool.py exists
    phased_tool_exists = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phased_audit_tool.py'))
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Cisco Router Audit Tool with 5-Phase Approach")
    parser.add_argument("-t", "--test", action="store_true", help="Run in test mode with simulated connections")
    parser.add_argument("-c", "--csv", type=str, default="routers01.csv", help="CSV file with router details (default: routers01.csv)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip interactive prompts and use defaults")
    parser.add_argument("-m", "--mode", type=str, choices=['simple', 'advanced'], default='advanced', 
                        help="Audit mode: 'simple' uses basic checks, 'advanced' uses the 5-phase framework")
    args = parser.parse_args()
    
    # Print banner
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}CISCO ROUTER AUDIT TOOL - 5-PHASE APPROACH{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Phases: Connectivity, Authentication, Config Audit, Risk Assessment, Reporting{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    # Set up logging
    log_file = setup_logging()
    
    # Validate advanced mode is available
    if args.mode == 'advanced' and not phased_tool_exists:
        print(f"{Fore.YELLOW}Warning: phased_audit_tool.py not found. Falling back to simple mode.{Style.RESET_ALL}\n")
        logger.warning("phased_audit_tool.py not found. Falling back to simple mode.")
        args.mode = 'simple'
    
    try:
        # Check if test mode is enabled
        if args.test:
            print(f"{Fore.YELLOW}Running in TEST MODE with simulated connections{Style.RESET_ALL}")
            print(f"This mode doesn't require actual network connectivity.\n")
        else:
            print(f"{Fore.CYAN}Running in INTERACTIVE MODE with actual network connections{Style.RESET_ALL}")
            print(f"You will be prompted for jump host and router credentials.\n")
            
            if args.yes:
                print(f"{Fore.YELLOW}Interactive prompts disabled. Using default or saved credentials.{Style.RESET_ALL}\n")
        
        # Display audit mode
        if args.mode == 'advanced':
            print(f"{Fore.CYAN}Using ADVANCED 5-phase audit framework from phased_audit_tool.py{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.CYAN}Using SIMPLE audit mode with basic checks{Style.RESET_ALL}\n")
        
        # Create auditor instance
        auditor = DeviceAuditor(test_mode=args.test)
        
        # Load configuration
        auditor.load_environment()
        
        # Load devices from CSV
        if not auditor.load_devices_from_csv(args.csv):
            logger.error(f"Failed to load devices from CSV file {args.csv}, aborting audit")
            print(f"\n{Fore.RED}AUDIT ABORTED: Failed to load devices from CSV file {args.csv}{Style.RESET_ALL}")
            print(f"Please make sure the CSV file exists and contains the required columns.")
            return
        
        # Confirm before proceeding with actual connections
        if not args.test and not args.yes:
            print(f"\n{Fore.YELLOW}Ready to start the audit with the following configuration:{Style.RESET_ALL}")
            print(f"Jump Host: {auditor.jump_host['host']} (user: {auditor.jump_host['username']})")
            print(f"Number of Devices: {len(auditor.devices)}")
            print(f"CSV File: {args.csv}")
            print(f"Audit Mode: {args.mode.upper()}")
            
            proceed = input(f"\nProceed with the audit? (y/n): ").strip().lower()
            if proceed != 'y':
                print(f"\n{Fore.YELLOW}Audit cancelled by user{Style.RESET_ALL}")
                return
        
        # Run the audit
        auditor.run_audit(use_advanced_mode=(args.mode == 'advanced'))
        
    except KeyboardInterrupt:
        logger.warning("Audit interrupted by user")
        print(f"\n{Fore.YELLOW}Audit interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        if isinstance(e, Exception) and e is not None:
            logger.error(f"Unexpected error of type {type(e).__name__}: {str(e)}")
            print(f"\n{Fore.RED}Audit failed: {type(e).__name__} - {str(e)}{Style.RESET_ALL}")
        else:
            logger.error("Unexpected error: Exception object was None.")
            print(f"\n{Fore.RED}Audit failed: An unspecified error occurred{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
