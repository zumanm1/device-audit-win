#!/usr/bin/env python3
"""
Network Audit Tool Core Module (v3.11)
Central module that provides common functionality and utilities
for all network audit components.

This module handles:
- Common configuration and settings
- Shared utilities and helper functions
- Logging infrastructure
- Database connections
- Secure credential management

Cross-platform compatible with Windows and Ubuntu.
"""

import os
import sys
import json
import logging
import datetime
import uuid
import csv
import base64
import getpass
import platform
from pathlib import Path  # Use pathlib for cross-platform path handling

# Import colorama for cross-platform colored terminal output
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    colorama_available = True
except ImportError:
    # Create mock Fore and Style if colorama not available
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = MockColor()
    colorama_available = False

# Import cryptography libraries for secure credential management
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    cryptography_available = True
except ImportError:
    cryptography_available = False
    print(f"{Fore.YELLOW}Warning: cryptography package not available. Secure credential storage disabled.{Style.RESET_ALL}")

# Global constants
VERSION = "3.11.0"
DEFAULT_LOG_DIR = "logs"
DEFAULT_REPORT_DIR = "reports"
DEFAULT_CONFIG_DIR = "config"
DEFAULT_DATA_DIR = "data"
DEFAULT_DB_NAME = "audit_results.sqlite"

# Cross-platform paths (automatically handles different OS path separators)
def get_app_dir():
    """Get the application directory using pathlib for cross-platform compatibility"""
    return Path(__file__).parent.absolute()

# Ensure all required directories exist
def ensure_directories():
    """Create required directories if they don't exist using pathlib for cross-platform compatibility"""
    base_dir = get_app_dir()
    created_dirs = []
    
    for directory in [DEFAULT_LOG_DIR, DEFAULT_REPORT_DIR, DEFAULT_CONFIG_DIR, DEFAULT_DATA_DIR]:
        directory_path = base_dir / directory
        if not directory_path.exists():
            try:
                directory_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(directory)
                print(f"Created {directory} directory at: {directory_path}")
            except Exception as e:
                print(f"{Fore.RED}Error creating {directory} directory: {e}{Style.RESET_ALL}")
                return False
    
    if created_dirs:
        print(f"{Fore.GREEN}✓ All required directories created successfully{Style.RESET_ALL}")
    return True
    return True

