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


class CredentialManager:
    """
    Handles encryption and decryption of sensitive credentials
    Uses Fernet symmetric encryption with a key derived from a master password
    """
    def __init__(self, master_password=None):
        self.salt = None
        self.key = None
        self.cipher_suite = None
        self.salt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.salt')
        
        # Initialize with master password if provided
        if master_password:
            self.initialize(master_password)
        
    def initialize(self, master_password):
        """
        Initialize the encryption with a master password
        Will create a new salt if none exists or load existing one
        """
        # Create or load salt
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                self.salt = f.read()
        else:
            self.salt = secrets.token_bytes(16)  # Generate new salt
            with open(self.salt_file, 'wb') as f:
                f.write(self.salt)
        
        # Derive key from password and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Create the key and cipher suite
        self.key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, plaintext):
        """
        Encrypt a string and return a base64-encoded encrypted value
        """
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized. Call initialize() first.")
        
        if not plaintext:
            return None
            
        encrypted = self.cipher_suite.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text):
        """
        Decrypt a base64-encoded encrypted value and return the plaintext
        """
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized. Call initialize() first.")
        
        if not encrypted_text:
            return None
            
        try:
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return None
    
    def hash_password(self, password, salt=None):
        """
        Generate a secure hash of a password with an optional salt
        Returns (hash, salt) tuple
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        # Create a hash with the password and salt
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode(), 
            salt.encode(), 
            100000
        )
        password_hash = hash_obj.hex()
        
        return password_hash, salt
    
    def verify_password(self, password, stored_hash, salt):
        """
        Verify a password against a stored hash and salt
        """
        hash_to_check, _ = self.hash_password(password, salt)
        return hash_to_check == stored_hash


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
        
        # Setup credential manager
        self.cred_manager = CredentialManager()
        self.master_password = None
        
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
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        
        # Ask for master password for credential encryption/decryption
        # self.master_password = getpass.getpass(f"Enter master password for credential encryption: ")
        self.master_password = "temp_master_password_for_testing" # Temporary for testing
        logger.info("Using temporary master password for testing.")
        self.cred_manager.initialize(self.master_password)
        
        if os.path.exists(env_file):
            # Load existing .env file
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'JUMP_HOST':
                            self.jump_host['host'] = value
                        elif key == 'JUMP_USERNAME':
                            self.jump_host['username'] = value
                        elif key == 'JUMP_HOST_PASSWORD':
                            # Decrypt password from stored encrypted value
                            try:
                                decrypted_pw = self.cred_manager.decrypt(value)
                                if decrypted_pw:
                                    self.jump_host['password'] = decrypted_pw
                                else:
                                    logger.warning("Could not decrypt jump host password")
                            except Exception as e:
                                logger.error(f"Password decryption error: {e}")
            
            logger.info(f"Loaded environment from .env file")
        else:
            # Create new .env file
            print(f"\n{Fore.YELLOW}⚠️ No .env file found. Creating a new one.{Style.RESET_ALL}")
            
            # Get jump host details from user
            # jump_host = input(f"Enter jump host IP [{self.jump_host['host']}]: ") or self.jump_host['host']
            # jump_username = input(f"Enter jump host username [{self.jump_host['username']}]: ") or self.jump_host['username']
            # jump_password = getpass.getpass(f"Enter jump host password: ")
            jump_password = "temp_jump_password_for_testing" # Temporary for testing
            logger.info(f"Using temporary jump host IP: {self.jump_host['host']}, User: {self.jump_host['username']}")
            logger.info("Using temporary jump host password for testing as .env was not found.")
            
            # Update jump host config
            # self.jump_host['host'] = jump_host # Defaults are used
            # self.jump_host['username'] = jump_username # Defaults are used
            self.jump_host['password'] = jump_password
            
            # Encrypt sensitive information
            # --- TEMPORARILY COMMENTED OUT FOR TESTING ---
            # encrypted_password = self.cred_manager.encrypt(jump_password)
            # 
            # # Write to .env file
            # with open(env_file, 'w') as f:
            #     f.write(f"JUMP_HOST={self.jump_host['host']}\n") # Use self.jump_host['host'] as jump_host variable is commented
            #     f.write(f"JUMP_USERNAME={self.jump_host['username']}\n") # Use self.jump_host['username'] as jump_username variable is commented
            #     f.write(f"JUMP_HOST_PASSWORD={encrypted_password}\n")
            # 
            # os.chmod(env_file, 0o600)  # Secure file permissions
            # logger.info(f"Created new .env file with jump host configuration")
            # --- END OF TEMPORARILY COMMENTED OUT SECTION ---
            logger.info("Skipped writing new .env file during temporary testing setup.")

    def load_routers_from_csv(self, csv_file="routers01.csv"):
        """Load router configurations from CSV file"""
        device_type = "cisco_ios"
        self.routers = []
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if we have required fields
                    if 'hostname' in row and 'ip_address' in row:
                        # Check if passwords are encrypted
                        password = row.get('password', 'cisco')
                        secret = row.get('secret', 'cisco')
                        
                        # If passwords start with 'ENC:', they are encrypted and need decryption
                        if password.startswith('ENC:'):
                            try:
                                password = self.cred_manager.decrypt(password[4:]) or password
                            except Exception as e:
                                logger.error(f"Error decrypting password for {row['hostname']}: {e}")
                        
                        if secret.startswith('ENC:'):
                            try:
                                secret = self.cred_manager.decrypt(secret[4:]) or secret
                            except Exception as e:
                                logger.error(f"Error decrypting secret for {row['hostname']}: {e}")
                        
                        # Create router config dict
                        router_config = {
                            'hostname': row['hostname'],
                            'host': row['ip_address'],
                            'username': row.get('username', 'admin'),
                            'password': password,
                            'secret': secret,
                            'device_type': device_type,
                            'model': row.get('model', 'Unknown')
                        }
                        
                        self.routers.append(router_config)
                        
            logger.info(f"Loaded {len(self.routers)} routers from {csv_file} with device type: {device_type}")
            return self.routers
        except FileNotFoundError:
            logger.error(f"CSV file {csv_file} not found")
            return []
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return []
            
    def save_encrypted_credentials(self, csv_file="routers01.csv", output_file="routers_encrypted.csv"):
        """Save router configurations with encrypted credentials"""
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
                
            logger.info(f"Saved encrypted credentials to {output_file}")
            print(f"{Fore.GREEN}✅ Saved encrypted credentials to {output_file}{Style.RESET_ALL}")
            return True
        except Exception as e:
            logger.error(f"Error saving encrypted credentials: {e}")
            print(f"{Fore.RED}❌ Error saving encrypted credentials: {e}{Style.RESET_ALL}")
            return False

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
            "risk_level": "UNKNOWN",
            "error": None
        }
        
        # Return the result dictionary for this router
        return result

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

        # Connectivity and execution status counts
        ping_status = {"SUCCESS": 0, "FAILED": 0, "UNKNOWN": 0}
        ssh_status = {"SUCCESS": 0, "FAILED": 0, "UNKNOWN": 0}
        auth_status = {"SUCCESS": 0, "FAILED": 0, "UNKNOWN": 0}
        command_status = {"SUCCESS": 0, "PARTIAL": 0, "FAILED": 0, "UNKNOWN": 0}
        privilege_levels = {"PRIVILEGED": 0, "USER": 0, "UNKNOWN": 0}

        # Count common authentication and command execution failures
        auth_failure_reasons = {}
        command_failure_reasons = {}

        for r in self.results:
            ping_status[r.get("ping_status", "UNKNOWN")] += 1
            ssh_status[r.get("ssh_status", "UNKNOWN")] += 1
            auth_status[r.get("auth_status", "UNKNOWN")] += 1
            command_status[r.get("command_status", "UNKNOWN")] += 1
            privilege_levels[r.get("privilege_level", "UNKNOWN")] += 1

            # Collect authentication failure reasons
            if r.get("auth_status") == "FAILED" and r.get("auth_error_details"):
                reason = r.get("auth_error_details")
                # Simplify the reason to group similar errors
                for key in ["password", "authentication", "timed out", "refused", "no route", "permission"]:
                    if key in reason.lower():
                        reason = key
                        break
                if reason not in auth_failure_reasons:
                    auth_failure_reasons[reason] = 0
                auth_failure_reasons[reason] += 1

            # Collect command execution failure reasons
            if r.get("command_status") in ["FAILED", "PARTIAL"] and r.get("command_failures"):
                for cmd in r.get("command_failures", []):
                    if cmd not in command_failure_reasons:
                        command_failure_reasons[cmd] = 0
                    command_failure_reasons[cmd] += 1

        # HEADER
        print("\n" + "═" * 80)
        print(f"{'CISCO ROUTER SECURITY AUDIT REPORT':^80}")
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
                print(f"{indicator} {risk:<8}: {count:3} ({percentage:.1f}%) - {self.risk_descriptions[risk]}")

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
                for category, _ in self.error_categories.items():
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
                description = self.error_categories.get(error_type, "Uncategorized error")
                print(f"📌 {error_type.upper().replace('_', ' ')} ({len(devices)}) - {description}")
                for device in devices:
                    print(f"   • {device['hostname']} ({device['ip_address']}) - {device['error']}")
                print()

        # AUTHENTICATION SUMMARY
        print(f"\n{Fore.CYAN}🗝️ AUTHENTICATION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Authentication Success: {auth_status['SUCCESS']}/{len(self.results)} ({auth_status['SUCCESS']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Authentication Failed: {auth_status['FAILED']}/{len(self.results)} ({auth_status['FAILED']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ Authentication Unknown: {auth_status['UNKNOWN']}/{len(self.results)} ({auth_status['UNKNOWN']/len(self.results)*100:.1f}%){Style.RESET_ALL}")

        # Show authentication failure reasons if any exist
        if auth_failure_reasons:
            print(f"\n{Fore.CYAN}🔍 AUTHENTICATION FAILURE REASONS{Style.RESET_ALL}")
            for reason, count in sorted(auth_failure_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"{Fore.RED}❌ {reason}: {count} devices{Style.RESET_ALL}")

        # COMMAND EXECUTION SUMMARY
        print(f"\n{Fore.CYAN}⌨️ COMMAND EXECUTION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Full Success: {command_status['SUCCESS']}/{len(self.results)} ({command_status['SUCCESS']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ Partial Success: {command_status['PARTIAL']}/{len(self.results)} ({command_status['PARTIAL']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Command Failed: {command_status['FAILED']}/{len(self.results)} ({command_status['FAILED']/len(self.results)*100:.1f}%){Style.RESET_ALL}")

        # Show command execution failure reasons if any exist
        if command_failure_reasons:
            print(f"\n{Fore.CYAN}🔍 COMMANDS THAT FAILED MOST FREQUENTLY{Style.RESET_ALL}")
            for cmd, count in sorted(command_failure_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:  # Top 5 failing commands
                print(f"{Fore.RED}❌ '{cmd}': failed on {count} devices{Style.RESET_ALL}")

        # PRIVILEGE LEVEL SUMMARY
        print(f"\n{Fore.CYAN}🗝️ PRIVILEGE LEVEL SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Privileged (Enable) Access: {privilege_levels['PRIVILEGED']}/{len(self.results)} ({privilege_levels['PRIVILEGED']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️ User-Level Access Only: {privilege_levels['USER']}/{len(self.results)} ({privilege_levels['USER']/len(self.results)*100:.1f}%){Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Unknown Access Level: {privilege_levels['UNKNOWN']}/{len(self.results)} ({privilege_levels['UNKNOWN']/len(self.results)*100:.1f}%){Style.RESET_ALL}")

        # FAILURE CATEGORY REFERENCE
        print(f"\n{Fore.CYAN}📚 ERROR CATEGORY REFERENCE{Style.RESET_ALL}")
        print("-" * 80)
        for category, description in self.error_categories.items():
            print(f"• {category.upper().replace('_', ' ')}: {description}")

        # RISK LEVEL REFERENCE
        print(f"\n{Fore.CYAN}🔍 RISK LEVEL REFERENCE{Style.RESET_ALL}")
        print("-" * 80)
        for risk, description in self.risk_descriptions.items():
            indicator = "🔴" if risk in ["CRITICAL", "HIGH"] else "🟠" if risk == "MEDIUM" else "🟡" if risk == "LOW" else "🟢" if risk == "SECURE" else "⚪"
            print(f"{indicator} {risk}: {description}")

        # AUTHENTICATION STATUS REFERENCE
        print(f"\n{Fore.CYAN}🗝️ AUTHENTICATION STATUS REFERENCE{Style.RESET_ALL}")
        print("-" * 80)
        for status, description in self.auth_status_descriptions.items():
            indicator = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "⚠️"
            print(f"{indicator} {status}: {description}")

        # COMMAND EXECUTION STATUS REFERENCE
        print(f"\n{Fore.CYAN}⌨️ COMMAND EXECUTION STATUS REFERENCE{Style.RESET_ALL}")
        print("-" * 80)
        for status, description in self.command_status_descriptions.items():
            indicator = "✅" if status == "SUCCESS" else "⚠️" if status == "PARTIAL" else "❌" if status == "FAILED" else "⚠️"
            print(f"{indicator} {status}: {description}")

        print("\n" + "═" * 80)
        print(f"{'END OF REPORT':^80}")
        print("═" * 80)

    def risk_descriptions(self):
        return {
            "CRITICAL": "Telnet enabled with no authentication",
            "HIGH": "Telnet enabled with weak authentication (line password)",
            "MEDIUM": "Telnet enabled with username/password authentication",
            "LOW": "Telnet disabled or secured",
            "SECURE": "All vulnerable services disabled",
            "UNKNOWN": "Risk could not be determined"
        }

    def auth_status_descriptions(self):
        return {
            "SUCCESS": "Authentication completed successfully",
            "FAILED": "Authentication failed - incorrect credentials or insufficient privileges",
            "UNKNOWN": "Authentication status could not be determined"
        }
    # Print header
    print("=" * 60)
    print("Cisco AUX Port Telnet Audit Script")
    print("5-Phase Audit with Timing - Press CTRL+C to pause/stop")
    print("Credential Protection: Passwords are encrypted and salted")
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
        # input("Press Enter to start the audit...") # Commented out for non-interactive testing
        logger.info("Audit script started non-interactively.") # Added log for clarity
        
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
        if e is None:
            logger.error("Unexpected error: Exception object was None.")
            print("\n❌ Audit failed: An unspecified error occurred (Exception object was None).")
        else:
            logger.error(f"Unexpected error of type {type(e).__name__}: {str(e)}")
            print(f"\n❌ Audit failed: {type(e).__name__} - {str(e)}")

    # --- Add logic to dump last lines of audit.log before exiting --- 
    try:
        audit_log_filepath = '/root/za-con/audit.log'
        diag_dump_filepath = '/root/za-con/last_audit_lines.txt'
        num_lines_to_dump = 20

        if os.path.exists(audit_log_filepath):
            with open(audit_log_filepath, 'r') as f_audit_log:
                all_lines = f_audit_log.readlines()
            
            with open(diag_dump_filepath, 'w') as f_diag_dump:
                f_diag_dump.write(f"--- Last {num_lines_to_dump} lines from {audit_log_filepath} ---\n")
                for line in all_lines[-num_lines_to_dump:]:
                    f_diag_dump.write(line)
                f_diag_dump.write("--- End of dump ---\n")
            # logger.info(f"Dumped last {num_lines_to_dump} lines of audit log to {diag_dump_filepath}") # Might not be seen
            print(f"[INFO] Dumped last {num_lines_to_dump} lines of audit log to {diag_dump_filepath}") # Try printing to console
        else:
            with open(diag_dump_filepath, 'w') as f_diag_dump:
                f_diag_dump.write(f"{audit_log_filepath} not found.\n")
            # logger.warning(f"{audit_log_filepath} not found. Cannot dump last lines.")
            print(f"[WARN] {audit_log_filepath} not found. Cannot dump last lines to {diag_dump_filepath}")

    except Exception as dump_exc:
        # logger.error(f"Error dumping last audit log lines: {dump_exc}")
        print(f"[ERROR] Error dumping last audit log lines to {diag_dump_filepath}: {dump_exc}")
    # --- End of dump logic ---

if __name__ == "__main__":
    main()