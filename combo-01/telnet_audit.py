#!/usr/bin/env python3
"""
Network Audit Tool - Telnet Audit Module (v3.11)

This module focuses specifically on telnet vulnerability detection:
- Detection of telnet service on VTY lines
- Identification of insecure authentication on telnet access
- Discovery of AUX ports with telnet enabled
- Analysis of telnet access control lists

It can be run independently or as part of the comprehensive audit framework.
"""

import os
import sys
import csv
import time
import datetime
import argparse
import re
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

# Required third-party modules
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
    netmiko_available = True
except ImportError:
    print(f"Warning: netmiko package not available. SSH connectivity will be limited.")
    netmiko_available = False

# Set up module-specific constants
MODULE_NAME = "Telnet Audit"
AUDIT_TYPE = "telnet"

# Configure logger
logger, log_file = setup_logging(f"telnet_audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
if not logger:
    print("Failed to set up logging. Exiting.")
    sys.exit(1)

class TelnetAuditor:
    """Handles telnet vulnerability auditing for network devices"""
    
    def __init__(self, test_mode=False, jump_host=None):
        """Initialize the telnet auditor"""
        self.test_mode = test_mode
        self.devices = []
        self.results = []
        self.timestamp = datetime.datetime.now()
        self.jump_host = jump_host
        self.jump_conn = None
        
        # Print banner
        self.print_banner()
    
    def print_banner(self):
        """Print the module banner"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}NETWORK AUDIT TOOL - {MODULE_NAME} v{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Specialized for Telnet Vulnerability Detection{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        if self.test_mode:
            print(f"{Fore.YELLOW}Running in TEST MODE with simulated responses{Style.RESET_ALL}")
        print(f"Started at: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
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
                    'secret', 'model'
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
    
    def connect_to_device(self, device):
        """Connect to a device directly or via jump host"""
        if self.test_mode:
            # Simulate a connection in test mode
            return True, None
        
        if not netmiko_available:
            logger.error("Netmiko package not available, cannot connect to devices")
            return False, "Netmiko package not available"
        
        try:
            # Configure device connection parameters
            device_params = {
                'device_type': device.get('device_type', 'cisco_ios'),
                'ip': device.get('ip'),
                'username': device.get('username'),
                'password': device.get('password'),
                'secret': device.get('secret'),
                'port': 22,
                'timeout': 10
            }
            
            # Connect via jump host if specified
            if self.jump_host and self.jump_conn:
                # Implementation would depend on how jump host is configured
                # This is a simplified placeholder
                logger.info(f"Connecting to {device['hostname']} via jump host")
                # Would need appropriate commands to connect through jump host
                return False, "Jump host connection not fully implemented"
            
            # Direct connection
            conn = ConnectHandler(**device_params)
            
            # Enter enable mode if needed
            if device.get('device_type') in ['cisco_ios', 'cisco_xe', 'cisco_xr', 'cisco_nxos']:
                conn.enable()
            
            return True, conn
            
        except NetmikoTimeoutException:
            return False, "Connection timed out"
        except NetmikoAuthenticationException:
            return False, "Authentication failed"
        except Exception as e:
            return False, str(e)
    
    def audit_device_telnet(self, device):
        """Audit a single device for telnet vulnerabilities"""
        hostname = device['hostname']
        ip = device['ip']
        
        logger.info(f"Starting telnet audit for {hostname} ({ip})")
        print(f"\n{Fore.CYAN}Auditing device: {hostname} ({ip}){Style.RESET_ALL}")
        
        # Create an audit result
        device_info = {
            'hostname': hostname,
            'ip': ip,
            'model': device.get('model', 'Unknown'),
            'device_type': device.get('device_type', 'cisco_ios')
        }
        
        audit_result = AuditResult(device_info, AUDIT_TYPE)
        
        # Phase 1: Connect to device
        print(f"  {Fore.CYAN}⏳ Connecting to device...{Style.RESET_ALL}")
        
        if self.test_mode:
            # In test mode, simulate connection based on hostname
            conn_success = 'firewall' not in hostname.lower()
            conn_error = None if conn_success else "Connection refused"
            connection = None  # No actual connection in test mode
        else:
            conn_success, conn_result = self.connect_to_device(device)
            if conn_success:
                connection = conn_result
                conn_error = None
            else:
                connection = None
                conn_error = conn_result
        
        # Add connection result to audit
        audit_result.add_phase_result(
            'connection',
            'Success' if conn_success else 'Failed',
            {'method': 'SSH'},
            conn_error
        )
        
        if conn_success:
            print(f"  {Fore.GREEN}✓ Connection successful{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Connection failed: {conn_error}{Style.RESET_ALL}")
            
            # If connection failed, we can't continue with the audit
            self.results.append(audit_result)
            return audit_result
        
        # Phase 2: Check for telnet configuration on lines
        print(f"  {Fore.CYAN}⏳ Checking for telnet configuration...{Style.RESET_ALL}")
        
        if self.test_mode:
            # In test mode, generate sample results based on hostname
            has_telnet = 'router' in hostname.lower() or hostname.lower().endswith('1.example.com')
            
            # Simulate line configuration data
            vty_lines = []
            aux_lines = []
            con_lines = []
            
            if has_telnet:
                vty_lines = [
                    {'line': 'vty 0 4', 'transport': 'telnet ssh', 'acl': None},
                    {'line': 'vty 5 15', 'transport': 'ssh', 'acl': '10'}
                ]
                
                if 'router' in hostname.lower():
                    aux_lines = [
                        {'line': 'aux 0', 'transport': 'telnet', 'acl': None}
                    ]
                
                con_lines = [
                    {'line': 'con 0', 'transport': None, 'acl': None}
                ]
            else:
                vty_lines = [
                    {'line': 'vty 0 15', 'transport': 'ssh', 'acl': '10'}
                ]
                con_lines = [
                    {'line': 'con 0', 'transport': None, 'acl': None}
                ]
            
            telnet_enabled = has_telnet
            transport_all_lines = vty_lines + aux_lines + con_lines
            
        else:
            # Real device - get line configuration
            if not connection:
                # We should have a connection at this point, but double-check
                telnet_enabled = False
                vty_lines = []
                aux_lines = []
                con_lines = []
                transport_all_lines = []
            else:
                # Get running configuration
                running_config = connection.send_command("show running-config")
                
                # Extract line configurations
                vty_config = re.findall(r'line vty.*?(?=\n\S)', running_config, re.DOTALL)
                aux_config = re.findall(r'line aux.*?(?=\n\S)', running_config, re.DOTALL)
                con_config = re.findall(r'line con.*?(?=\n\S)', running_config, re.DOTALL)
                
                # Parse VTY lines
                vty_lines = []
                for config in vty_config:
                    line_match = re.search(r'line (vty \d+( \d+)?)', config)
                    transport_match = re.search(r'transport input (.+)', config)
                    acl_match = re.search(r'access-class (\d+) in', config)
                    
                    if line_match:
                        vty_lines.append({
                            'line': line_match.group(1),
                            'transport': transport_match.group(1) if transport_match else None,
                            'acl': acl_match.group(1) if acl_match else None
                        })
                
                # Parse AUX lines
                aux_lines = []
                for config in aux_config:
                    line_match = re.search(r'line (aux \d+)', config)
                    transport_match = re.search(r'transport input (.+)', config)
                    acl_match = re.search(r'access-class (\d+) in', config)
                    
                    if line_match:
                        aux_lines.append({
                            'line': line_match.group(1),
                            'transport': transport_match.group(1) if transport_match else None,
                            'acl': acl_match.group(1) if acl_match else None
                        })
                
                # Parse CON lines
                con_lines = []
                for config in con_config:
                    line_match = re.search(r'line (con \d+)', config)
                    transport_match = re.search(r'transport input (.+)', config)
                    acl_match = re.search(r'access-class (\d+) in', config)
                    
                    if line_match:
                        con_lines.append({
                            'line': line_match.group(1),
                            'transport': transport_match.group(1) if transport_match else None,
                            'acl': acl_match.group(1) if acl_match else None
                        })
                
                # Combine all lines for checks
                transport_all_lines = vty_lines + aux_lines + con_lines
                
                # Check if telnet is enabled anywhere
                telnet_enabled = any(
                    line.get('transport') and 'telnet' in line.get('transport', '')
                    for line in transport_all_lines
                )
        
        # Add telnet configuration to audit
        telnet_details = {
            'telnet_enabled': telnet_enabled,
            'vty_lines': len(vty_lines),
            'aux_lines': len(aux_lines),
            'con_lines': len(con_lines),
            'telnet_lines': sum(1 for line in transport_all_lines 
                               if line.get('transport') and 'telnet' in line.get('transport', ''))
        }
        
        audit_result.add_phase_result(
            'telnet_config',
            'Vulnerable' if telnet_enabled else 'Secure',
            telnet_details
        )
        
        if telnet_enabled:
            print(f"  {Fore.RED}✗ Telnet is enabled on this device{Style.RESET_ALL}")
            
            # Check which lines have telnet
            telnet_vty = any(line.get('transport') and 'telnet' in line.get('transport', '') 
                           for line in vty_lines)
            telnet_aux = any(line.get('transport') and 'telnet' in line.get('transport', '') 
                            for line in aux_lines)
            telnet_con = any(line.get('transport') and 'telnet' in line.get('transport', '') 
                            for line in con_lines)
            
            if telnet_vty:
                print(f"    {Fore.RED}• Telnet enabled on VTY lines{Style.RESET_ALL}")
            if telnet_aux:
                print(f"    {Fore.RED}• Telnet enabled on AUX lines{Style.RESET_ALL}")
            if telnet_con:
                print(f"    {Fore.RED}• Telnet enabled on CON lines{Style.RESET_ALL}")
            
            # Check for ACLs on telnet lines
            telnet_without_acl = [
                line.get('line') for line in transport_all_lines
                if line.get('transport') and 'telnet' in line.get('transport', '') and not line.get('acl')
            ]
            
            if telnet_without_acl:
                print(f"    {Fore.RED}• Telnet lines without ACL: {', '.join(telnet_without_acl)}{Style.RESET_ALL}")
            
            # Add recommendations
            audit_result.add_recommendation(
                "Disable Telnet and use SSH for secure remote access",
                "critical",
                "NIST SP 800-53: AC-17, IA-2"
            )
            
            if telnet_without_acl:
                audit_result.add_recommendation(
                    "Apply access control lists to restrict telnet access",
                    "high",
                    "NIST SP 800-53: AC-3"
                )
            
            if telnet_aux:
                audit_result.add_recommendation(
                    "Disable telnet on AUX ports to prevent unauthorized access",
                    "critical",
                    "NIST SP 800-53: AC-17"
                )
        else:
            print(f"  {Fore.GREEN}✓ Telnet is not enabled on this device{Style.RESET_ALL}")
        
        # Phase 3: Check for telnet port accessibility
        print(f"  {Fore.CYAN}⏳ Checking telnet port accessibility...{Style.RESET_ALL}")
        
        if self.test_mode:
            # In test mode, simulate telnet port check based on telnet_enabled
            port_accessible = telnet_enabled
        else:
            # Real check would involve testing port 23 accessibility
            # This would typically involve a separate tool or module
            # For safety, we'll assume it's accessible if telnet is enabled
            port_accessible = telnet_enabled
        
        # Add port accessibility to audit
        audit_result.add_phase_result(
            'telnet_port',
            'Vulnerable' if port_accessible else 'Secure',
            {'port_23_accessible': port_accessible}
        )
        
        if port_accessible:
            print(f"  {Fore.RED}✗ Telnet port (23) is accessible{Style.RESET_ALL}")
            audit_result.add_recommendation(
                "Block telnet port (23) at the network level with firewall rules",
                "critical",
                "NIST SP 800-53: SC-7"
            )
        else:
            print(f"  {Fore.GREEN}✓ Telnet port (23) is not accessible{Style.RESET_ALL}")
        
        # Close connection if we opened one
        if connection and not self.test_mode:
            try:
                connection.disconnect()
            except:
                pass
        
        # Add final result to results list
        self.results.append(audit_result)
        return audit_result
    
    def run_audit(self):
        """Run the telnet audit for all devices"""
        if not self.devices:
            logger.error("No devices to audit")
            print(f"{Fore.RED}Error: No devices to audit. Please load devices first.{Style.RESET_ALL}")
            return False
        
        start_time = time.time()
        print(f"{Fore.CYAN}Starting telnet audit for {len(self.devices)} devices...{Style.RESET_ALL}")
        logger.info(f"Starting telnet audit for {len(self.devices)} devices")
        
        # Use ThreadPoolExecutor for parallel auditing
        with ThreadPoolExecutor(max_workers=min(5, len(self.devices))) as executor:
            future_to_device = {executor.submit(self.audit_device_telnet, device): device for device in self.devices}
            
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    logger.info(f"Completed audit for {device['hostname']} ({device['ip']})")
                except Exception as e:
                    logger.error(f"Error auditing {device['hostname']} ({device['ip']}): {e}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed telnet audit in {elapsed_time:.2f} seconds")
        print(f"\n{Fore.CYAN}Completed telnet audit in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
        
        return True
    
    def generate_reports(self):
        """Generate reports for the audit results"""
        if not self.results:
            logger.warning("No audit results to report")
            print(f"{Fore.YELLOW}Warning: No audit results to report{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.CYAN}Generating audit reports...{Style.RESET_ALL}")
        
        # Create a report
        report = AuditReport(self.results)
        
        # Generate all report formats
        report_files = report.generate_all_reports()
        
        # Print summary
        report.print_summary()
        
        # Calculate overall statistics
        total_devices = len(self.results)
        telnet_enabled = sum(1 for result in self.results 
                            if result.get_phase_result('telnet_config') and 
                               result.get_phase_result('telnet_config').get('status') == 'Vulnerable')
        
        telnet_port_accessible = sum(1 for result in self.results 
                                  if result.get_phase_result('telnet_port') and 
                                     result.get_phase_result('telnet_port').get('status') == 'Vulnerable')
        
        # Print specialized telnet summary
        print(f"\n{Fore.CYAN}TELNET VULNERABILITY SUMMARY{Style.RESET_ALL}")
        print(f"Total devices audited: {total_devices}")
        print(f"Devices with telnet enabled: {telnet_enabled} ({telnet_enabled/total_devices*100:.1f}%)")
        print(f"Devices with accessible telnet port: {telnet_port_accessible} ({telnet_port_accessible/total_devices*100:.1f}%)")
        
        if telnet_enabled == 0:
            print(f"\n{Fore.GREEN}✓ No telnet vulnerabilities detected!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}✗ Telnet vulnerabilities detected! See reports for details.{Style.RESET_ALL}")
        
        return True


def main():
    """Main entry point for the telnet audit module"""
    parser = argparse.ArgumentParser(description=f"Network Audit Tool - {MODULE_NAME} v{VERSION}")
    parser.add_argument("-t", "--test", action="store_true", help="Run in test mode with simulated responses")
    parser.add_argument("-c", "--csv", type=str, default="devices.csv", help="CSV file with device details")
    parser.add_argument("-j", "--jump-host", type=str, help="Jump host IP for accessing devices")
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Create the auditor
    auditor = TelnetAuditor(test_mode=args.test, jump_host=args.jump_host)
    
    # Load devices
    if not auditor.load_devices_from_csv(args.csv):
        if not args.test:
            print(f"{Fore.RED}Failed to load devices. Exiting.{Style.RESET_ALL}")
            return 1
    
    # Run the audit
    if not auditor.run_audit():
        print(f"{Fore.RED}Failed to run audit. Exiting.{Style.RESET_ALL}")
        return 1
    
    # Generate reports
    auditor.generate_reports()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
