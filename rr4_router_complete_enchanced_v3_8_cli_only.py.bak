#!/usr/bin/env python3
"""
Cisco AUX Port Telnet Audit Script via Jump Host
Connects to jump host 172.16.39.128 and audits routers from CSV file
Compatible with Linux and Windows
"""

import csv
import json
import os
import sys
import getpass
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
from pathlib import Path
import colorama
from colorama import Fore, Style

try:
    from netmiko import ConnectHandler
    import paramiko
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install netmiko paramiko")
    sys.exit(1)

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a custom formatter with colors
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

# Add colored console handler
console = logging.StreamHandler()
console.setFormatter(ColoredFormatter())
logger.handlers = [logging.FileHandler('audit.log'), console]


class JumpHostAuditor:
    def __init__(self):
        # Default values that will be configurable
        self.jump_host = {
            "device_type": "linux",
            "host": "172.16.39.128",  # Default, will be configurable
            "username": "root",      # Default, will be configurable
            "password": None
        }
        self.routers = []
        self.results = []
        self.env_file = Path(".env")

    def load_environment(self):
        """Load or create .env file with jump host configuration"""
        env_data = {}
        # Default values
        default_host = self.jump_host["host"]
        default_username = self.jump_host["username"]
        jump_password = None
        
        # Try to load from .env file if it exists
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_data[key.strip()] = value.strip().strip('"\'')
                            
                # Check for saved jump host values
                if 'JUMP_HOST' in env_data:
                    default_host = env_data['JUMP_HOST']
                if 'JUMP_USERNAME' in env_data:
                    default_username = env_data['JUMP_USERNAME']
                if 'JUMP_HOST_PASSWORD' in env_data:
                    jump_password = env_data['JUMP_HOST_PASSWORD']
                    use_saved = input(f"Use saved jump host password? (y/n): ").lower().strip()
                    if use_saved != 'y':
                        jump_password = None
                        
            except Exception as e:
                logger.warning(f"Error reading .env file: {e}")
        
        # Prompt for jump host configuration
        print("\nJump Host Configuration:")
        host = input(f"Jump host IP [default: {default_host}]: ").strip()
        if not host:
            host = default_host
            
        username = input(f"Jump host username [default: {default_username}]: ").strip()
        if not username:
            username = default_username
            
        if not jump_password:
            jump_password = getpass.getpass(f"Enter jump host ({host}) password: ")
            
            save_config = input("Save jump host configuration to .env file? (y/n): ").lower().strip()
            if save_config == 'y':
                try:
                    with open(self.env_file, 'w') as f:
                        f.write(f'JUMP_HOST="{host}"\n')
                        f.write(f'JUMP_USERNAME="{username}"\n')
                        f.write(f'JUMP_HOST_PASSWORD="{jump_password}"\n')
                    logger.info("Jump host configuration saved to .env file")
                except Exception as e:
                    logger.warning(f"Could not save configuration: {e}")

        # Update jump host configuration
        self.jump_host["host"] = host
        self.jump_host["username"] = username
        self.jump_host["password"] = jump_password
        
        logger.info(f"Jump host configured: {username}@{host}")

    def load_routers_from_csv(self, csv_file="routers01.csv"):
        """Load router configurations from CSV file with the following format:
        index (integer), hostname (text), management_ip, wan_ip, model_name (free text)
        """
        if not Path(csv_file).exists():
            # Create sample CSV file with new format
            sample_data = [
                ["index", "hostname", "management_ip", "wan_ip", "model_name"],
                ["0", "RTR-CORE-01", "192.168.1.1", "203.0.113.1", "Cisco 4431 Integrated Services Router"],
                ["1", "RTR-EDGE-02", "192.168.1.2", "203.0.113.2", "Cisco 4451-X Integrated Services Router"],
                ["2", "RTR-BRANCH-03", "192.168.1.3", "203.0.113.3", "Cisco 3945 Integrated Services Router"]
            ]

            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(sample_data)

            logger.info(f"Created sample {csv_file} file. Please update with your router details.")

        try:
            # Check if we should use the default device type or prompt the user
            device_type = os.getenv('DEVICE_TYPE', 'cisco_xe')
            if device_type == 'cisco_xe':
                use_default = input(f"Use default device type 'cisco_xe'? (y/n, default: y): ").lower().strip()
                if use_default == 'n':
                    device_type = input("Enter device type (e.g., cisco_ios, cisco_xe, etc.): ").strip()

            username = input("Enter router SSH username: ").strip()
            password = getpass.getpass("Enter router SSH password: ")
            secret = getpass.getpass("Enter enable secret (press Enter if none): ")
            if not secret:
                secret = password  # Use password as secret if none provided

            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Ensure index is an integer
                        index = int(row['index'])
                        
                        # Create router config with management IP as the primary connection IP
                        router_config = {
                            "device_type": device_type,
                            "host": row['management_ip'].strip(),
                            "username": username,
                            "password": password,
                            "secret": secret,
                            "hostname": row['hostname'].strip(),  # Use the actual hostname field
                            "wan_ip": row['wan_ip'].strip(),
                            "model": row['model_name'].strip(),
                            "index": index  # Store the index as an integer
                        }
                        self.routers.append(router_config)
                        
                    except ValueError as e:
                        logger.warning(f"Skipping row with invalid index value: {row['index']} - {e}")

            logger.info(f"Loaded {len(self.routers)} routers from {csv_file} with device type: {device_type}")

        except FileNotFoundError:
            logger.error(f"CSV file {csv_file} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            sys.exit(1)

    def test_jump_host_connection(self):
        """Test connection to jump host"""
        logger.info(f"Testing jump host connection to {self.jump_host['host']}...")
        try:
            with ConnectHandler(**self.jump_host, timeout=10) as conn:
                output = conn.send_command("hostname", delay_factor=1)
                logger.info(f"✓ Connected to jump host: {output.strip()}")
                return True
        except Exception as e:
            logger.error(f"✗ Jump host connection failed: {e}")
            return False

    def audit_router_via_jump(self, router_config):
        """Audit a single router via jump host"""
        router_name = router_config["hostname"]
        router_ip = router_config["host"]
        model = router_config.get("model", "Unknown")

        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔄 STARTING AUDIT: {router_name} ({router_ip}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}📱 MODEL: {model}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        logger.info(f"Auditing {router_name} ({router_ip}) via jump host...")

        result = {
            "hostname": router_name,
            "ip_address": router_ip,
            "line": "connection_failed",
            "telnet_allowed": "UNKNOWN",
            "login_method": "UNKNOWN",
            "exec_timeout": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
            "connection_method": "jump_host"
        }

        try:
            # Connect to jump host first
            with ConnectHandler(**self.jump_host, timeout=15) as jump_conn:
                # Method 1: Try using sshpass (Linux/Unix)
                ssh_command = f"sshpass -p '{router_config['password']}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {router_config['username']}@{router_ip}"

                try:
                    # Send SSH command to connect to router
                    print(f"{Fore.YELLOW}🔌 Connecting to router using sshpass method...{Style.RESET_ALL}")
                    output = jump_conn.send_command_timing(ssh_command, delay_factor=2, max_loops=10)
                    print(f"{Fore.YELLOW}📤 Command sent: {ssh_command}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}📥 Initial response received ({len(output)} chars){Style.RESET_ALL}")

                    # Check if we got a router prompt
                    if '>' not in output and '#' not in output:
                        # If sshpass failed, try expect-style login
                        print(f"{Fore.YELLOW}⚠️ sshpass method failed, switching to manual SSH method{Style.RESET_ALL}")
                        raise Exception("sshpass method failed, trying manual SSH")

                except:
                    # Method 2: Manual SSH with expect-style interaction
                    logger.info(f"Trying manual SSH for {router_name}...")
                    print(f"{Fore.YELLOW}🔄 Switching to manual SSH with interactive login{Style.RESET_ALL}")
                    ssh_command = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {router_config['username']}@{router_ip}"
                    print(f"{Fore.YELLOW}📤 Command: {ssh_command}{Style.RESET_ALL}")

                    # Send SSH command
                    jump_conn.write_channel(ssh_command + '\n')

                    # Wait for password prompt and send password
                    output = ""
                    print(f"{Fore.YELLOW}🕒 Waiting for password prompt...{Style.RESET_ALL}")
                    for i in range(15):  # Wait up to 15 seconds
                        time.sleep(1)
                        new_output = jump_conn.read_channel()
                        if new_output:
                            print(f"{Fore.CYAN}📥 Received: {new_output.strip()}{Style.RESET_ALL}")
                        output += new_output

                        if 'password:' in output.lower() or 'Password:' in output:
                            print(f"{Fore.GREEN}🔑 Password prompt detected, sending credentials...{Style.RESET_ALL}")
                            jump_conn.write_channel(router_config['password'] + '\n')
                            time.sleep(2)
                            new_response = jump_conn.read_channel()
                            print(f"{Fore.CYAN}📥 Response after password: {len(new_response)} chars{Style.RESET_ALL}")
                            output += new_response
                            break
                        elif '>' in output or '#' in output:
                            print(f"{Fore.GREEN}✅ Router prompt detected!{Style.RESET_ALL}")
                            break
                        elif 'Connection refused' in output or 'No route to host' in output:
                            print(f"{Fore.RED}❌ Connection refused or no route to host{Style.RESET_ALL}")
                            raise Exception(f"Cannot connect to {router_ip}")
                        
                        print(f"{Fore.YELLOW}⏳ Still waiting... ({i+1}/15 seconds){Style.RESET_ALL}")

                # At this point, we should be connected to the router
                # Check if we need to enter enable mode
                if '#' not in output:
                    print(f"{Fore.YELLOW}🔒 Entering enable mode...{Style.RESET_ALL}")
                    jump_conn.write_channel("enable\n")
                    time.sleep(1)
                    output = jump_conn.read_channel()
                    if "assword" in output:
                        print(f"{Fore.YELLOW}🔑 Enable password prompt detected, sending secret...{Style.RESET_ALL}")
                        jump_conn.write_channel(router_config['secret'] + '\n')
                        time.sleep(1)
                        output = jump_conn.read_channel()
                        print(f"{Fore.GREEN}✅ Enable mode activated{Style.RESET_ALL}")

                # Get and run show commands
                show_commands = [
                    "terminal length 0",
                    "show run | include aux",
                    "show run | include line aux",
                    "show run | begin line aux",
                    "show version | include IOS"
                ]

                print(f"{Fore.CYAN}📋 Executing router commands...{Style.RESET_ALL}")
                for cmd in show_commands:
                    print(f"{Fore.YELLOW}📤 Sending command: {cmd}{Style.RESET_ALL}")
                    jump_conn.write_channel(cmd + '\n')
                    time.sleep(1)
                
                # Run our audit command
                audit_cmd = "show running-config | include telnet|aux|line"  # Show telnet and aux port config
                print(f"{Fore.YELLOW}📤 Sending audit command: {audit_cmd}{Style.RESET_ALL}")
                jump_conn.write_channel(audit_cmd + '\n')
                time.sleep(3)  # Give time for command to execute

                # Collect output
                time.sleep(2)
                output = jump_conn.read_channel()
                print(f"{Fore.GREEN}📥 Received configuration data: {len(output)} chars{Style.RESET_ALL}")
                
                # Exit the router
                print(f"{Fore.YELLOW}🚪 Exiting router session...{Style.RESET_ALL}")
                jump_conn.write_channel("exit\n")
                time.sleep(1)

                # Parse the router output
                if output and len(output.strip()) > 10:  # Ensure we got substantial output
                    print(f"{Fore.CYAN}🔍 Analyzing router configuration...{Style.RESET_ALL}")
                    result = self.parse_router_output(output, router_name, router_ip)
                    
                    # Show result summary for this router
                    risk_color = Fore.RED if result["risk_level"] in ["CRITICAL", "HIGH"] else \
                                 Fore.YELLOW if result["risk_level"] == "MEDIUM" else \
                                 Fore.GREEN if result["risk_level"] in ["LOW", "SECURE"] else Fore.WHITE
                    
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    print(f"{risk_color}🏁 AUDIT COMPLETE: {router_name} ({router_ip}){Style.RESET_ALL}")
                    print(f"{risk_color}⚠️ Risk Level: {result['risk_level']}{Style.RESET_ALL}")
                    print(f"{risk_color}🔐 Telnet Allowed: {result['telnet_allowed']}{Style.RESET_ALL}")
                    print(f"{risk_color}🔑 Login Method: {result['login_method']}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    
                    return result
                else:
                    raise Exception("No meaningful output received from router")

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"✗ {router_name} - {error_msg}")

        return result

    def parse_router_output(self, output, fallback_hostname, router_ip):
        """Parse router output and assess security risk"""
        lines = output.strip().split('\n')

        # Clean up the output (remove command echo and prompts)
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip command echo, prompts, and empty lines
            if (line and
                    not line.startswith('show run') and
                    not line.endswith('#') and
                    not line.endswith('>') and
                    not 'show run | include' in line):
                cleaned_lines.append(line)

        # Initialize parsing results
        hostname = fallback_hostname
        aux_line = "line aux 0"  # default
        telnet_allowed = "NO"
        login_method = "unknown"
        exec_timeout = "default"

        # Parse each line
        for line in cleaned_lines:
            if line.startswith("hostname"):
                parts = line.split()
                if len(parts) >= 2:
                    hostname = parts[1]
            elif line.startswith("line aux"):
                aux_line = line
            elif "transport input" in line:
                if re.search(r"transport input.*(all|telnet)", line, re.IGNORECASE):
                    telnet_allowed = "YES"
                elif re.search(r"transport input.*(ssh|none)", line, re.IGNORECASE):
                    telnet_allowed = "NO"
            elif line.strip() == "login":
                login_method = "line_password"
            elif "login local" in line:
                login_method = "local"
            elif "login authentication" in line:
                login_method = "aaa"
            elif "exec-timeout" in line:
                timeout_match = re.search(r"exec-timeout (\d+) (\d+)", line)
                if timeout_match:
                    min_val, sec_val = timeout_match.groups()
                    if min_val == "0" and sec_val == "0":
                        exec_timeout = "never"
                    else:
                        exec_timeout = f"{min_val}m{sec_val}s"

        # If no login method found but telnet is enabled, it might be no authentication
        if login_method == "unknown" and telnet_allowed == "YES":
            login_method = "none"

        # Risk assessment logic
        risk_level = self.assess_risk(telnet_allowed, login_method, exec_timeout)

        return {
            "hostname": hostname,
            "ip_address": router_ip,
            "line": aux_line,
            "telnet_allowed": telnet_allowed,
            "login_method": login_method,
            "exec_timeout": exec_timeout,
            "risk_level": risk_level,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
            "connection_method": "jump_host"
        }

    def assess_risk(self, telnet_allowed, login_method, exec_timeout):
        """Assess security risk based on configuration"""
        if telnet_allowed != "YES":
            return "LOW"

        # Telnet is enabled, assess based on other factors
        if login_method in ["unknown", "none"]:
            return "CRITICAL"
        elif login_method == "line_password":
            return "HIGH"
        elif login_method in ["local", "aaa"]:
            if exec_timeout == "never":
                return "MEDIUM"
            else:
                return "MEDIUM"

        return "MEDIUM"

    def run_audit(self, max_workers=3):
        """Run audit across all routers via jump host"""
        if not self.test_jump_host_connection():
            logger.error("Jump host connection failed, cannot continue")
            return False

        total_routers = len(self.routers)
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 STARTING FULL AUDIT PROCESS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📡 Jump Host: {self.jump_host['host']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🖥️  Total Routers: {total_routers}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⚙️  Concurrent Workers: {max_workers}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        logger.info(f"Starting audit of {total_routers} routers with {max_workers} workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            print(f"{Fore.YELLOW}🔄 Submitting audit tasks to thread pool...{Style.RESET_ALL}")
            futures = {executor.submit(self.audit_router_via_jump, router): router for router in self.routers}
            completed = 0
            
            for future in as_completed(futures):
                router = futures[future]
                completed += 1
                try:
                    result = future.result()
                    self.results.append(result)
                    status = f"✅ SUCCESS" if result["error"] is None else f"❌ FAILED: {result['error']}"
                    risk_color = Fore.RED if result["risk_level"] in ["CRITICAL", "HIGH"] else \
                                 Fore.YELLOW if result["risk_level"] == "MEDIUM" else \
                                 Fore.GREEN if result["risk_level"] in ["LOW", "SECURE"] else Fore.WHITE
                    
                    print(f"\n{Fore.CYAN}🔄 PROGRESS: {completed}/{total_routers} ({completed/total_routers*100:.1f}%){Style.RESET_ALL}")
                    print(f"{risk_color}🔍 {router['hostname']} ({router['host']}) - {status}{Style.RESET_ALL}")
                    print(f"{risk_color}⚠️ Risk: {result['risk_level']} | Telnet: {result['telnet_allowed']} | Login: {result['login_method']}{Style.RESET_ALL}")
                    
                    logger.info(f"Completed audit for {router['hostname']} ({router['host']})")
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Error auditing {router['hostname']} ({router['host']}): {error_message}")
                    
                    print(f"\n{Fore.CYAN}🔄 PROGRESS: {completed}/{total_routers} ({completed/total_routers*100:.1f}%){Style.RESET_ALL}")
                    print(f"{Fore.RED}❌ {router['hostname']} ({router['host']}) - FAILED{Style.RESET_ALL}")
                    print(f"{Fore.RED}⚠️ Error: {error_message}{Style.RESET_ALL}")
                    
                    self.results.append({
                        "hostname": router['hostname'],
                        "ip_address": router['host'],
                        "line": "connection_failed",
                        "telnet_allowed": "UNKNOWN",
                        "login_method": "UNKNOWN",
                        "exec_timeout": "UNKNOWN",
                        "risk_level": "UNKNOWN",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "error": error_message,
                        "connection_method": "jump_host"
                    })

        return True

    def generate_reports(self):
        """Generate CSV report and summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"aux_telnet_audit_{timestamp}.csv"

        # CSV Report
        fieldnames = ["hostname", "ip_address", "line", "telnet_allowed", "login_method",
                      "exec_timeout", "risk_level", "connection_method", "timestamp", "error"]

        with open(csv_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        # Console Summary
        self.print_summary()

        logger.info(f"Detailed report saved to: {csv_filename}")
        return csv_filename

    def print_summary(self):
        """Print comprehensive audit summary to console with detailed formatting"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r["error"] is None)
        telnet_enabled = sum(1 for r in self.results if r["telnet_allowed"] == "YES")
        
        # Count risk levels
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "SECURE": 0, "UNKNOWN": 0}
        for result in self.results:
            risk_level = result["risk_level"]
            risk_counts[risk_level] += 1

        # Risk level descriptions
        risk_descriptions = {
            "CRITICAL": "Urgent remediation required - Major security vulnerabilities present",
            "HIGH": "Immediate attention needed - Significant security issues detected",
            "MEDIUM": "Remediation recommended - Notable security concerns identified",
            "LOW": "Minor issues - Security improvements suggested",
            "SECURE": "No significant issues detected - Good security posture",
            "UNKNOWN": "Assessment incomplete - Unable to determine security status"
        }
        
        # Error categories and descriptions
        error_categories = {
            "connection_failed": "Could not establish connection to device",
            "authentication_failed": "Failed to authenticate with provided credentials",
            "timeout": "Connection or command timed out",
            "permission_denied": "Insufficient privileges to execute commands",
            "command_error": "Error executing commands on device",
            "parse_error": "Error parsing device configuration output"
        }

        # HEADER
        print("\n" + "═" * 80)
        print(f"{'CISCO ROUTER SECURITY AUDIT REPORT':^80}")
        print(f"{'GENERATED VIA JUMP HOST':^80}")
        print("═" * 80)
        
        # AUDIT INFORMATION
        print(f"\n{'📊 AUDIT SUMMARY':^80}")
        print("-" * 80)
        print(f"📍 Jump Host:           {self.jump_host['host']}")
        print(f"🕒 Timestamp:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 Total Routers:       {total}")
        success_pct = (successful/total*100) if total > 0 else 0
        failure_pct = ((total-successful)/total*100) if total > 0 else 0
        telnet_pct = (telnet_enabled/total*100) if total > 0 else 0
        print(f"✅ Successfully Audited: {successful} ({success_pct:.1f}%)")
        print(f"❌ Connection Failures: {total - successful} ({failure_pct:.1f}%)")
        print(f"⚠️ Telnet Enabled:      {telnet_enabled} ({telnet_pct:.1f}%)")
        
        # RISK DISTRIBUTION
        print(f"\n{'📈 RISK DISTRIBUTION':^80}")
        print("-" * 80)
        for risk, count in risk_counts.items():
            if count > 0:
                percentage = count/total*100 if total > 0 else 0
                indicator = "🔴" if risk in ["CRITICAL", "HIGH"] else "🟠" if risk == "MEDIUM" else "🟡" if risk == "LOW" else "🟢" if risk == "SECURE" else "⚪"
                print(f"{indicator} {risk:<8}: {count:3} ({percentage:.1f}%) - {risk_descriptions[risk]}")

        # DEVICE SUMMARY TABLE
        print(f"\n{'📱 ALL DEVICES SUMMARY':^80}")
        print("-" * 80)
        print(f"{'INDEX':<6} {'HOSTNAME':<25} {'IP ADDRESS':<15} {'MODEL':<15} {'RISK':<8} {'TELNET':<6} {'LOGIN':<10}")
        print("-" * 80)
        
        # Sort by risk level (highest first) then by hostname
        risk_priority = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "SECURE": 1, "UNKNOWN": 0}
        sorted_results = sorted(self.results, key=lambda x: (risk_priority.get(x["risk_level"], 0), x["hostname"]), reverse=True)
        
        for device in sorted_results:
            index = device.get("index", "N/A")
            hostname = device["hostname"]
            if len(hostname) > 24:
                hostname = hostname[:21] + "..."
            ip = device["ip_address"]
            model = device.get("model", "Unknown")[:14]
            risk = device["risk_level"]
            telnet = device["telnet_allowed"]
            login = device["login_method"]
            
            # Add color indicators based on risk level
            risk_indicator = "🔴" if risk in ["CRITICAL", "HIGH"] else "🟠" if risk == "MEDIUM" else "🟡" if risk == "LOW" else "🟢" if risk == "SECURE" else "⚪"
            telnet_indicator = "❌" if telnet == "YES" else "✅" if telnet == "NO" else "?"
            
            print(f"{index:<6} {hostname:<25} {ip:<15} {model:<15} {risk_indicator} {risk:<7} {telnet_indicator} {telnet:<5} {login:<10}")

        # HIGH-RISK DEVICES SECTION
        high_risk = [r for r in self.results if r["risk_level"] in ["CRITICAL", "HIGH"]]
        if high_risk:
            print(f"\n{'⚠️  HIGH-RISK DEVICES':^80}")
            print("-" * 80)
            for device in high_risk:
                error_info = f" - ERROR: {device['error']}" if device['error'] else ""
                print(f"🔴 {device['hostname']} ({device['ip_address']})")
                print(f"   Risk Level: {device['risk_level']}")
                print(f"   Login Method: {device['login_method']}")
                print(f"   Telnet Enabled: {device['telnet_allowed']}")
                print(f"   Exec Timeout: {device['exec_timeout']}")
                if error_info:
                    print(f"   {error_info}")
                print()

        # CONNECTION FAILURES SECTION
        failed = [r for r in self.results if r["error"] is not None]
        if failed:
            print(f"\n{'❌ CONNECTION FAILURES':^80}")
            print("-" * 80)
            # Group by error type
            error_groups = {}
            for device in failed:
                error_text = device['error']
                error_type = "unknown"
                
                # Categorize errors
                for category, _ in error_categories.items():
                    if category in error_text.lower():
                        error_type = category
                        break
                if "authentication" in error_text.lower() or "password" in error_text.lower():
                    error_type = "authentication_failed"
                if "timed out" in error_text.lower() or "timeout" in error_text.lower():
                    error_type = "timeout"
                    
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(device)
            
            # Print errors by category
            for error_type, devices in error_groups.items():
                description = error_categories.get(error_type, "Uncategorized error")
                print(f"📌 {error_type.upper().replace('_', ' ')} ({len(devices)}) - {description}")
                for device in devices:
                    print(f"   • {device['hostname']} ({device['ip_address']}) - {device['error']}")
                print()

        # FAILURE CATEGORY REFERENCE
        print(f"\n{'📚 ERROR CATEGORY REFERENCE':^80}")
        print("-" * 80)
        for category, description in error_categories.items():
            print(f"• {category.upper().replace('_', ' ')}: {description}")
            
        # RISK LEVEL REFERENCE
        print(f"\n{'🔍 RISK LEVEL REFERENCE':^80}")
        print("-" * 80)
        for risk, description in risk_descriptions.items():
            indicator = "🔴" if risk in ["CRITICAL", "HIGH"] else "🟠" if risk == "MEDIUM" else "🟡" if risk == "LOW" else "🟢" if risk == "SECURE" else "⚪"
            print(f"{indicator} {risk}: {description}")
            
        print("\n" + "═" * 80)
        print(f"{'END OF REPORT':^80}")
        print("═" * 80)


def main():
    # Print header
    print("=" * 60)
    print("Cisco AUX Port Telnet Audit Script")
    print("Connects via Jump Host: 172.16.39.128")
    print("=" * 60)

    # Check for required tools
    if os.name == 'nt':  # Windows
        sshpass_check = os.system("where sshpass >nul 2>&1")
        if sshpass_check != 0:
            print("Warning: sshpass not found. You may need to install it or use alternative authentication.")
    else:  # Linux/Unix
        sshpass_check = os.system("which sshpass >/dev/null 2>&1")
        if sshpass_check != 0:
            print("Warning: sshpass not found. Installing...")
            os.system("sudo apt-get update && sudo apt-get install -y sshpass")

    try:
        auditor = JumpHostAuditor()

        # Load configuration
        auditor.load_environment()
        auditor.load_routers_from_csv()

        if not auditor.routers:
            logger.error("No routers loaded from CSV file")
            return

        # Run audit
        if auditor.run_audit():
            auditor.generate_reports()
            print(f"\n✅ Audit completed successfully!")
        else:
            print(f"\n❌ Audit failed - check logs for details")

    except KeyboardInterrupt:
        print("\n\n🛑 Audit interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Audit failed: {e}")


if __name__ == "__main__":
    main()