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
from datetime import datetime, timedelta
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
        
        # Timing variables
        self.start_time = None
        self.end_time = None
        self.pause_start_time = None
        self.total_pause_duration = timedelta(0)
        self.is_paused = False
        self.phase_times = {
            "connectivity": None,
            "authentication": None,
            "config_audit": None,
            "risk_assessment": None,
            "reporting": None
        }
        self.current_phases = {}

    # Timing Management Methods
    def start_timer(self):
        """Start the audit timer"""
        self.start_time = datetime.now()
        self.end_time = None
        self.total_pause_duration = timedelta(0)
        self.is_paused = False
        logger.info(f"Audit started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return self.start_time
    
    def pause_timer(self):
        """Pause the audit timer"""
        if not self.is_paused and self.start_time is not None:
            self.pause_start_time = datetime.now()
            self.is_paused = True
            logger.info(f"Audit paused at {self.pause_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return self.pause_start_time
        return None
    
    def resume_timer(self):
        """Resume the audit timer"""
        if self.is_paused and self.pause_start_time is not None:
            pause_end_time = datetime.now()
            pause_duration = pause_end_time - self.pause_start_time
            self.total_pause_duration += pause_duration
            self.is_paused = False
            logger.info(f"Audit resumed at {pause_end_time.strftime('%Y-%m-%d %H:%M:%S')} after {pause_duration.total_seconds():.2f} seconds")
            return pause_duration
        return None
    
    def stop_timer(self):
        """Stop the audit timer and calculate elapsed time"""
        if self.start_time is not None:
            if self.is_paused:
                self.resume_timer()
            self.end_time = datetime.now()
            elapsed_time = self.end_time - self.start_time - self.total_pause_duration
            logger.info(f"Audit completed at {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Total audit duration: {elapsed_time.total_seconds():.2f} seconds (excluding pauses)")
            return elapsed_time
        return None
    
    def format_elapsed_time(self, elapsed_time):
        """Format elapsed time into a readable string"""
        if elapsed_time is None:
            return "N/A"
        
        total_seconds = int(elapsed_time.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_timing_summary(self):
        """Get a summary of timing information"""
        if self.start_time is None:
            return "Audit has not started"
        
        current_time = datetime.now()
        if self.end_time is None:
            if self.is_paused:
                current_duration = self.pause_start_time - self.start_time - self.total_pause_duration
                status = "PAUSED"
            else:
                current_duration = current_time - self.start_time - self.total_pause_duration
                status = "RUNNING"
        else:
            current_duration = self.end_time - self.start_time - self.total_pause_duration
            status = "COMPLETED"
        
        return {
            "status": status,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "N/A",
            "elapsed_time": self.format_elapsed_time(current_duration),
            "total_pause_duration": self.format_elapsed_time(self.total_pause_duration),
            "phase_times": {phase: self.format_elapsed_time(time) for phase, time in self.phase_times.items() if time is not None}
        }
    
    def record_phase_time(self, phase, duration):
        """Record time for a specific audit phase"""
        if phase in self.phase_times:
            self.phase_times[phase] = duration
            logger.info(f"Phase '{phase}' completed in {self.format_elapsed_time(duration)}")
            
    def start_phase(self, phase_name):
        """Start timing for a specific audit phase"""
        if phase_name in self.phase_times:
            self.current_phases[phase_name] = datetime.now()
            logger.info(f"Starting phase: {phase_name} at {self.current_phases[phase_name].strftime('%Y-%m-%d %H:%M:%S')}")
            return self.current_phases[phase_name]
        return None
        
    def end_phase(self, phase_name):
        """End timing for a specific audit phase and record duration"""
        if phase_name in self.phase_times and phase_name in self.current_phases:
            end_time = datetime.now()
            duration = end_time - self.current_phases[phase_name]
            self.record_phase_time(phase_name, duration)
            logger.info(f"Completed phase: {phase_name} in {self.format_elapsed_time(duration)}")
            return duration
        return None
    
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
            
    def ping_device(self, host, jump_conn=None):
        """Test connectivity to a device with ping from jump host"""
        try:
            if jump_conn:
                # Execute ping through existing jump host connection
                cmd = f"ping -c 3 -W 2 {host}"
                output = jump_conn.send_command(cmd, delay_factor=1)
                success = "0% packet loss" in output or " 0% packet loss" in output
            else:
                # If no connection provided, establish a new one
                with ConnectHandler(**self.jump_host, timeout=10) as conn:
                    cmd = f"ping -c 3 -W 2 {host}"
                    output = conn.send_command(cmd, delay_factor=1)
                    success = "0% packet loss" in output or " 0% packet loss" in output
            
            if success:
                logger.info(f"✓ Ping to {host} successful")
                return True, output
            else:
                logger.warning(f"✗ Ping to {host} failed with packet loss")
                return False, output
        except Exception as e:
            logger.error(f"✗ Ping test to {host} failed with error: {e}")
            return False, str(e)
            
    def test_ssh_connectivity(self, host, username, password, jump_conn=None):
        """Test SSH connectivity to a device from jump host"""
        try:
            if jump_conn:
                # Try simple SSH command through jump host
                cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes {username}@{host} exit 2>&1"
                output = jump_conn.send_command(cmd, delay_factor=1)
            else:
                # If no connection provided, establish a new one
                with ConnectHandler(**self.jump_host, timeout=10) as conn:
                    cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes {username}@{host} exit 2>&1"
                    output = conn.send_command(cmd, delay_factor=1)
            
            # Check for SSH errors in output
            if "Connection refused" in output:
                logger.warning(f"✗ SSH to {host} failed: Connection refused")
                return False, "Connection refused"
            elif "Connection timed out" in output:
                logger.warning(f"✗ SSH to {host} failed: Connection timed out")
                return False, "Connection timed out"
            elif "Permission denied" in output:
                logger.warning(f"✗ SSH to {host} failed: Permission denied (authentication failed)")
                return False, "Authentication failed"
            elif "Host key verification failed" in output:
                logger.warning(f"✗ SSH to {host} failed: Host key verification failed")
                return False, "Host key verification failed"
            elif "No route to host" in output:
                logger.warning(f"✗ SSH to {host} failed: No route to host")
                return False, "No route to host"
            elif "Connection reset" in output:
                logger.warning(f"✗ SSH to {host} failed: Connection reset")
                return False, "Connection reset"
            elif "command not found" in output:
                logger.warning(f"✗ sshpass command not found on jump host")
                return False, "sshpass not available"
            elif "255" in output or "exit status 255" in output:
                logger.warning(f"✗ SSH to {host} failed with generic error")
                return False, "SSH error"
            else:
                logger.info(f"✓ SSH to {host} successful")
                return True, "SSH connectivity successful"
        except Exception as e:
            logger.error(f"✗ SSH test to {host} failed with error: {e}")
            return False, str(e)

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
            "connection_method": "jump_host",
            "model": model,
            "ping_status": "UNKNOWN",
            "ssh_status": "UNKNOWN",
            "auth_status": "UNKNOWN",
            "command_status": "UNKNOWN",
            "platform_info": "UNKNOWN"
        }

        try:
            # Start the connectivity phase
            self.start_phase("Connectivity")
            
            # First ping test from jump host
            print(f"{Fore.YELLOW}🔄 Testing ICMP connectivity to {router_ip}...{Style.RESET_ALL}")
            ping_success, ping_output = self.ping_device(router_ip)
            result["ping_status"] = "SUCCESS" if ping_success else "FAILED"
            if not ping_success:
                print(f"{Fore.RED}❌ Ping test failed: {router_ip}{Style.RESET_ALL}")
                result["error"] = f"Ping failed: {ping_output}"
                print(f"{Fore.YELLOW}⚠️ Continuing audit despite ping failure...{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ Ping test successful{Style.RESET_ALL}")
            
            # Test SSH connectivity
            print(f"{Fore.YELLOW}🔄 Testing SSH connectivity to {router_ip}...{Style.RESET_ALL}")
            ssh_success, ssh_message = self.test_ssh_connectivity(
                router_ip,
                router_config['username'],
                router_config['password']
            )
            result["ssh_status"] = "SUCCESS" if ssh_success else "FAILED"
            if not ssh_success:
                print(f"{Fore.RED}❌ SSH connectivity test failed: {ssh_message}{Style.RESET_ALL}")
                result["error"] = f"SSH failed: {ssh_message}"
                print(f"{Fore.YELLOW}⚠️ Continuing audit despite SSH connectivity failure...{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ SSH connectivity test successful{Style.RESET_ALL}")
                
            # Complete connectivity phase
            self.end_phase("Connectivity")
            
            # Connect to jump host
            print(f"{Fore.YELLOW}🔄 Connecting to jump host...{Style.RESET_ALL}")
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
                except Exception as ssh_err:
                    # Method 2: Manual SSH with expect-style interaction
                    logger.info(f"Trying manual SSH for {router_name}: {ssh_err}")
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
                # Start authentication phase
                self.start_phase("Authentication")
                
                # Check for authentication success
                try:
                    if '>' in output or '#' in output:
                        print(f"{Fore.GREEN}✅ Authentication successful{Style.RESET_ALL}")
                        result["auth_status"] = "SUCCESS"
                    else:
                        print(f"{Fore.RED}❌ Authentication failed - no router prompt detected{Style.RESET_ALL}")
                        result["auth_status"] = "FAILED"
                        result["error"] = "Authentication failed - no router prompt"
                        # Continue anyway
                        print(f"{Fore.YELLOW}⚠️ Continuing audit despite authentication issues...{Style.RESET_ALL}")
                except Exception as auth_err:
                    print(f"{Fore.RED}❌ Authentication check error: {auth_err}{Style.RESET_ALL}")
                    result["auth_status"] = "FAILED"
                    result["error"] = f"Authentication check error: {auth_err}"
                    print(f"{Fore.YELLOW}⚠️ Continuing audit despite authentication issues...{Style.RESET_ALL}")
                
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
                        if '#' in output:
                            print(f"{Fore.GREEN}✅ Enable mode activated{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Enable mode failed - incorrect secret{Style.RESET_ALL}")
                            result["error"] = "Enable mode failed - incorrect secret"
                    
                # End authentication phase
                self.end_phase("Authentication")
                
                # Start config audit phase
                self.start_phase("Config Audit")

                # Get and run show commands
                show_commands = [
                    "terminal length 0",
                    "show run | include aux",
                    "show run | include line aux",
                    "show run | begin line aux",
                    "show version | include IOS",
                    "show platform",         # Added platform info command
                    "show version"           # Full version info
                ]

                print(f"{Fore.CYAN}📋 Executing router commands...{Style.RESET_ALL}")
                command_outputs = {}
                command_success = True
                
                for cmd in show_commands:
                    print(f"{Fore.YELLOW}📤 Sending command: {cmd}{Style.RESET_ALL}")
                    jump_conn.write_channel(cmd + '\n')
                    time.sleep(2)  # Allow time for command execution
                    temp_output = jump_conn.read_channel()
                    
                    # Verify command response
                    if len(temp_output.strip()) > 5 and (cmd in temp_output or '#' in temp_output):
                        print(f"{Fore.GREEN}✅ Command executed successfully: {cmd}{Style.RESET_ALL}")
                        command_outputs[cmd] = temp_output
                        
                        # Capture platform info specifically
                        if cmd == "show platform":
                            result["platform_info"] = temp_output
                    else:
                        print(f"{Fore.RED}❌ Command may have failed: {cmd}{Style.RESET_ALL}")
                        command_success = False
                
                # Run our audit command
                audit_cmd = "show running-config | include telnet|aux|line"  # Show telnet and aux port config
                print(f"{Fore.YELLOW}📤 Sending audit command: {audit_cmd}{Style.RESET_ALL}")
                jump_conn.write_channel(audit_cmd + '\n')
                time.sleep(3)  # Give time for command to execute

                # Collect output
                time.sleep(2)
                output = jump_conn.read_channel()
                if len(output.strip()) > 10:
                    print(f"{Fore.GREEN}📥 Received configuration data: {len(output)} chars{Style.RESET_ALL}")
                    command_outputs[audit_cmd] = output
                    result["command_status"] = "SUCCESS" if command_success else "PARTIAL"
                else:
                    print(f"{Fore.RED}❌ Audit command failed or returned minimal data{Style.RESET_ALL}")
                    result["command_status"] = "FAILED"
                    result["error"] = "Audit command failed to return sufficient data"
                
                # End config audit phase
                self.end_phase("Config Audit")
                
                # Start risk assessment phase
                self.start_phase("Risk Assessment")
                
                # Exit the router
                print(f"{Fore.YELLOW}🚪 Exiting router session...{Style.RESET_ALL}")
                jump_conn.write_channel("exit\n")
                time.sleep(1)

                # Parse the router output
                if output and len(output.strip()) > 10:  # Ensure we got substantial output
                    print(f"{Fore.CYAN}🔍 Analyzing router configuration...{Style.RESET_ALL}")
                    # Pass the existing result to preserve the auth_status and other fields
                    result = self.parse_router_output(output, router_name, router_ip, result)
                    
                    # These are now preserved inside parse_router_output, but we'll set them again to be safe
                    result["ping_status"] = "SUCCESS" if ping_success else "FAILED"
                    result["ssh_status"] = "SUCCESS" if ssh_success else "FAILED"
                    result["command_status"] = "SUCCESS" if command_success else "PARTIAL"
                    result["platform_info"] = command_outputs.get("show platform", "Not available")
                    
                    # End risk assessment phase
                    self.end_phase("Risk Assessment")
                    
                    # Start reporting phase
                    self.start_phase("Reporting")
                    
                    # Show result summary for this router
                    risk_color = Fore.RED if result["risk_level"] in ["CRITICAL", "HIGH"] else \
                                 Fore.YELLOW if result["risk_level"] == "MEDIUM" else \
                                 Fore.GREEN if result["risk_level"] in ["LOW", "SECURE"] else Fore.WHITE
                    
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    print(f"{risk_color}🏁 AUDIT COMPLETE: {router_name} ({router_ip}){Style.RESET_ALL}")
                    print(f"{risk_color}⚠️ Risk Level: {result['risk_level']}{Style.RESET_ALL}")
                    print(f"{risk_color}🔐 Telnet Allowed: {result['telnet_allowed']}{Style.RESET_ALL}")
                    print(f"{risk_color}🔑 Login Method: {result['login_method']}{Style.RESET_ALL}")
                    
                    # Show connectivity and execution status
                    ping_color = Fore.GREEN if ping_success else Fore.RED
                    ssh_color = Fore.GREEN if ssh_success else Fore.RED
                    auth_color = Fore.GREEN if result.get("auth_status", "UNKNOWN") == "SUCCESS" else Fore.RED
                    cmd_color = Fore.GREEN if command_success else Fore.YELLOW
                    
                    print(f"{ping_color}🌐 Ping Status: {result.get('ping_status', 'UNKNOWN')}{Style.RESET_ALL}")
                    print(f"{ssh_color}🔌 SSH Status: {result.get('ssh_status', 'UNKNOWN')}{Style.RESET_ALL}")
                    print(f"{auth_color}🔐 Auth Status: {result.get('auth_status', 'UNKNOWN')}{Style.RESET_ALL}")
                    print(f"{cmd_color}🖥️ Command Status: {result.get('command_status', 'UNKNOWN')}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}📱 Model/Platform: {result.get('model', 'Unknown')}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    
                    # End reporting phase
                    self.end_phase("Reporting")
                    
                    return result
                else:
                    raise Exception("No meaningful output received from router")

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"✗ {router_name} - {error_msg}")

        return result

    def parse_router_output(self, output, fallback_hostname, router_ip, result=None):
        """Parse router output and assess security risk"""
        lines = output.strip().split('\n')

        # If result was provided, use it, otherwise create a new one
        if result is None:
            result = {
                "hostname": fallback_hostname,
                "ip_address": router_ip,
                "line": "unknown",
                "telnet_allowed": "UNKNOWN",
                "login_method": "UNKNOWN",
                "exec_timeout": "UNKNOWN",
                "risk_level": "UNKNOWN",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": None,
                "connection_method": "jump_host",
                "ping_status": "UNKNOWN",
                "ssh_status": "UNKNOWN",
                "auth_status": "UNKNOWN",
                "command_status": "UNKNOWN",
                "platform_info": "UNKNOWN"
            }

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
        """Run audit across all routers via jump host using the 5-phase approach"""
        # Start the timer for the entire audit
        self.start_timer()
        
        # Display audit initiation header
        total_routers = len(self.routers)
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 STARTING FULL AUDIT PROCESS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📡 Jump Host: {self.jump_host['host']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🖥️  Total Routers: {total_routers}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⚙️  Concurrent Workers: {max_workers}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🕒 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        logger.info(f"Starting audit of {total_routers} routers with {max_workers} workers...")
        
        # Phase 1: Connectivity
        phase1_start = datetime.now()
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔗 PHASE 1: CONNECTIVITY TESTING{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Test jump host connection
        connectivity_success = self.test_jump_host_connection()
        if not connectivity_success:
            logger.error("Jump host connection failed, cannot continue")
            self.record_phase_time("connectivity", datetime.now() - phase1_start)
            self.stop_timer()
            return False
            
        print(f"{Fore.GREEN}✅ Jump host connectivity test passed{Style.RESET_ALL}")
        self.record_phase_time("connectivity", datetime.now() - phase1_start)

        # Phase 2: Authentication
        phase2_start = datetime.now()
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔑 PHASE 2: AUTHENTICATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Verify credentials are loaded
        auth_success = True
        if not self.jump_host.get('password'):
            print(f"{Fore.RED}❌ Jump host credentials not configured{Style.RESET_ALL}")
            auth_success = False
        else:
            print(f"{Fore.GREEN}✅ Jump host credentials verified{Style.RESET_ALL}")
            
        self.record_phase_time("authentication", datetime.now() - phase2_start)
        if not auth_success:
            self.stop_timer()
            return False
            
        # Phase 3: Configuration Audit
        phase3_start = datetime.now()
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📝 PHASE 3: CONFIGURATION AUDIT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
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
                    
        self.record_phase_time("config_audit", datetime.now() - phase3_start)

        # Phase 4: Risk Assessment
        phase4_start = datetime.now()
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🛡 PHASE 4: RISK ASSESSMENT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "SECURE": 0, "UNKNOWN": 0}
        for result in self.results:
            risk_level = result["risk_level"]
            risk_counts[risk_level] += 1
            
        total_assessed = len(self.results)
        high_risk_percent = ((risk_counts["CRITICAL"] + risk_counts["HIGH"]) / total_assessed * 100) if total_assessed > 0 else 0
        medium_risk_percent = (risk_counts["MEDIUM"] / total_assessed * 100) if total_assessed > 0 else 0
        low_risk_percent = ((risk_counts["LOW"] + risk_counts["SECURE"]) / total_assessed * 100) if total_assessed > 0 else 0
        unknown_risk_percent = (risk_counts["UNKNOWN"] / total_assessed * 100) if total_assessed > 0 else 0
        
        print(f"{Fore.YELLOW}Risk Assessment Summary:{Style.RESET_ALL}")
        print(f"• High Risk (CRITICAL/HIGH): {risk_counts['CRITICAL'] + risk_counts['HIGH']} devices ({high_risk_percent:.1f}%)")
        print(f"• Medium Risk: {risk_counts['MEDIUM']} devices ({medium_risk_percent:.1f}%)")
        print(f"• Low Risk (LOW/SECURE): {risk_counts['LOW'] + risk_counts['SECURE']} devices ({low_risk_percent:.1f}%)")
        print(f"• Unknown Risk: {risk_counts['UNKNOWN']} devices ({unknown_risk_percent:.1f}%)")
        
        self.record_phase_time("risk_assessment", datetime.now() - phase4_start)
        
        # Phase 5: Reporting
        phase5_start = datetime.now()
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 PHASE 5: REPORTING{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Reporting will be handled by generate_reports and print_summary
        # which are called after this method
        
        self.record_phase_time("reporting", datetime.now() - phase5_start)
        
        # Stop the timer for the entire audit
        elapsed_time = self.stop_timer()
        
        print(f"\n{Fore.GREEN}✓ Audit completed successfully in {self.format_elapsed_time(elapsed_time)}{Style.RESET_ALL}")
        return True

    def generate_reports(self):
        """Generate CSV report and summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"aux_telnet_audit_{timestamp}.csv"
        
        try:
            with open(csv_filename, 'w', newline='') as f:
                # Add timing information to the field names
                fieldnames = ['hostname', 'ip_address', 'line', 'model', 'telnet_allowed', 'login_method',
                              'exec_timeout', 'risk_level', 'timestamp', 'error', 'model',
                              'ping_status', 'ssh_status', 'auth_status', 'command_status', 'platform_info',
                              'audit_start_time', 'audit_end_time', 'audit_duration']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Get timing information for the report
                timing_info = self.get_timing_summary()
                start_time = self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else "N/A"
                end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "N/A"
                
                for result in self.results:
                    writer.writerow({
                        'hostname': result['hostname'],
                        'ip_address': result['ip_address'],
                        'line': result.get('line', ''),
                        'telnet_allowed': result['telnet_allowed'],
                        'login_method': result['login_method'],
                        'exec_timeout': result['exec_timeout'],
                        'risk_level': result['risk_level'],
                        'timestamp': result.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        'error': result.get('error', ''),
                        'model': result.get('model', 'Unknown'),
                        'ping_status': result.get('ping_status', 'UNKNOWN'),
                        'ssh_status': result.get('ssh_status', 'UNKNOWN'),
                        'auth_status': result.get('auth_status', 'UNKNOWN'),
                        'command_status': result.get('command_status', 'UNKNOWN'),
                        'platform_info': result.get('platform_info', 'UNKNOWN'),
                        'audit_start_time': start_time,
                        'audit_end_time': end_time,
                        'audit_duration': timing_info.get('elapsed_time', 'N/A') if isinstance(timing_info, dict) else 'N/A'
                    })
                    
            logger.info(f"Detailed report saved to: {csv_filename}")
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            
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
        
        # TIMING INFORMATION
        timing_summary = self.get_timing_summary()
        if isinstance(timing_summary, dict):
            print(f"\n{'🕐 AUDIT TIMING INFORMATION':^80}")
            print("-" * 80)
            print(f"🕒 Start Time:       {timing_summary.get('start_time', 'N/A')}")
            print(f"🕓 End Time:         {timing_summary.get('end_time', 'N/A')}")
            print(f"⏱ Total Duration:    {timing_summary.get('elapsed_time', 'N/A')}")
            print(f"⏸ Pause Duration:    {timing_summary.get('total_pause_duration', 'N/A')}")
            print(f"💡 Status:           {timing_summary.get('status', 'N/A')}")
            
            # Phase timing information
            phase_times = timing_summary.get('phase_times', {})
            if phase_times:
                print("\nPhase Durations:")
                for phase, duration in phase_times.items():
                    if phase == "connectivity":
                        icon = "🔗"  # Chain link
                    elif phase == "authentication":
                        icon = "🔑"  # Key
                    elif phase == "config_audit":
                        icon = "📝"  # Clipboard
                    elif phase == "risk_assessment":
                        icon = "🛡"  # Shield
                    elif phase == "reporting":
                        icon = "📊"  # Chart
                    else:
                        icon = "•"  # Bullet
                    print(f"  {icon} {phase.capitalize()}: {duration}")
        
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
        failed = [r for r in self.results if r.get("error") is not None]
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
    print("5-Phase Audit with Timing - Press CTRL+C to pause/stop")
    print("=" * 60)
    
    # Initialize auditor at the top level so it's accessible in all blocks
    auditor = None

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
        
        # Display start prompt and current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nCurrent Date/Time: {current_time}")
        input("Press Enter to start the audit...")
        
        # Load configuration
        auditor.load_environment()
        auditor.load_routers_from_csv()

        if not auditor.routers:
            logger.error("No routers loaded from CSV file")
            return

        # Run audit with timing
        if auditor.run_audit():
            # Generate reports (phase 5 completion)
            csv_report = auditor.generate_reports()
            auditor.print_summary()
            print(f"\n✅ Audit completed successfully!")
            print(f"Report saved to: {csv_report}")
        else:
            print(f"\n❌ Audit failed - check logs for details")

    except KeyboardInterrupt:
        # Handle keyboard interrupt for pause/resume functionality
        if hasattr(auditor, 'is_paused') and auditor.is_paused:
            print("\n\n▶ Resuming audit...")
            auditor.resume_timer()
            # Continue with audit where we left off
            if auditor.run_audit():
                csv_report = auditor.generate_reports()
                auditor.print_summary()
                print(f"\n✅ Audit completed successfully!")
                print(f"Report saved to: {csv_report}")
        else:
            print("\n\n🛑 Audit paused by user")
            auditor.pause_timer()
            resume = input("Press Enter to resume or 'q' to quit: ")
            if resume.lower() != 'q':
                print("\n▶ Resuming audit...")
                auditor.resume_timer()
                # Continue with audit
                if auditor.run_audit():
                    csv_report = auditor.generate_reports()
                    auditor.print_summary()
                    print(f"\n✅ Audit completed successfully!")
                    print(f"Report saved to: {csv_report}")
            else:
                print("\n🛑 Audit terminated by user")
                elapsed = auditor.stop_timer()
                print(f"Partial audit duration: {auditor.format_elapsed_time(elapsed)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Audit failed: {e}")




if __name__ == "__main__":
    main()