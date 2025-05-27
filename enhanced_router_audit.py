#!/usr/bin/env python3
"""
Enhanced Router Audit Tool Integration Script
This script shows how to integrate the credential_manager.py and ssh_command_handler.py
enhancements with your existing router audit tool.
"""

import sys
import os
import time
import logging
import getpass
from datetime import datetime
from colorama import Fore, Style, init
from netmiko import ConnectHandler

# Import our enhancement modules
from credential_manager import CredentialManager
from ssh_command_handler import SSHCommandHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='enhanced_audit.log'
)
logger = logging.getLogger('EnhancedRouterAudit')

# Initialize colorama
init(autoreset=True)

class EnhancedRouterAudit:
    """
    Enhanced Router Audit tool that demonstrates the integration of security
    and reliability improvements
    """
    def __init__(self):
        # Initialize credential manager
        self.cred_manager = CredentialManager()
        self.master_password = None
        
        # Initialize router configurations
        self.routers = []
        self.results = []
        
    def initialize_security(self):
        """Initialize security with master password"""
        print(f"\n{Fore.CYAN}🔐 Initializing Secure Credential Management{Style.RESET_ALL}")
        self.master_password = getpass.getpass("Enter master password for credential encryption: ")
        self.cred_manager.initialize(self.master_password)
        print(f"{Fore.GREEN}✅ Secure credential system initialized{Style.RESET_ALL}")
        
    def load_encrypted_router_credentials(self, csv_file="routers_encrypted.csv"):
        """Load router configurations with encrypted credentials"""
        import csv
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'hostname' in row and 'ip_address' in row:
                        # Decrypt passwords if encrypted
                        password = row.get('password', 'cisco')
                        secret = row.get('secret', 'cisco')
                        
                        # Check if passwords are encrypted (prefixed with 'ENC:')
                        if password.startswith('ENC:'):
                            try:
                                decrypted_pw = self.cred_manager.decrypt(password[4:])
                                if decrypted_pw:
                                    password = decrypted_pw
                                else:
                                    logger.warning(f"Could not decrypt password for {row['hostname']}")
                            except Exception as e:
                                logger.error(f"Password decryption error for {row['hostname']}: {e}")
                        
                        if secret.startswith('ENC:'):
                            try:
                                decrypted_secret = self.cred_manager.decrypt(secret[4:])
                                if decrypted_secret:
                                    secret = decrypted_secret
                                else:
                                    logger.warning(f"Could not decrypt enable secret for {row['hostname']}")
                            except Exception as e:
                                logger.error(f"Secret decryption error for {row['hostname']}: {e}")
                        
                        router = {
                            'hostname': row['hostname'],
                            'host': row['ip_address'],
                            'username': row.get('username', 'admin'),
                            'password': password,
                            'secret': secret,
                            'device_type': row.get('device_type', 'cisco_ios')
                        }
                        
                        self.routers.append(router)
                        
            print(f"{Fore.GREEN}✅ Loaded {len(self.routers)} routers with decrypted credentials{Style.RESET_ALL}")
            return self.routers
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading router configurations: {e}{Style.RESET_ALL}")
            logger.error(f"Error loading router configurations: {e}")
            return []
            
    def encrypt_router_credentials(self, csv_file="routers01.csv", output_file="routers_encrypted.csv"):
        """Convert plaintext router credentials to encrypted format"""
        import csv
        
        try:
            # Read the original CSV
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)
            
            # Encrypt passwords
            for row in rows:
                if 'password' in row and row['password'] and not row['password'].startswith('ENC:'):
                    row['password'] = 'ENC:' + self.cred_manager.encrypt(row['password'])
                
                if 'secret' in row and row['secret'] and not row['secret'].startswith('ENC:'):
                    row['secret'] = 'ENC:' + self.cred_manager.encrypt(row['secret'])
            
            # Write the encrypted CSV
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            print(f"{Fore.GREEN}✅ Saved encrypted credentials to {output_file}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Error encrypting credentials: {e}{Style.RESET_ALL}")
            logger.error(f"Error encrypting credentials: {e}")
            return False
    
    def audit_router(self, router_config):
        """Perform enhanced audit of a single router with proper timeout and authentication handling"""
        router_name = router_config.get('hostname', 'UnknownRouter')
        router_ip = router_config.get('host', 'UnknownIP')
        
        # Initialize result dictionary with detailed fields
        result = {
            "hostname": router_name,
            "ip_address": router_ip,
            "ssh_status": "UNKNOWN",
            "auth_status": "UNKNOWN",
            "privilege_level": "UNKNOWN",
            "command_status": "UNKNOWN",
            "command_failures": [],
            "command_timeouts": {},
            "auth_error_details": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔍 Auditing router: {router_name} ({router_ip}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        try:
            # Connect directly to the router
            print(f"{Fore.YELLOW}🔌 Connecting to router...{Style.RESET_ALL}")
            
            # Set connection timeout to ensure it doesn't hang
            router_config['timeout'] = 10
            router_config['session_timeout'] = 15
            
            # Try to connect to the router
            try:
                connection = ConnectHandler(**router_config)
                print(f"{Fore.GREEN}✅ SSH connection established{Style.RESET_ALL}")
                result["ssh_status"] = "SUCCESS"
            except Exception as ssh_err:
                print(f"{Fore.RED}❌ SSH connection failed: {ssh_err}{Style.RESET_ALL}")
                result["ssh_status"] = "FAILED"
                result["error"] = f"SSH connection error: {ssh_err}"
                logger.error(f"SSH connection failed for {router_ip}: {ssh_err}")
                return result
            
            # Check authentication status
            if connection.is_alive():
                # Get the command prompt to determine privilege level
                prompt = connection.find_prompt()
                result["auth_status"] = "SUCCESS"
                
                # Determine privilege level
                if '#' in prompt:
                    result["privilege_level"] = "PRIVILEGED"
                    print(f"{Fore.GREEN}🗝️ Privilege level: PRIVILEGED (Enable mode){Style.RESET_ALL}")
                else:
                    result["privilege_level"] = "USER"
                    print(f"{Fore.YELLOW}🗝️ Privilege level: USER (Non-privileged mode){Style.RESET_ALL}")
                    
                    # Try to enter enable mode if not already there
                    try:
                        connection.enable()
                        prompt = connection.find_prompt()
                        if '#' in prompt:
                            result["privilege_level"] = "PRIVILEGED"
                            print(f"{Fore.GREEN}🗝️ Successfully entered privileged mode{Style.RESET_ALL}")
                    except Exception as enable_err:
                        print(f"{Fore.YELLOW}⚠️ Unable to enter privileged mode: {enable_err}{Style.RESET_ALL}")
            else:
                result["auth_status"] = "FAILED"
                result["auth_error_details"] = "Connection not properly established"
                print(f"{Fore.RED}❌ Authentication verification failed{Style.RESET_ALL}")
                logger.error(f"Authentication verification failed for {router_ip}")
                return result
            
            # Create an enhanced command handler for this connection
            cmd_handler = SSHCommandHandler(connection, timeout=5)
            
            # Define commands to run
            commands = [
                "terminal length 0",
                "show version | include IOS",
                "show platform",
                "show run | include telnet|aux|line"
            ]
            
            # Execute commands with enhanced timeout handling
            print(f"{Fore.CYAN}📋 Executing router commands with 5-second timeout...{Style.RESET_ALL}")
            cmd_results = cmd_handler.execute_multiple_commands(commands)
            
            # Process command results
            if cmd_results['summary']['all_succeeded']:
                result["command_status"] = "SUCCESS"
                print(f"{Fore.GREEN}✅ All commands executed successfully{Style.RESET_ALL}")
            elif cmd_results['summary']['successful'] > 0:
                result["command_status"] = "PARTIAL"
                result["command_failures"] = cmd_handler.get_command_failures()
                print(f"{Fore.YELLOW}⚠️ Some commands failed: {len(result['command_failures'])} failures{Style.RESET_ALL}")
            else:
                result["command_status"] = "FAILED"
                result["command_failures"] = cmd_handler.get_command_failures()
                print(f"{Fore.RED}❌ All commands failed{Style.RESET_ALL}")
            
            # Store command timing information
            for cmd, cmd_result in cmd_results.items():
                if cmd != 'summary':  # Skip the summary entry
                    result["command_timeouts"][cmd] = cmd_result.get('duration', 0)
            
            # Disconnect from router
            connection.disconnect()
            print(f"{Fore.GREEN}✅ Disconnected from router{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error during router audit: {e}{Style.RESET_ALL}")
            result["error"] = f"Audit error: {e}"
            logger.error(f"Error during router audit for {router_ip}: {e}")
            return result
    
    def run_demo(self):
        """Run a demo of the enhanced router audit capabilities"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 ENHANCED ROUTER AUDIT DEMO{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Initialize security
        self.initialize_security()
        
        # Ask if user wants to encrypt an existing router CSV file
        encrypt_csv = input("\nDo you want to encrypt an existing router CSV file? (y/n): ").lower().strip() == 'y'
        if encrypt_csv:
            csv_file = input("Enter CSV file path [routers01.csv]: ").strip() or "routers01.csv"
            output_file = input("Enter output file path [routers_encrypted.csv]: ").strip() or "routers_encrypted.csv"
            self.encrypt_router_credentials(csv_file, output_file)
        
        # Load router configurations
        csv_file = input("\nEnter router CSV file to load [routers01.csv]: ").strip() or "routers01.csv"
        self.load_encrypted_router_credentials(csv_file)
        
        if not self.routers:
            print(f"{Fore.RED}❌ No routers loaded. Cannot continue.{Style.RESET_ALL}")
            return
        
        # Audit routers
        for router in self.routers:
            result = self.audit_router(router)
            self.results.append(result)
            
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary of router audit results"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 AUDIT SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        total = len(self.results)
        
        # Count statuses
        ssh_status = {"SUCCESS": 0, "FAILED": 0, "UNKNOWN": 0}
        auth_status = {"SUCCESS": 0, "FAILED": 0, "UNKNOWN": 0}
        command_status = {"SUCCESS": 0, "PARTIAL": 0, "FAILED": 0, "UNKNOWN": 0}
        privilege_levels = {"PRIVILEGED": 0, "USER": 0, "UNKNOWN": 0}
        
        # Count failures by type
        auth_failure_reasons = {}
        command_failures = {}
        
        for r in self.results:
            ssh_status[r.get("ssh_status", "UNKNOWN")] += 1
            auth_status[r.get("auth_status", "UNKNOWN")] += 1
            command_status[r.get("command_status", "UNKNOWN")] += 1
            privilege_levels[r.get("privilege_level", "UNKNOWN")] += 1
            
            # Collect auth failure details
            if r.get("auth_status") == "FAILED" and r.get("auth_error_details"):
                reason = r.get("auth_error_details")
                if reason not in auth_failure_reasons:
                    auth_failure_reasons[reason] = 0
                auth_failure_reasons[reason] += 1
            
            # Collect command failures
            for cmd in r.get("command_failures", []):
                if cmd not in command_failures:
                    command_failures[cmd] = 0
                command_failures[cmd] += 1
        
        # Print totals
        print(f"Total routers audited: {total}")
        
        # SSH connectivity
        print(f"\n{Fore.CYAN}🔌 SSH CONNECTIVITY{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Successful: {ssh_status['SUCCESS']}/{total} ({ssh_status['SUCCESS']/total*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Failed: {ssh_status['FAILED']}/{total} ({ssh_status['FAILED']/total*100:.1f}%){Style.RESET_ALL}")
        
        # Authentication status
        print(f"\n{Fore.CYAN}🗝️ AUTHENTICATION STATUS{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Successful: {auth_status['SUCCESS']}/{total} ({auth_status['SUCCESS']/total*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Failed: {auth_status['FAILED']}/{total} ({auth_status['FAILED']/total*100:.1f}%){Style.RESET_ALL}")
        
        # Authentication failure reasons
        if auth_failure_reasons:
            print(f"\n{Fore.CYAN}📋 AUTHENTICATION FAILURE REASONS{Style.RESET_ALL}")
            for reason, count in auth_failure_reasons.items():
                print(f"{Fore.RED}❌ {reason}: {count} devices{Style.RESET_ALL}")
        
        # Command execution
        print(f"\n{Fore.CYAN}⌨️ COMMAND EXECUTION{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Full Success: {command_status['SUCCESS']}/{total} ({command_status['SUCCESS']/total*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ Partial Success: {command_status['PARTIAL']}/{total} ({command_status['PARTIAL']/total*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Failed: {command_status['FAILED']}/{total} ({command_status['FAILED']/total*100:.1f}%){Style.RESET_ALL}")
        
        # Failed commands
        if command_failures:
            print(f"\n{Fore.CYAN}📋 FAILED COMMANDS{Style.RESET_ALL}")
            for cmd, count in sorted(command_failures.items(), key=lambda x: x[1], reverse=True):
                print(f"{Fore.RED}❌ '{cmd}': {count} devices{Style.RESET_ALL}")
        
        # Privilege levels
        print(f"\n{Fore.CYAN}🔐 PRIVILEGE LEVELS{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Privileged (Enable): {privilege_levels['PRIVILEGED']}/{total} ({privilege_levels['PRIVILEGED']/total*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ User-Level Only: {privilege_levels['USER']}/{total} ({privilege_levels['USER']/total*100:.1f}%){Style.RESET_ALL}")
        
        # Per-device details
        print(f"\n{Fore.CYAN}📱 DEVICE DETAILS{Style.RESET_ALL}")
        print(f"{'HOSTNAME':<20} {'IP ADDRESS':<15} {'SSH':<8} {'AUTH':<8} {'PRIVILEGE':<10} {'COMMANDS':<8}")
        print("-" * 70)
        
        for device in self.results:
            hostname = device["hostname"]
            if len(hostname) > 19:
                hostname = hostname[:16] + "..."
            ip = device["ip_address"]
            ssh = device.get("ssh_status", "UNKNOWN")
            auth = device.get("auth_status", "UNKNOWN")
            priv = device.get("privilege_level", "UNKNOWN")
            cmd = device.get("command_status", "UNKNOWN")
            
            # Color indicators
            ssh_color = Fore.GREEN if ssh == "SUCCESS" else Fore.RED
            auth_color = Fore.GREEN if auth == "SUCCESS" else Fore.RED
            priv_color = Fore.GREEN if priv == "PRIVILEGED" else Fore.YELLOW if priv == "USER" else Fore.RED
            cmd_color = Fore.GREEN if cmd == "SUCCESS" else Fore.YELLOW if cmd == "PARTIAL" else Fore.RED
            
            print(f"{hostname:<20} {ip:<15} {ssh_color}{ssh:<8}{Style.RESET_ALL} {auth_color}{auth:<8}{Style.RESET_ALL} {priv_color}{priv:<10}{Style.RESET_ALL} {cmd_color}{cmd:<8}{Style.RESET_ALL}")


if __name__ == "__main__":
    auditor = EnhancedRouterAudit()
    auditor.run_demo()
