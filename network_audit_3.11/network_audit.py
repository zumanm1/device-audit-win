#!/usr/bin/env python3
"""
Network Audit Tool - Main Module (v3.11)

This is the unified entry point for the Network Audit Tool that integrates all
three specialized audit modules:
1. Connectivity Audit (basic network connectivity testing)
2. Security Audit (5-phase security configuration analysis)
3. Telnet Audit (specialized telnet vulnerability detection)

Run this script to perform a comprehensive audit or specify individual
audit types with command-line options.
"""

import os
import sys
import time
import datetime
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import core functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from audit_core import (
        VERSION, ensure_directories, setup_logging, CredentialManager, 
        prompt_for_master_password, AuditResult, AuditReport,
        Fore, Style, colorama_available
    )
except ImportError as e:
    print(f"Error importing audit_core module: {e}")
    print("Make sure audit_core.py is in the same directory.")
    sys.exit(1)

# Set up module-specific constants
MODULE_NAME = "Network Audit Tool"
DEFAULT_CSV = "devices.csv"

# Configure logger
logger, log_file = setup_logging(f"network_audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
if not logger:
    print("Failed to set up logging. Exiting.")
    sys.exit(1)

class NetworkAuditTool:
    """Main class that orchestrates all audit modules"""
    
    def __init__(self, options):
        """Initialize the network audit tool with command-line options"""
        self.options = options
        self.test_mode = options.test
        self.csv_file = options.csv
        self.jump_host = options.jump_host
        self.master_password = None
        self.cred_manager = None
        self.timestamp = datetime.datetime.now()
        self.devices = []
        self.results = {}  # Results by audit type
        
        # Print banner
        self.print_banner()
        
        # Determine which audit types to run
        self.audit_types = []
        if options.all or (not options.connectivity and not options.security and not options.telnet):
            self.audit_types = ['connectivity', 'security', 'telnet']
        else:
            if options.connectivity:
                self.audit_types.append('connectivity')
            if options.security:
                self.audit_types.append('security')
            if options.telnet:
                self.audit_types.append('telnet')
        
        logger.info(f"Audit types to run: {', '.join(self.audit_types)}")
        
    def print_banner(self):
        """Print the main banner"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{MODULE_NAME} v{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Comprehensive Network Audit Framework{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        if self.test_mode:
            print(f"{Fore.YELLOW}Running in TEST MODE with simulated responses{Style.RESET_ALL}")
        print(f"Started at: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log file: {log_file}")
        
        # Print selected audit types
        print(f"\nAudit modules that will run:")
        if 'connectivity' in self.audit_types:
            print(f"  {Fore.GREEN}✓ Connectivity Audit{Style.RESET_ALL} - Basic network connectivity testing")
        if 'security' in self.audit_types:
            print(f"  {Fore.GREEN}✓ Security Audit{Style.RESET_ALL} - 5-phase security configuration analysis")
        if 'telnet' in self.audit_types:
            print(f"  {Fore.GREEN}✓ Telnet Audit{Style.RESET_ALL} - Specialized telnet vulnerability detection")
        
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def setup_credentials(self):
        """Set up secure credentials manager if needed"""
        if 'security' in self.audit_types or self.jump_host:
            # We need credential management for secure modules
            try:
                # Prompt for master password
                self.master_password = prompt_for_master_password()
                
                # Initialize credential manager
                self.cred_manager = CredentialManager(self.master_password)
                logger.info("Credential manager initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize credential manager: {e}")
                print(f"{Fore.RED}Error: Failed to initialize credential manager: {e}{Style.RESET_ALL}")
                return False
        
        return True  # No credential manager needed
    
    def load_devices_from_csv(self):
        """Load devices from the specified CSV file"""
        try:
            if not os.path.exists(self.csv_file):
                logger.error(f"CSV file not found: {self.csv_file}")
                print(f"{Fore.RED}Error: CSV file not found: {self.csv_file}{Style.RESET_ALL}")
                return False
            
            with open(self.csv_file, 'r') as f:
                csv_reader = csv.DictReader(f)
                required_fields = ['hostname', 'ip']
                
                for row in csv_reader:
                    # Check for required fields
                    if not all(field in row for field in required_fields):
                        logger.warning(f"Skipping row in CSV: missing required fields")
                        continue
                    
                    # Add device to the list
                    self.devices.append({
                        'hostname': row['hostname'],
                        'ip': row['ip'],
                        'device_type': row.get('device_type', 'cisco_ios'),
                        'username': row.get('username', ''),
                        'password': row.get('password', ''),
                        'secret': row.get('secret', ''),
                        'enable_password': row.get('enable_password', ''),
                        'model': row.get('model', 'Unknown')
                    })
            
            if not self.devices:
                logger.warning(f"No valid devices found in {self.csv_file}")
                print(f"{Fore.YELLOW}Warning: No valid devices found in {self.csv_file}{Style.RESET_ALL}")
                if self.test_mode:
                    self.create_test_devices()
                    return True
                return False
            
            logger.info(f"Loaded {len(self.devices)} devices from {self.csv_file}")
            print(f"{Fore.GREEN}Successfully loaded {len(self.devices)} devices from {self.csv_file}{Style.RESET_ALL}")
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
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123', 'model': 'Cisco 2901'},
            {'hostname': 'router2.example.com', 'ip': '192.168.1.2', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123', 'model': 'Cisco 2911'},
            {'hostname': 'switch1.example.com', 'ip': '192.168.1.10', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123', 'model': 'Cisco 3560'},
            {'hostname': 'switch2.example.com', 'ip': '192.168.1.11', 'device_type': 'cisco_ios',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123', 'model': 'Cisco 2960'},
            {'hostname': 'firewall.example.com', 'ip': '192.168.1.254', 'device_type': 'cisco_asa',
             'username': 'admin', 'password': 'cisco123', 'secret': 'cisco123', 'model': 'Cisco ASA 5505'}
        ]
        
        # Create a sample CSV file for reference
        sample_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'data', 'sample_devices.csv')
        try:
            with open(sample_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'hostname', 'ip', 'device_type', 'username', 'password', 
                    'secret', 'enable_password', 'model'
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
            print(f"  - {device['hostname']} ({device['ip']}) - {device['model']}")
        
        return True
    
    def run_connectivity_audit(self):
        """Run the connectivity audit module"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}RUNNING CONNECTIVITY AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        try:
            # Import connectivity audit module
            from connectivity_audit import ConnectivityAuditor
            
            # Create the auditor
            auditor = ConnectivityAuditor(test_mode=self.test_mode)
            
            # Add devices
            auditor.devices = self.devices.copy()
            
            # Run the audit
            if auditor.run_audit():
                # Generate reports
                auditor.generate_reports()
                
                # Store results
                self.results['connectivity'] = auditor.results
                return True
            else:
                logger.error("Failed to run connectivity audit")
                return False
                
        except ImportError as e:
            logger.error(f"Failed to import connectivity_audit module: {e}")
            print(f"{Fore.RED}Error: Failed to import connectivity_audit module: {e}{Style.RESET_ALL}")
            print(f"Make sure connectivity_audit.py is in the same directory.")
            return False
        except Exception as e:
            logger.error(f"Error running connectivity audit: {e}")
            print(f"{Fore.RED}Error running connectivity audit: {e}{Style.RESET_ALL}")
            return False
    
    def run_security_audit(self):
        """Run the security audit module"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}RUNNING SECURITY AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        try:
            # Import security audit modules
            from security_audit import SecurityAuditor
            from security_audit_phases import execute_all_phases
            
            # Create the auditor
            auditor = SecurityAuditor(test_mode=self.test_mode, jump_host=self.jump_host)
            
            # Add devices
            auditor.devices = self.devices.copy()
            
            # Set credential manager if available
            if self.cred_manager:
                auditor.cred_manager = self.cred_manager
            
            # Manually execute phases for each device
            results = []
            for device in auditor.devices:
                print(f"\n{Fore.CYAN}Auditing device: {device['hostname']} ({device['ip']}){Style.RESET_ALL}")
                result = execute_all_phases(device, auditor.test_mode)
                results.append(result)
            
            # Store results in auditor and our results
            auditor.results = results
            self.results['security'] = results
            
            # Generate reports
            report = AuditReport(results)
            report.generate_all_reports()
            report.print_summary()
            
            return True
                
        except ImportError as e:
            logger.error(f"Failed to import security audit modules: {e}")
            print(f"{Fore.RED}Error: Failed to import security audit modules: {e}{Style.RESET_ALL}")
            print(f"Make sure security_audit.py and security_audit_phases.py are in the same directory.")
            return False
        except Exception as e:
            logger.error(f"Error running security audit: {e}")
            print(f"{Fore.RED}Error running security audit: {e}{Style.RESET_ALL}")
            return False
    
    def run_telnet_audit(self):
        """Run the telnet audit module"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}RUNNING TELNET AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        try:
            # Import telnet audit module
            from telnet_audit import TelnetAuditor
            
            # Create the auditor
            auditor = TelnetAuditor(test_mode=self.test_mode, jump_host=self.jump_host)
            
            # Add devices
            auditor.devices = self.devices.copy()
            
            # Run the audit
            if auditor.run_audit():
                # Generate reports
                auditor.generate_reports()
                
                # Store results
                self.results['telnet'] = auditor.results
                return True
            else:
                logger.error("Failed to run telnet audit")
                return False
                
        except ImportError as e:
            logger.error(f"Failed to import telnet_audit module: {e}")
            print(f"{Fore.RED}Error: Failed to import telnet_audit module: {e}{Style.RESET_ALL}")
            print(f"Make sure telnet_audit.py is in the same directory.")
            return False
        except Exception as e:
            logger.error(f"Error running telnet audit: {e}")
            print(f"{Fore.RED}Error running telnet audit: {e}{Style.RESET_ALL}")
            return False
    
    def generate_unified_report(self):
        """Generate a unified report combining all audit results"""
        if not any(self.results.values()):
            logger.warning("No audit results to report")
            print(f"{Fore.YELLOW}Warning: No audit results to report{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}GENERATING UNIFIED AUDIT REPORT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        # Combine all audit results
        all_results = []
        for audit_type, results in self.results.items():
            if results:
                all_results.extend(results)
        
        # Create unified report
        unified_report = AuditReport(all_results, timestamp=self.timestamp.strftime("%Y%m%d_%H%M%S"))
        
        # Generate all report formats
        report_files = unified_report.generate_all_reports()
        
        # Print summary
        print(f"\n{Fore.CYAN}UNIFIED AUDIT SUMMARY{Style.RESET_ALL}")
        unified_report.print_summary()
        
        # Calculate overall security status
        total_devices = len(self.devices)
        recommendations_count = sum(len(result.recommendations) for result in all_results)
        
        print(f"\n{Fore.CYAN}OVERALL SECURITY STATUS{Style.RESET_ALL}")
        print(f"Total devices audited: {total_devices}")
        print(f"Total recommendations: {recommendations_count}")
        
        # Check for critical findings
        has_critical = any(
            rec['severity'] == 'critical' 
            for result in all_results 
            for rec in result.recommendations
        )
        
        if has_critical:
            print(f"\n{Fore.RED}⚠️ CRITICAL SECURITY ISSUES DETECTED!{Style.RESET_ALL}")
            print(f"{Fore.RED}Please review the detailed reports and address critical findings immediately.{Style.RESET_ALL}")
        elif recommendations_count > 0:
            print(f"\n{Fore.YELLOW}⚠️ Security improvements recommended{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please review the detailed reports for specific recommendations.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✓ No significant security issues detected{Style.RESET_ALL}")
        
        return True
    
    def run_all_audits(self):
        """Run all selected audit types"""
        start_time = time.time()
        
        # Set up credential manager if needed
        if not self.setup_credentials():
            return False
        
        # Load devices
        if not self.load_devices_from_csv():
            if not self.test_mode:
                print(f"{Fore.RED}Failed to load devices. Exiting.{Style.RESET_ALL}")
                return False
        
        # Run selected audit modules
        for audit_type in self.audit_types:
            if audit_type == 'connectivity':
                self.run_connectivity_audit()
            elif audit_type == 'security':
                self.run_security_audit()
            elif audit_type == 'telnet':
                self.run_telnet_audit()
        
        # Generate unified report
        self.generate_unified_report()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed all audits in {elapsed_time:.2f} seconds")
        print(f"\n{Fore.CYAN}Completed all audits in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
        
        return True


def main():
    """Main entry point for the Network Audit Tool"""
    parser = argparse.ArgumentParser(description=f"{MODULE_NAME} v{VERSION}")
    
    # Audit type selection
    audit_group = parser.add_argument_group('Audit Types')
    audit_group.add_argument("-a", "--all", action="store_true", help="Run all audit types (default)")
    audit_group.add_argument("-c", "--connectivity", action="store_true", help="Run connectivity audit")
    audit_group.add_argument("-s", "--security", action="store_true", help="Run security audit")
    audit_group.add_argument("-n", "--telnet", action="store_true", help="Run telnet audit")
    
    # General options
    parser.add_argument("-t", "--test", action="store_true", help="Run in test mode with simulated responses")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV, help=f"CSV file with device details (default: {DEFAULT_CSV})")
    parser.add_argument("-j", "--jump-host", type=str, help="Jump host IP for accessing devices")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Create and run the audit tool
    audit_tool = NetworkAuditTool(args)
    
    if audit_tool.run_all_audits():
        print(f"{Fore.GREEN}Audit completed successfully.{Style.RESET_ALL}")
        return 0
    else:
        print(f"{Fore.RED}Audit failed. Check the logs for details.{Style.RESET_ALL}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