# Custom colored formatter for console output
class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console logging"""
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

# Set up logging
def setup_logging(log_name=None, log_level=logging.INFO):
    """Configure logging with file and console handlers"""
    # Create logger
    logger = logging.getLogger("network_audit")
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Generate log filename with timestamp if not provided
    if not log_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_name = f"network_audit_{timestamp}.log"
    
    # Full path to log file
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_LOG_DIR, log_name)
    
    try:
        # Test if we can write to the log file
        with open(log_file, 'w') as f:
            f.write(f"Log initialized at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Add colored console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)  # Only INFO and above to console
        console.setFormatter(ColoredFormatter())
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console)
        
        logger.info(f"Logging configured. Log file: {log_file}")
        return logger, log_file
    
    except Exception as e:
        print(f"Error setting up logging: {e}")
        return None, None

class CredentialManager:
    """
    Handles encryption and decryption of sensitive credentials
    Uses Fernet symmetric encryption with a key derived from a master password
    """
    
    def __init__(self, master_password=None):
        """Initialize credential manager with optional master password"""
        if not cryptography_available:
            raise ImportError("Cryptography package not available. Cannot create CredentialManager.")
        
        self.salt = None
        self.key = None
        self.cipher_suite = None
        self.salt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      DEFAULT_CONFIG_DIR, '.salt')
        
        # Initialize with master password if provided
        if master_password:
            self.initialize(master_password)
    
    def initialize(self, master_password):
        """
        Initialize the encryption with a master password
        Will create a new salt if none exists or load existing one
        """
        # Create the config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.salt_file), exist_ok=True)
        
        if os.path.exists(self.salt_file):
            # Load existing salt
            with open(self.salt_file, 'rb') as f:
                self.salt = f.read()
        else:
            # Generate new salt
            import os as stdlib_os  # Used just for urandom
            self.salt = stdlib_os.urandom(16)
            # Save salt to file with secure permissions
            with open(self.salt_file, 'wb') as f:
                f.write(self.salt)
            try:
                # Make file read/write only by owner (POSIX only)
                os.chmod(self.salt_file, 0o600)
            except Exception:
                # On Windows or if chmod fails, at least warn the user
                print(f"{Fore.YELLOW}Warning: Could not set secure permissions on salt file.{Style.RESET_ALL}")
        
        # Generate key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Derive the key from the password
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, plaintext):
        """
        Encrypt a string and return a base64-encoded encrypted value
        """
        if not self.cipher_suite:
            raise ValueError("Credential manager not initialized with a master password")
            
        if not plaintext:
            return ""
            
        return base64.b64encode(
            self.cipher_suite.encrypt(plaintext.encode())
        ).decode('utf-8')
    
    def decrypt(self, encrypted_text):
        """
        Decrypt a base64-encoded encrypted value and return the plaintext
        """
        if not self.cipher_suite:
            raise ValueError("Credential manager not initialized with a master password")
            
        if not encrypted_text:
            return ""
            
        try:
            return self.cipher_suite.decrypt(
                base64.b64decode(encrypted_text)
            ).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt: {str(e)}")

def prompt_for_master_password(confirm=True):
    """
    Prompt user for a secure master password with confirmation
    Returns the entered password
    """
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔐 SECURITY SETUP - MASTER PASSWORD REQUIRED 🔐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}This password will be used to encrypt all sensitive information.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}It will not be stored anywhere - please remember it!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    while True:
        password = getpass.getpass("Enter your master password: ")
        
        # Basic password strength check
        if len(password) < 8:
            print(f"{Fore.YELLOW}Password is too short (minimum 8 characters).{Style.RESET_ALL}")
            continue
            
        if confirm:
            password_confirm = getpass.getpass("Confirm your master password: ")
            if password != password_confirm:
                print(f"{Fore.RED}Passwords do not match. Please try again.{Style.RESET_ALL}")
                continue
                
        return password

class AuditResult:
    """
    Represents a single audit result with standardized fields and methods
    for serialization and comparison
    """
    def __init__(self, device_info, audit_type, timestamp=None):
        self.device_info = device_info  # Dictionary with device details
        self.audit_type = audit_type  # Type of audit performed
        self.timestamp = timestamp or datetime.datetime.now()
        self.audit_id = str(uuid.uuid4())
        self.phases = {}  # Dictionary to store phase results
        self.summary = {}  # Summary of findings
        self.recommendations = []  # List of recommendations
        self.notes = []  # Additional notes about the audit
        
    def add_phase_result(self, phase_name, status, details=None, error=None):
        """Add the result of an audit phase"""
        self.phases[phase_name] = {
            'status': status,
            'details': details or {},
            'error': error
        }
        return self.phases[phase_name]
        
    def get_phase_result(self, phase_name):
        """Get the result of a specific audit phase"""
        return self.phases.get(phase_name)
        
    def add_recommendation(self, recommendation, severity="medium", reference=None):
        """Add a recommendation based on audit findings"""
        self.recommendations.append({
            'text': recommendation,
            'severity': severity,
            'reference': reference
        })
        
    def add_note(self, note):
        """Add a note about the audit process or results"""
        if note and isinstance(note, str):
            self.notes.append({
                'text': note,
                'timestamp': datetime.datetime.now().isoformat()
            })
            return True
        return False
        
    def to_dict(self):
        """Convert the audit result to a dictionary for serialization"""
        return {
            'audit_id': self.audit_id,
            'device_info': self.device_info,
            'audit_type': self.audit_type,
            'timestamp': self.timestamp.isoformat(),
            'phases': self.phases,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'notes': self.notes
        }
        
    def to_json(self):
        """Convert the audit result to a JSON string"""
        return json.dumps(self.to_dict(), indent=2)
        
    @classmethod
    def from_dict(cls, data):
        """Create an AuditResult instance from a dictionary"""
        result = cls(
            device_info=data['device_info'],
            audit_type=data['audit_type'],
            timestamp=datetime.datetime.fromisoformat(data['timestamp'])
        )
        result.audit_id = data['audit_id']
        result.phases = data['phases']
        result.summary = data['summary']
        result.recommendations = data['recommendations']
        return result

class AuditReport:
    """
    Generates reports from audit results in various formats
    """
    def __init__(self, audit_results=None, report_dir=None, timestamp=None):
        self.audit_results = audit_results or []
        self.report_dir = report_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            DEFAULT_REPORT_DIR
        )
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_files = {
            'csv': None,
            'txt': None,
            'json': None,
            'html': None
        }
        
        # Ensure the report directory exists
        os.makedirs(self.report_dir, exist_ok=True)
        
    def add_result(self, audit_result):
        """Add an audit result to the report"""
        if isinstance(audit_result, AuditResult):
            self.audit_results.append(audit_result)
        elif isinstance(audit_result, dict):
            self.audit_results.append(AuditResult.from_dict(audit_result))
        else:
            raise TypeError("audit_result must be an AuditResult instance or dictionary")
    
    def generate_csv_report(self):
        """Generate a CSV report of audit results"""
        csv_file = os.path.join(self.report_dir, f"network_audit_report_{self.timestamp}.csv")
        
        with open(csv_file, 'w', newline='') as f:
            fieldnames = [
                'audit_id', 'device_hostname', 'device_ip', 'audit_type', 
                'timestamp', 'phase', 'status', 'details', 'recommendations'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.audit_results:
                device_hostname = result.device_info.get('hostname', 'Unknown')
                device_ip = result.device_info.get('ip', result.device_info.get('host', 'Unknown'))
                
                # Write a row for each phase
                for phase_name, phase_data in result.phases.items():
                    writer.writerow({
                        'audit_id': result.audit_id,
                        'device_hostname': device_hostname,
                        'device_ip': device_ip,
                        'audit_type': result.audit_type,
                        'timestamp': result.timestamp.isoformat(),
                        'phase': phase_name,
                        'status': phase_data['status'],
                        'details': str(phase_data['details']),
                        'recommendations': '; '.join(r['text'] for r in result.recommendations)
                    })
        
        self.report_files['csv'] = csv_file
        return csv_file
    
    def generate_text_report(self):
        """Generate a text report with detailed audit results"""
        txt_file = os.path.join(self.report_dir, f"network_audit_report_{self.timestamp}.txt")
        
        with open(txt_file, 'w') as f:
            f.write(f"==== NETWORK AUDIT REPORT ====\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tool Version: {VERSION}\n\n")
            
            f.write(f"Total Devices Audited: {len(self.audit_results)}\n\n")
            
            for result in self.audit_results:
                device_hostname = result.device_info.get('hostname', 'Unknown')
                device_ip = result.device_info.get('ip', result.device_info.get('host', 'Unknown'))
                
                f.write(f"\n{'='*50}\n")
                f.write(f"Device: {device_hostname} ({device_ip})\n")
                f.write(f"Audit Type: {result.audit_type}\n")
                f.write(f"Audit ID: {result.audit_id}\n")
                f.write(f"Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write phase results
                for phase_name, phase_data in result.phases.items():
                    status = phase_data['status']
                    status_symbol = "✓" if status == "Success" else "✗"
                    f.write(f"{status_symbol} Phase: {phase_name} - Status: {status}\n")
                    
                    if 'details' in phase_data and phase_data['details']:
                        if isinstance(phase_data['details'], dict):
                            for k, v in phase_data['details'].items():
                                f.write(f"   - {k}: {v}\n")
                        else:
                            f.write(f"   Details: {phase_data['details']}\n")
                    
                    if 'error' in phase_data and phase_data['error']:
                        f.write(f"   Error: {phase_data['error']}\n")
                    
                    f.write("\n")
                
                # Write recommendations
                if result.recommendations:
                    f.write("Recommendations:\n")
                    for rec in result.recommendations:
                        severity_marker = {
                            "critical": "!!!",
                            "high": "!!",
                            "medium": "!",
                            "low": ""
                        }.get(rec['severity'].lower(), "")
                        
                        f.write(f"   {severity_marker} {rec['text']}\n")
                        if rec['reference']:
                            f.write(f"     (Reference: {rec['reference']})\n")
                    f.write("\n")
        
        self.report_files['txt'] = txt_file
        return txt_file
    
    def generate_json_report(self):
        """Generate a JSON report with full audit data"""
        json_file = os.path.join(self.report_dir, f"network_audit_report_{self.timestamp}.json")
        
        with open(json_file, 'w') as f:
            json.dump({
                "meta": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "version": VERSION,
                    "report_id": str(uuid.uuid4())
                },
                "results": [result.to_dict() for result in self.audit_results]
            }, f, indent=2)
        
        self.report_files['json'] = json_file
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
        
        # Count unique devices by IP address
        unique_devices = set()
        for result in self.audit_results:
            device_ip = result.device_info.get('ip', result.device_info.get('host', 'Unknown'))
            device_hostname = result.device_info.get('hostname', 'Unknown')
            unique_devices.add(f"{device_hostname}:{device_ip}")
        
        # Count statistics
        total_results = len(self.audit_results)
        total_unique_devices = len(unique_devices)
        phase_stats = {}
        audit_types = set()
        
        # Initialize statistics
        for result in self.audit_results:
            audit_types.add(result.audit_type)
            for phase_name in result.phases.keys():
                if phase_name not in phase_stats:
                    phase_stats[phase_name] = {"success": 0, "failure": 0, "total": 0}
        
        # Calculate statistics
        for result in self.audit_results:
            for phase_name, phase_data in result.phases.items():
                status = phase_data['status']
                phase_stats[phase_name]["total"] += 1
                if status == "Success":
                    phase_stats[phase_name]["success"] += 1
                else:
                    phase_stats[phase_name]["failure"] += 1
        
        # Print device count and audit types
        print(f"\nTotal Unique Devices Audited: {total_unique_devices}")
        print(f"Total Audit Results: {total_results}")
        print(f"Audit Types: {', '.join(sorted(audit_types))}")
        if total_unique_devices != total_results:
            print(f"{Fore.YELLOW}Note: Multiple audit types ran on the same devices{Style.RESET_ALL}")
        
        # Print phase statistics
        print("\nPhase Results:")
        for phase_name, stats in sorted(phase_stats.items()):
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            status_color = Fore.GREEN if success_rate >= 75 else (Fore.YELLOW if success_rate >= 50 else Fore.RED)
            print(f"{status_color}{phase_name}: {stats['success']}/{stats['total']} successful ({success_rate:.1f}%){Style.RESET_ALL}")
        
        # Print report file locations
        print(f"\n{Fore.CYAN}Report Files:{Style.RESET_ALL}")
        for report_type, file_path in self.report_files.items():
            if file_path:
                print(f"  - {report_type.upper()}: {file_path}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

# If the module is run directly, perform basic setup and tests
if __name__ == "__main__":
    print(f"{Fore.CYAN}Network Audit Tool Core Module v{VERSION}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}This module provides common functionality for the audit components.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}It should not be run directly - import it in other modules instead.{Style.RESET_ALL}")
    
    # Perform basic setup as a test
    if ensure_directories():
        print(f"{Fore.GREEN}✓ All required directories created successfully{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Failed to create required directories{Style.RESET_ALL}")
        sys.exit(1)
    
    # Test logging
    logger, log_file = setup_logging()
    if logger:
        print(f"{Fore.GREEN}✓ Logging system initialized successfully{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Failed to initialize logging system{Style.RESET_ALL}")
        sys.exit(1)
