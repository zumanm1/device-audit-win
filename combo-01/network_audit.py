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

Cross-platform compatible with Windows and Ubuntu.
"""

import os
import sys
import time
import datetime
import argparse
import csv
import platform
from pathlib import Path
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
DEFAULT_CSV = "routers01.csv"

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
        self.auto_fallback = options.auto_fallback
        self.csv_file = options.csv
        self.jump_host = options.jump_host
        self.no_report = options.no_report if hasattr(options, 'no_report') else False
        self.master_password = None
        self.cred_manager = None
        
        # Set timestamp based on command line or generate a new one
        if hasattr(options, 'timestamp') and options.timestamp:
            try:
                self.timestamp = datetime.datetime.strptime(options.timestamp, "%Y%m%d_%H%M%S")
                logger.info(f"Using provided timestamp: {options.timestamp}")
            except ValueError:
                logger.warning(f"Invalid timestamp format: {options.timestamp}, using current time instead")
                self.timestamp = datetime.datetime.now()
        else:
            self.timestamp = datetime.datetime.now()
        self.devices = []
        self.results = {}  # Results by audit type
        self.connection_failures = 0
        self.fallback_activated = False
        
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
                
        # Print banner after audit_types is initialized
        self.print_banner()
        
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
        """Load devices from the specified CSV file using pathlib for cross-platform compatibility"""
        try:
            # Convert to Path object for cross-platform compatibility
            csv_path = Path(self.csv_file)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_path}")
                print(f"{Fore.RED}Error: CSV file not found: {csv_path}{Style.RESET_ALL}")
                return False
            
            with open(csv_path, 'r', encoding='utf-8') as f:
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
        
        # Create a sample CSV file for reference using pathlib for cross-platform compatibility
        script_dir = Path(__file__).parent.absolute()
        data_dir = script_dir / 'data'
        data_dir.mkdir(exist_ok=True, parents=True)  # Ensure data directory exists
        sample_csv = data_dir / 'sample_devices.csv'
        
        try:
            with open(sample_csv, 'w', newline='', encoding='utf-8') as f:
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
        
        original_test_mode = self.test_mode
        fallback_used = False
        
        try:
            # Import connectivity audit module
            from connectivity_audit import ConnectivityAuditor
            
            # First attempt with current test mode setting
            auditor = ConnectivityAuditor(test_mode=self.test_mode)
            auditor.devices = self.devices.copy()
            auditor.timestamp = self.timestamp  # Use consistent timestamp
            
            # Run the audit
            if not auditor.run_audit() and not self.test_mode and self.auto_fallback:
                # If real mode failed and auto-fallback is enabled, try test mode
                logger.warning("Connectivity audit failed with real connections, falling back to test mode")
                print(f"\n{Fore.YELLOW}Warning: Connection failures detected. Falling back to test mode...{Style.RESET_ALL}")
                
                # Switch to test mode
                self.test_mode = True
                self.fallback_activated = True
                fallback_used = True
                
                # Create a new auditor in test mode
                auditor = ConnectivityAuditor(test_mode=True)
                auditor.devices = self.devices.copy()
                auditor.timestamp = self.timestamp  # Use consistent timestamp
                
                # Run in test mode
                if not auditor.run_audit():
                    logger.error("Connectivity audit failed even in test mode")
                    print(f"{Fore.RED}Error: Connectivity audit failed even in test mode{Style.RESET_ALL}")
                    self.test_mode = original_test_mode  # Restore original mode
                    return False
            elif not auditor.run_audit():
                # Failed without fallback
                logger.error("Failed to run connectivity audit")
                return False
            
            # If we got here, the audit was successful (either in real mode or test fallback)
            self.results['connectivity'] = auditor.results
            
            # Generate reports unless no_report flag is set
            if not self.no_report:
                auditor.generate_reports()
            else:
                print(f"{Fore.YELLOW}Skipping individual connectivity report generation (--no-report specified){Style.RESET_ALL}")
            
            # Add a note about fallback in the results if it was used
            if fallback_used:
                for result in self.results['connectivity']:
                    result.add_note("This audit was conducted in TEST MODE due to connection failures with real devices.")
            
            return True
                
        except ImportError as e:
            logger.error(f"Failed to import connectivity_audit module: {e}")
            print(f"{Fore.RED}Error: Failed to import connectivity_audit module: {e}{Style.RESET_ALL}")
            print(f"Make sure connectivity_audit.py is in the same directory.")
            return False
        except Exception as e:
            logger.error(f"Error running connectivity audit: {e}")
            print(f"{Fore.RED}Error running connectivity audit: {e}{Style.RESET_ALL}")
            return False
        finally:
            # Always restore original test mode setting
            self.test_mode = original_test_mode
    
    def run_security_audit(self):
        """Run the security audit module"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}RUNNING SECURITY AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        original_test_mode = self.test_mode
        fallback_used = False
        
        try:
            # Import security audit modules
            from security_audit import SecurityAuditor
            from security_audit_phases import execute_all_phases
            
            # First attempt with current test mode setting
            auditor = SecurityAuditor(test_mode=self.test_mode, jump_host=self.jump_host)
            auditor.devices = self.devices.copy()
            
            # Set credential manager if available
            if self.cred_manager:
                auditor.cred_manager = self.cred_manager
            
            # Manually execute phases for each device
            results = []
            connection_failures = 0
            
            # First attempt with real connections if not in test mode
            for device in auditor.devices:
                print(f"\n{Fore.CYAN}Auditing device: {device['hostname']} ({device['ip']}){Style.RESET_ALL}")
                result = execute_all_phases(device, auditor.test_mode)
                
                # Check if connectivity phase failed
                if result.phases.get('connectivity', {}).get('status') == 'Failed':
                    connection_failures += 1
                
                results.append(result)
            
            # If too many connection failures and auto-fallback is enabled, retry in test mode
            if not self.test_mode and self.auto_fallback and connection_failures >= len(auditor.devices) / 2:
                logger.warning(f"Security audit had {connection_failures}/{len(auditor.devices)} connection failures, falling back to test mode")
                print(f"\n{Fore.YELLOW}Warning: {connection_failures}/{len(auditor.devices)} connection failures detected. Falling back to test mode for security audit...{Style.RESET_ALL}")
                
                # Switch to test mode
                self.test_mode = True
                self.fallback_activated = True
                fallback_used = True
                
                # Re-run the audit in test mode
                results = []
                for device in auditor.devices:
                    print(f"\n{Fore.CYAN}Auditing device: {device['hostname']} ({device['ip']}) [TEST MODE]{Style.RESET_ALL}")
                    result = execute_all_phases(device, True)  # Force test mode
                    result.add_note("This audit was conducted in TEST MODE due to connection failures with real devices.")
                    results.append(result)
            
            # Store results in auditor and our results
            auditor.results = results
            self.results['security'] = results
            
            # Generate reports unless no_report flag is set
            report = AuditReport(results, timestamp=self.timestamp.strftime("%Y%m%d_%H%M%S"))
            
            if not self.no_report:
                report.generate_all_reports()
                report.print_summary()
            else:
                print(f"{Fore.YELLOW}Skipping individual security report generation (--no-report specified){Style.RESET_ALL}")
            
            # Display message if fallback was used
            if fallback_used:
                print(f"\n{Fore.YELLOW}Note: Security audit was conducted in TEST MODE due to connection failures with real devices.{Style.RESET_ALL}")
            
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
        finally:
            # Always restore original test mode setting
            self.test_mode = original_test_mode
    
    def run_telnet_audit(self):
        """Run the telnet audit module"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}RUNNING TELNET AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        original_test_mode = self.test_mode
        fallback_used = False
        
        try:
            # Import telnet audit module
            from telnet_audit import TelnetAuditor
            
            # First attempt with current test mode setting
            auditor = TelnetAuditor(test_mode=self.test_mode, jump_host=self.jump_host)
            auditor.devices = self.devices.copy()
            auditor.timestamp = self.timestamp  # Use consistent timestamp
            
            # Run the audit
            success = auditor.run_audit()
            
            # Check if we should fall back to test mode
            if not success and not self.test_mode and self.auto_fallback:
                logger.warning("Telnet audit failed with real connections, falling back to test mode")
                print(f"\n{Fore.YELLOW}Warning: Connection failures detected. Falling back to test mode for telnet audit...{Style.RESET_ALL}")
                
                # Switch to test mode
                self.test_mode = True
                self.fallback_activated = True
                fallback_used = True
                
                # Create a new auditor in test mode
                auditor = TelnetAuditor(test_mode=True, jump_host=self.jump_host)
                auditor.devices = self.devices.copy()
                auditor.timestamp = self.timestamp  # Use consistent timestamp
                
                # Run in test mode
                success = auditor.run_audit()
                
                if not success:
                    logger.error("Telnet audit failed even in test mode")
                    print(f"{Fore.RED}Error: Telnet audit failed even in test mode{Style.RESET_ALL}")
                    self.test_mode = original_test_mode  # Restore original mode
                    return False
            elif not success:
                # Failed without fallback
                logger.error("Failed to run telnet audit")
                return False
            
            # If we got here, the audit was successful (either in real mode or test fallback)
            self.results['telnet'] = auditor.results
            
            # Generate reports unless no_report flag is set
            if not self.no_report:
                auditor.generate_reports()
            else:
                print(f"{Fore.YELLOW}Skipping individual telnet report generation (--no-report specified){Style.RESET_ALL}")
            
            # Add a note about fallback in the results if it was used
            if fallback_used:
                for result in self.results['telnet']:
                    result.add_note("This audit was conducted in TEST MODE due to connection failures with real devices.")
                print(f"\n{Fore.YELLOW}Note: Telnet audit was conducted in TEST MODE due to connection failures with real devices.{Style.RESET_ALL}")
            
            return True
                
        except ImportError as e:
            logger.error(f"Failed to import telnet_audit module: {e}")
            print(f"{Fore.RED}Error: Failed to import telnet_audit module: {e}{Style.RESET_ALL}")
            print(f"Make sure telnet_audit.py is in the same directory.")
            return False
        except Exception as e:
            logger.error(f"Error running telnet audit: {e}")
            print(f"{Fore.RED}Error running telnet audit: {e}{Style.RESET_ALL}")
            return False
        finally:
            # Always restore original test mode setting
            self.test_mode = original_test_mode
    
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
    parser.add_argument("--auto-fallback", action="store_true", default=True, 
                        help="Automatically fall back to test mode if real connections fail (default: enabled)")
    parser.add_argument("--no-fallback", action="store_false", dest="auto_fallback",
                        help="Disable automatic fallback to test mode")
    parser.add_argument("--timestamp", type=str, 
                        help="Use specified timestamp for report naming (for consistency across reports)")
    parser.add_argument("--no-report", action="store_true", 
                        help="Skip individual module reports and only generate the unified report")
    
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
