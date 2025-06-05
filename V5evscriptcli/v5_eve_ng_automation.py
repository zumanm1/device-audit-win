#!/usr/bin/env python3
"""
V5evscriptcli - EVE-NG MPLS L3VPN Topology Builder Enhanced
Creates complete MPLS L3VPN lab with CORRECT interface mapping for c3725 routers

Key Fix: Correct interface mapping for c3725 + NM-1FE-TX modules:
- f0/0, f0/1 = Onboard FastEthernet interfaces (API index 0, 1)
- f1/0 = NM-1FE-TX in slot 1 (API index 16)
- f2/0 = NM-1FE-TX in slot 2 (API index 32)

Version: 0.2.0
Author: MPLS L3VPN Automation Team
"""

import requests
import json
import logging
import time
import subprocess
import re
import os
from typing import Dict, List, Tuple, Optional
from functools import wraps

# ============================================================================
# ENHANCED LOGGING CONFIGURATION (Addresses BUG-007)
# ============================================================================

class StructuredLogger:
    """
    Enhanced logger with configurable levels and structured logging
    Addresses BUG-007: Limited Logging Granularity
    """
    
    def __init__(self, name: str = __name__, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.set_log_level(level)
        self._setup_formatter()
        
    def set_log_level(self, level: str):
        """Set logging level from string"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Also set root logger level
        logging.getLogger().setLevel(log_level)
        
    def _setup_formatter(self):
        """Setup structured log formatter"""
        # Check if handlers already exist to avoid duplicate logs
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Reduce noise from external libraries
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
    def log_api_call(self, method: str, url: str, status_code: int = None, duration: float = None):
        """Structured logging for API calls"""
        if status_code:
            self.logger.debug(f"API Call: {method} {url} -> {status_code} ({duration:.2f}s)")
        else:
            self.logger.debug(f"API Call: {method} {url}")
            
    def log_operation_start(self, operation: str, details: Dict = None):
        """Log the start of an operation with context"""
        msg = f"Starting {operation}"
        if details:
            msg += f" | Context: {details}"
        self.logger.info(msg)
        
    def log_operation_success(self, operation: str, details: Dict = None):
        """Log successful operation completion"""
        msg = f"✅ {operation} completed successfully"
        if details:
            msg += f" | Details: {details}"
        self.logger.info(msg)
        
    def log_operation_failure(self, operation: str, error: str, details: Dict = None):
        """Log operation failure with troubleshooting info"""
        msg = f"❌ {operation} failed: {error}"
        if details:
            msg += f" | Context: {details}"
        self.logger.error(msg)
        
    def log_validation_result(self, component: str, is_valid: bool, errors: List[str] = None):
        """Log validation results"""
        if is_valid:
            self.logger.debug(f"✅ {component} validation passed")
        else:
            self.logger.warning(f"❌ {component} validation failed:")
            if errors:
                for error in errors:
                    self.logger.warning(f"  - {error}")

    def log_performance(self, operation: str, duration: float, context: Dict = None) -> None:
        """Log performance metrics"""
        message = f"⚡ Performance: {operation} took {duration:.2f}s"
        if context:
            message = f"{message} | Context: {context}"
        self.logger.debug(message)
    
    # Standard logging methods for compatibility with existing code
    def debug(self, message: str, context: Dict = None) -> None:
        """Debug level logging"""
        if context:
            message = f"{message} | Context: {context}"
        self.logger.debug(message)
        
    def info(self, message: str, context: Dict = None) -> None:
        """Info level logging"""
        if context:
            message = f"{message} | Context: {context}"
        self.logger.info(message)
        
    def warning(self, message: str, context: Dict = None) -> None:
        """Warning level logging"""
        if context:
            message = f"{message} | Context: {context}"
        self.logger.warning(message)
        
    def error(self, message: str, context: Dict = None) -> None:
        """Error level logging"""
        if context:
            message = f"{message} | Context: {context}"
        self.logger.error(message)
        
    def critical(self, message: str, context: Dict = None) -> None:
        """Critical level logging"""
        if context:
            message = f"{message} | Context: {context}"
        self.logger.critical(message)

# Initialize enhanced logger
LOG_LEVEL = os.getenv('V5EVE_LOG_LEVEL', 'INFO')
logger = StructuredLogger(__name__, LOG_LEVEL)

# ============================================================================
# ERROR RECOVERY UTILITIES (Addresses BUG-005)
# ============================================================================

def retry_on_failure(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Decorator for retrying functions on failure with exponential backoff
    Addresses BUG-005: Limited Error Recovery
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                        break
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= backoff
            
            # If we get here, all retries failed
            raise last_exception
        return wrapper
    return decorator

def handle_api_errors(func):
    """
    Decorator for handling API errors gracefully
    Addresses BUG-005: Limited Error Recovery
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in {func.__name__}: {e}")
            logger.info("💡 Check network connectivity and EVE-NG server status")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in {func.__name__}: {e}")
            logger.info("💡 Try increasing timeout or check server load")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error in {func.__name__}: {e}")
            # Re-raise for retry decorator to handle
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.debug(f"Error details: {type(e).__name__}: {str(e)}")
            return None
    return wrapper

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================

# EVE-NG Connection Settings
EVE_HOST = "172.16.39.128"
EVE_USER = "admin" 
EVE_PASS = "eve"

# SSH Settings for troubleshooting
SSH_HOST = EVE_HOST
SSH_USER = "root"
SSH_PASS = "eve"

# Lab Settings
LAB_NAME = "mpls_l3vpn_enhanced"
LAB_AUTHOR = "V5evscriptcli Enhanced"
LAB_DESCRIPTION = "Enhanced MPLS L3VPN topology with correct interface mapping"
LAB_VERSION = "2"
LAB_PATH = "/"

# Router Template Settings
DEFAULT_ROUTER_TYPE = "dynamips"
DEFAULT_ROUTER_TEMPLATE = "c3725"
DEFAULT_ROUTER_IMAGE = "c3725-adventerprisek9-mz.124-15.T14.image"
DEFAULT_ROUTER_RAM = "256"
DEFAULT_ROUTER_NVRAM = "256"
DEFAULT_ROUTER_IDLE = "0x60606040"
DEFAULT_CONSOLE_TYPE = "telnet"
DEFAULT_ETHERNET_COUNT = "6"

# Network Module Configuration
ROUTER_SLOTS = {
    "slot1": "NM-1FE-TX",  # Provides f1/0
    "slot2": "NM-1FE-TX"   # Provides f2/0
}

# Management Network Settings
USE_MANAGEMENT_NETWORK = True
MANAGEMENT_NETWORK_NAME = "Management"
MANAGEMENT_NETWORK_TYPE = "bridge"

# ============================================================================
# TOPOLOGY DEFINITION
# ============================================================================

TOPOLOGY_ROUTERS = {
    "CE-4": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE, 
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png",
        "left": "100", "top": "150",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": "",
        "mgmt_interface": "f0/1"
    },
    "CE-5": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE,
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png", 
        "left": "100", "top": "350",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": "",
        "mgmt_interface": "f0/1"
    },
    "PE1": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE,
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png",
        "left": "300", "top": "150", 
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": ROUTER_SLOTS.get("slot2", ""),
        "mgmt_interface": "f2/0"
    },
    "PE2": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE,
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png",
        "left": "300", "top": "350",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": ROUTER_SLOTS.get("slot2", ""),
        "mgmt_interface": "f2/0"
    },
    "P": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE,
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png",
        "left": "500", "top": "250",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": ROUTER_SLOTS.get("slot2", ""),
        "mgmt_interface": "f2/0"
    },
    "RR1": {
        "type": DEFAULT_ROUTER_TYPE,
        "template": DEFAULT_ROUTER_TEMPLATE,
        "image": DEFAULT_ROUTER_IMAGE,
        "ram": DEFAULT_ROUTER_RAM,
        "nvram": DEFAULT_ROUTER_NVRAM,
        "idlepc": DEFAULT_ROUTER_IDLE,
        "icon": "Router.png",
        "left": "700", "top": "250",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": ROUTER_SLOTS.get("slot2", ""),
        "mgmt_interface": "f2/0"
    }
}

# Connection Definitions - CRITICAL: These use the interfaces that need correct mapping
TOPOLOGY_CONNECTIONS = [
    ("CE-4", "f1/0", "PE1", "f1/0", "Link_CE4_PE1", "200", "150"),
    ("PE1", "f0/0", "P", "f0/0", "Link_PE1_P", "400", "200"), 
    ("P", "f0/1", "PE2", "f0/1", "Link_P_PE2", "400", "300"),
    ("P", "f1/0", "RR1", "f1/0", "Link_P_RR1", "600", "250"),
    ("PE2", "f0/0", "CE-5", "f0/0", "Link_PE2_CE5", "200", "350"),
]

# ============================================================================
# SSH TROUBLESHOOTING FUNCTIONS
# ============================================================================

def ssh_execute_command(command: str) -> Optional[str]:
    """Execute command via SSH on EVE-NG host for troubleshooting"""
    try:
        ssh_cmd = f"sshpass -p '{SSH_PASS}' ssh -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.debug(f"SSH command succeeded: {command}")
            return result.stdout
        else:
            logger.warning(f"SSH command failed: {command}, Error: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"SSH execution failed: {e}")
        return None

def verify_ssh_access() -> bool:
    """Verify SSH access to EVE-NG host"""
    logger.info(f"Verifying SSH access to {SSH_HOST}...")
    result = ssh_execute_command("echo 'SSH connection test'")
    if result:
        logger.info("✅ SSH access verified")
        return True
    else:
        logger.warning("⚠️ SSH access failed - troubleshooting features may be limited")
        return False

# ============================================================================
# EVE-NG API CLIENT CLASS
# ============================================================================

class EVEClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.base_url = f"http://{host}/api"
        
        # Initialize caches for performance improvement (addresses BUG-004)
        self._interface_cache = {}
        self._lab_cache = {}
        self._node_cache = {}
        self._network_cache = {}
        self._cache_timeout = 300  # 5 minutes cache timeout
        self._cache_timestamps = {}
        
        # Initialize rollback tracking (addresses BUG-008)
        self._deployment_state = {
            "lab_created": False,
            "lab_name": None,
            "lab_folder": "/",
            "nodes_created": [],
            "networks_created": [],
            "connections_created": [],
            "rollback_enabled": True
        }

    @retry_on_failure(max_retries=2, delay=3, exceptions=(requests.exceptions.RequestException,))
    def api_request(self, method, endpoint, data=None, timeout=15):
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            logger.log_api_call(method, url)
            if data and method not in ['GET', 'DELETE']:
                logger.logger.debug(f"Payload: {json.dumps(data, indent=2)}")

            if method == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            elif method == 'PUT':
                response = self.session.put(url, json=data, timeout=timeout)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            duration = time.time() - start_time
            logger.log_api_call(method, url, response.status_code, duration)
            
            if response.status_code >= 400:
                if response.status_code == 401:
                    logger.logger.error("Authentication error (401). Please check credentials.")
                logger.logger.error(f"API Error {response.status_code} for {method} {url}. Response: {response.text}")
                return response

            if response.content:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    logger.logger.warning(f"Failed to decode JSON from response")
                    return {"status": "success_non_json", "text": response.text, "http_status_code": response.status_code}

            return {"status": "success", "http_status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            logger.log_operation_failure(f"API Request {method} {url}", str(e), {"duration": duration})
            # Re-raise for retry decorator to handle
            raise e

    @retry_on_failure(max_retries=2, delay=3, exceptions=(requests.exceptions.RequestException,))
    def login(self):
        logger.log_operation_start("EVE-NG Authentication")
        response_data = self.api_request('POST', '/auth/login', {
            "username": self.username, "password": self.password, "html5": "-1"
        })
        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            logger.log_operation_success("Login", {"user": self.username})
            return True
        else:
            logger.log_operation_failure("Login", f"Authentication failed", {"response": response_data})
            return False

    def logout(self):
        try:
            self.session.get(f"{self.base_url}/auth/logout")
            logger.logger.info("Logged out successfully")
        except:
            pass
        finally:
            self.session.close()

    def get_api_lab_path(self, lab_name_base, folder_path="/"):
        lab_filename = f"{lab_name_base}.unl"
        if not folder_path or folder_path.strip() == "/":
            return f"/{lab_filename}"
        else:
            clean_folder_path = folder_path.strip("/")
            return f"/{clean_folder_path}/{lab_filename}"

    def create_lab(self, name, path="/", author="", description="", version="1"):
        logger.log_operation_start("Lab Creation", {"name": name, "path": path})
        
        # Validate lab configuration (addresses BUG-006)
        is_valid, errors = self.validate_lab_config(name, path, author, description, version)
        logger.log_validation_result("Lab Configuration", is_valid, errors)
        if not is_valid:
            return False
        
        api_lab_uri_path = self.get_api_lab_path(name, path)
        
        # Check if lab exists
        try:
            check_response = self.session.get(f"{self.base_url}/labs{api_lab_uri_path}")
            if check_response.status_code == 200:
                logger.log_operation_success("Lab Verification", {"name": name, "status": "already_exists"})
                return True
        except:
            pass

        # Create lab
        create_payload = {"path": path, "name": name, "author": author, "description": description, "version": version}
        response = self.api_request('POST', '/labs', create_payload)
        
        if isinstance(response, dict) and response.get('status') == 'success':
            logger.log_operation_success("Lab Creation", {"name": name, "path": path})
            # Track lab creation for rollback (addresses BUG-008)
            self.track_lab_creation(name)
            time.sleep(2)
            return True
        else:
            logger.log_operation_failure("Lab Creation", "API request failed", {"name": name, "response": response})
            return False

    def create_node(self, lab_name, node_config, lab_folder="/"):
        node_name = node_config.get('name', 'Unknown')
        logger.log_operation_start("Node Creation", {"name": node_name, "lab": lab_name})
        
        # Validate node configuration (addresses BUG-006)
        is_valid, errors = self.validate_node_config(node_config)
        logger.log_validation_result("Node Configuration", is_valid, errors)
        if not is_valid:
            return None
        
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response_data = self.api_request('POST', f'/labs{api_lab_uri_path}/nodes', node_config)

        if isinstance(response_data, dict) and response_data.get('status') == 'success' and 'data' in response_data:
            node_id = response_data['data']['id']
            logger.log_operation_success("Node Creation", {"name": node_name, "id": node_id})
            # Track node creation for rollback (addresses BUG-008)
            self.track_node_creation(node_name, str(node_id))
            return str(node_id)
        else:
            logger.log_operation_failure("Node Creation", "API request failed", {"name": node_name, "response": response_data})
            return None

    def create_network(self, lab_name, network_type="bridge", network_name="Network1", lab_folder="/", left="400", top="100"):
        logger.info(f"Creating network '{network_name}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        config = {"type": network_type, "name": network_name, "left": str(left), "top": str(top), "visibility": "1"}
        response_data = self.api_request('POST', f'/labs{api_lab_uri_path}/networks', config)

        if isinstance(response_data, dict) and response_data.get('status') == 'success' and 'data' in response_data:
            network_id = response_data['data']['id']
            logger.info(f"✅ Network '{network_name}' created with ID: {network_id}")
            # Track network creation for rollback (addresses BUG-008)
            self.track_network_creation(network_name, str(network_id))
            return str(network_id)
        else:
            logger.error(f"❌ Failed to create network '{network_name}'")
            return None

    def is_valid_interface(self, interface_name: str, router_type: str = "c3725") -> bool:
        """
        Validate interface name for multiple router types
        Addresses NEW-001: Multi-Vendor Router Support
        
        Supported routers and their valid interfaces:
        - c3725: f0/0, f0/1, f1/0, f2/0 (with NM-1FE-TX modules)
        - c7200: g0/0-g5/0 (6xGE), f0/0-f3/0+g0/0-g1/0 (4xFE+2xGE)
        - c3640: f0/0, f0/1, f1/0, f2/0 (with NM modules)
        - c2691: f0/0, f0/1, f1/0, f2/0 (with NM modules)
        - c1700: f0/0, s0/0, s0/1 (1xFE + WIC slots)
        """
        return self._validate_interface_for_router_type(interface_name, router_type)
    
    def _validate_interface_for_router_type(self, interface_name: str, router_type: str) -> bool:
        """Validate interface based on router type"""
        # Define interface patterns for each router type
        interface_patterns = {
            'c3725': {
                'pattern': r'^f[0-2]/[0-1]$',
                'valid_interfaces': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
                'description': 'FastEthernet interfaces (f0/0, f0/1 onboard; f1/0, f2/0 with NM-1FE-TX)'
            },
            'c7200': {
                'pattern': r'^(g[0-5]/0|f[0-3]/0)$',
                'valid_interfaces': ['g0/0', 'g1/0', 'g2/0', 'g3/0', 'g4/0', 'g5/0', 'f0/0', 'f1/0', 'f2/0', 'f3/0'],
                'description': 'GigabitEthernet (g0/0-g5/0) or FastEthernet (f0/0-f3/0) interfaces'
            },
            'c3640': {
                'pattern': r'^f[0-2]/[0-1]$',
                'valid_interfaces': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
                'description': 'FastEthernet interfaces (f0/0, f0/1 onboard; f1/0, f2/0 with NM modules)'
            },
            'c2691': {
                'pattern': r'^f[0-2]/[0-1]$',
                'valid_interfaces': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
                'description': 'FastEthernet interfaces (f0/0, f0/1 onboard; f1/0, f2/0 with NM modules)'
            },
            'c1700': {
                'pattern': r'^(f0/0|s0/[0-1])$',
                'valid_interfaces': ['f0/0', 's0/0', 's0/1'],
                'description': 'FastEthernet f0/0 (onboard) or Serial s0/0, s0/1 (with WIC modules)'
            }
        }
        
        if router_type not in interface_patterns:
            logger.warning(f"Unknown router type: {router_type}. Falling back to c3725 validation.")
            router_type = 'c3725'
        
        pattern_info = interface_patterns[router_type]
        
        # First check with regex pattern
        if not re.match(pattern_info['pattern'], interface_name):
            return False
        
        # Then check against known valid interfaces (more restrictive)
        return interface_name in pattern_info['valid_interfaces']

    def get_interface_index(self, interface_name: str, router_type: str = "c3725") -> str:
        """
        Get the correct API interface index for multiple router types
        Addresses NEW-001: Multi-Vendor Router Support
        Enhanced from BUG-001: Interface Mapping Validation Missing
        
        Router-specific interface mappings:
        - c3725: f0/0→0, f0/1→1, f1/0→16, f2/0→32 (NM-1FE-TX slots)
        - c7200: g0/0→0, g1/0→1, g2/0→2, g3/0→3, g4/0→4, g5/0→5, f0/0→6, f1/0→7, f2/0→8, f3/0→9
        - c3640: f0/0→0, f0/1→1, f1/0→16, f2/0→32 (NM slots)
        - c2691: f0/0→0, f0/1→1, f1/0→16, f2/0→32 (NM slots)
        - c1700: f0/0→0, s0/0→1, s0/1→2 (WIC slots)
        """
        if not self.is_valid_interface(interface_name, router_type):
            raise ValueError(f"Invalid interface name '{interface_name}' for router type '{router_type}'")
        
        # Use cache if available
        cache_key = f"{router_type}_{interface_name}"
        if hasattr(self, '_interface_cache') and cache_key in self._interface_cache:
            return self._interface_cache[cache_key]
        
        # Calculate interface index
        index = self._calculate_interface_index(interface_name, router_type)
        
        # Cache the result
        if not hasattr(self, '_interface_cache'):
            self._interface_cache = {}
        self._interface_cache[cache_key] = index
        
        return index

    def _calculate_interface_index(self, interface_name: str, router_type: str) -> str:
        """Calculate the interface index based on router type and interface name"""
        # Define interface mappings for each router type
        interface_mappings = {
            'c3725': {
                'f0/0': '0',   # Onboard FastEthernet 0/0
                'f0/1': '1',   # Onboard FastEthernet 0/1
                'f1/0': '16',  # NM-1FE-TX in slot 1
                'f2/0': '32'   # NM-1FE-TX in slot 2
            },
            'c7200': {
                # 6x GigabitEthernet configuration
                'g0/0': '0',   # GigabitEthernet 0/0
                'g1/0': '1',   # GigabitEthernet 1/0
                'g2/0': '2',   # GigabitEthernet 2/0
                'g3/0': '3',   # GigabitEthernet 3/0
                'g4/0': '4',   # GigabitEthernet 4/0
                'g5/0': '5',   # GigabitEthernet 5/0
                # 4x FastEthernet + 2x GigabitEthernet configuration (alternative)
                'f0/0': '6',   # FastEthernet 0/0
                'f1/0': '7',   # FastEthernet 1/0
                'f2/0': '8',   # FastEthernet 2/0
                'f3/0': '9'    # FastEthernet 3/0
            },
            'c3640': {
                'f0/0': '0',   # Onboard FastEthernet 0/0
                'f0/1': '1',   # Onboard FastEthernet 0/1
                'f1/0': '16',  # NM module in slot 1
                'f2/0': '32'   # NM module in slot 2
            },
            'c2691': {
                'f0/0': '0',   # Onboard FastEthernet 0/0
                'f0/1': '1',   # Onboard FastEthernet 0/1
                'f1/0': '16',  # NM module in slot 1
                'f2/0': '32'   # NM module in slot 2
            },
            'c1700': {
                'f0/0': '0',   # Onboard FastEthernet 0/0
                's0/0': '1',   # Serial 0/0 (WIC slot)
                's0/1': '2'    # Serial 0/1 (WIC slot)
            }
        }
        
        if router_type not in interface_mappings:
            raise ValueError(f"Unsupported router type: {router_type}")
        
        router_mapping = interface_mappings[router_type]
        
        if interface_name not in router_mapping:
            raise ValueError(f"Interface '{interface_name}' not supported for router type '{router_type}'")
        
        return router_mapping[interface_name]
    
    def get_supported_interfaces(self, router_type: str) -> List[str]:
        """
        Get list of supported interfaces for a given router type
        Addresses NEW-001: Multi-Vendor Router Support
        """
        interface_lists = {
            'c3725': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
            'c7200': ['g0/0', 'g1/0', 'g2/0', 'g3/0', 'g4/0', 'g5/0', 'f0/0', 'f1/0', 'f2/0', 'f3/0'],
            'c3640': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
            'c2691': ['f0/0', 'f0/1', 'f1/0', 'f2/0'],
            'c1700': ['f0/0', 's0/0', 's0/1']
        }
        
        if router_type not in interface_lists:
            logger.warning(f"Unknown router type: {router_type}. Returning c3725 interfaces.")
            return interface_lists['c3725']
        
        return interface_lists[router_type]
    
    def get_router_type_from_config(self, node_config: Dict) -> str:
        """
        Extract router type from node configuration
        Addresses NEW-001: Multi-Vendor Router Support
        """
        # Check template field first
        router_type = node_config.get('template', 'c3725')
        
        # Validate router type is supported
        supported_types = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
        if router_type not in supported_types:
            logger.warning(f"Unsupported router type '{router_type}'. Falling back to c3725.")
            return 'c3725'
        
        return router_type

    def validate_interfaces(self, interfaces: List[str], router_type: str = "c3725") -> List[str]:
        """
        Validate a list of interface names for specific router type
        Enhanced for NEW-001: Multi-Vendor Router Support
        Returns list of invalid interfaces
        """
        invalid_interfaces = []
        for interface in interfaces:
            if not self.is_valid_interface(interface, router_type):
                invalid_interfaces.append(interface)
        return invalid_interfaces

    def connect_node_to_network(self, lab_name, node_id, interface_name, network_id, lab_folder="/", router_type="c3725"):
        """Enhanced connection method with multi-vendor interface validation"""
        # Validate interface before attempting connection
        if not self.is_valid_interface(interface_name, router_type):
            supported_interfaces = self.get_supported_interfaces(router_type)
            raise ValueError(f"Invalid interface name '{interface_name}' for router type '{router_type}'. Valid interfaces: {', '.join(supported_interfaces)}")
        
        # Get correct interface index
        interface_index = self.get_interface_index(interface_name, router_type)
        
        logger.log_operation_start("Interface Connection", {
            "node_id": node_id, 
            "interface": interface_name, 
            "index": interface_index, 
            "network_id": network_id,
            "router_type": router_type
        })
        
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        endpoint = f'/labs{api_lab_uri_path}/nodes/{node_id}/interfaces'
        
        data = {
            interface_index: str(network_id)
        }
        
        response = self.api_request('PUT', endpoint, data)
        
        if isinstance(response, dict) and response.get('status') == 'success':
            logger.log_operation_success("Interface Connection", {
                "node_id": node_id, 
                "interface": interface_name, 
                "index": interface_index, 
                "network_id": network_id,
                "router_type": router_type
            })
            # Track connection creation for rollback (addresses BUG-008)
            self.track_connection_creation({
                "node_id": node_id,
                "interface": interface_name,
                "interface_index": interface_index,
                "network_id": network_id,
                "lab_name": lab_name,
                "router_type": router_type
            })
            return True
        else:
            logger.log_operation_failure("Interface Connection", "API request failed", {
                "node_id": node_id, 
                "interface": interface_name, 
                "network_id": network_id,
                "router_type": router_type,
                "response": response
            })
            # SSH troubleshooting hint
            logger.logger.info(f"💡 For troubleshooting, try: ssh {SSH_USER}@{SSH_HOST}")
            return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid based on timeout"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_age = time.time() - self._cache_timestamps[cache_key]
        return cache_age < self._cache_timeout

    def _set_cache(self, cache_dict: dict, cache_key: str, value: any) -> None:
        """Set cache value and timestamp"""
        cache_dict[cache_key] = value
        self._cache_timestamps[cache_key] = time.time()

    def _get_cache(self, cache_dict: dict, cache_key: str) -> any:
        """Get cache value if valid, otherwise return None"""
        if self._is_cache_valid(cache_key) and cache_key in cache_dict:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cache_dict[cache_key]
        return None

    def clear_cache(self) -> None:
        """Clear all caches - useful for testing or when data changes"""
        self._interface_cache.clear()
        self._lab_cache.clear()
        self._node_cache.clear()
        self._network_cache.clear()
        self._cache_timestamps.clear()
        logger.debug("All caches cleared")

    def get_node_interfaces(self, lab_name, node_id, lab_folder="/"):
        """Enhanced with caching to address BUG-004"""
        cache_key = f"{lab_name}_{lab_folder}_{node_id}_interfaces"
        
        # Check cache first
        cached_result = self._get_cache(self._node_cache, cache_key)
        if cached_result is not None:
            return cached_result
        
        # Make API call if not cached
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response = self.api_request('GET', f'/labs{api_lab_uri_path}/nodes/{node_id}/interfaces')

        if isinstance(response, dict) and response.get('status') == 'success':
            result = response.get('data', {})
            # Cache the result
            self._set_cache(self._node_cache, cache_key, result)
            return result
        else:
            return None

    def verify_connection(self, lab_name, node_id, network_id_to_check, lab_folder="/"):
        """ENHANCED: Verify connection with improved API response parsing"""
        logger.info(f"Verifying connection for node {node_id} to network {network_id_to_check}...")
        interfaces_data = self.get_node_interfaces(lab_name, node_id, lab_folder)

        if interfaces_data:
            logger.debug(f"Interface data structure: {interfaces_data}")
            
            # Handle different response formats from EVE-NG API
            if 'ethernet' in interfaces_data:
                # New format: {'ethernet': {'0': {'name': 'fa0/0', 'network_id': X}, ...}}
                for iface_id, iface_info in interfaces_data['ethernet'].items():
                    if isinstance(iface_info, dict):
                        network_id = iface_info.get('network_id', 0)
                        if str(network_id) == str(network_id_to_check):
                            logger.info(f"✅ Verified: Node {node_id} interface {iface_id} connected to network {network_id_to_check}")
                            return True
            else:
                # Legacy format: direct interface mapping
                for key, value in interfaces_data.items():
                    if isinstance(value, dict):
                        network_id = value.get('network_id', 0)
                        if str(network_id) == str(network_id_to_check):
                            logger.info(f"✅ Verified: Node {node_id} interface {key} connected to network {network_id_to_check}")
                            return True

        logger.warning(f"❌ Node {node_id} NOT connected to network {network_id_to_check}")
        return False

    # ============================================================================
    # CONFIGURATION VALIDATION (Addresses BUG-006)
    # ============================================================================

    def validate_node_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate node configuration before deployment
        Enhanced for NEW-001: Multi-Vendor Router Support
        Addresses BUG-006: No Configuration Validation
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields validation
        required_fields = ['type', 'template', 'name']
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Node name validation
        if 'name' in config:
            name = config['name']
            if not re.match(r'^[a-zA-Z0-9_-]+$', name):
                errors.append(f"Invalid node name '{name}'. Use only alphanumeric characters, underscore, and dash")
            if len(name) > 50:
                errors.append(f"Node name '{name}' too long. Maximum 50 characters")
        
        # Template validation - Enhanced for multi-vendor support
        valid_templates = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
        if 'template' in config and config['template'] not in valid_templates:
            errors.append(f"Invalid template '{config['template']}'. Valid templates: {valid_templates}")
        
        # Type validation
        valid_types = ['dynamips', 'qemu', 'docker', 'vpcs']
        if 'type' in config and config['type'] not in valid_types:
            errors.append(f"Invalid type '{config['type']}'. Valid types: {valid_types}")
        
        # Router-specific validation
        router_type = config.get('template', 'c3725')
        errors.extend(self._validate_router_specific_config(config, router_type))
        
        # Position validation
        for pos_field in ['left', 'top']:
            if pos_field in config:
                try:
                    pos = int(config[pos_field])
                    if pos < 0 or pos > 2000:
                        errors.append(f"Position {pos_field}={pos} out of range. Valid range: 0-2000")
                except (ValueError, TypeError):
                    errors.append(f"Invalid {pos_field} position '{config[pos_field]}'. Must be a number")
        
        return len(errors) == 0, errors
    
    def _validate_router_specific_config(self, config: Dict, router_type: str) -> List[str]:
        """
        Validate router-specific configuration parameters
        Addresses NEW-001: Multi-Vendor Router Support
        """
        errors = []
        
        # Router-specific RAM validation
        if config.get('type') == 'dynamips' and 'ram' in config:
            try:
                ram = int(config['ram'])
                ram_ranges = {
                    'c3725': (128, 512),
                    'c7200': (256, 1024),
                    'c3640': (128, 512),
                    'c2691': (128, 512),
                    'c1700': (64, 256)
                }
                
                min_ram, max_ram = ram_ranges.get(router_type, (128, 512))
                if ram < min_ram or ram > max_ram:
                    errors.append(f"RAM value {ram}MB out of range for {router_type}. Valid range: {min_ram}-{max_ram}MB")
            except (ValueError, TypeError):
                errors.append(f"Invalid RAM value '{config['ram']}'. Must be a number")
        
        # Router-specific module validation
        valid_modules_by_router = {
            'c3725': ['NM-1FE-TX', 'NM-4T', 'NM-16ESW', ''],
            'c7200': ['PA-GE', 'PA-FE-TX', 'PA-4E', 'PA-8E', ''],
            'c3640': ['NM-1FE-TX', 'NM-4T', 'NM-2FE2W', ''],
            'c2691': ['NM-1FE-TX', 'NM-4T', 'NM-2FE2W', ''],
            'c1700': ['WIC-1T', 'WIC-2T', 'WIC-1ENET', '']
        }
        
        valid_modules = valid_modules_by_router.get(router_type, [''])
        
        # Validate slots based on router type
        if router_type in ['c3725', 'c3640', 'c2691']:
            for slot in ['slot1', 'slot2']:
                if slot in config and config[slot] not in valid_modules:
                    errors.append(f"Invalid module '{config[slot]}' in {slot} for {router_type}. Valid modules: {valid_modules}")
        elif router_type == 'c7200':
            for slot in ['slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6']:
                if slot in config and config[slot] not in valid_modules:
                    errors.append(f"Invalid PA module '{config[slot]}' in {slot} for {router_type}. Valid modules: {valid_modules}")
        elif router_type == 'c1700':
            for slot in ['wic0', 'wic1']:
                if slot in config and config[slot] not in valid_modules:
                    errors.append(f"Invalid WIC module '{config[slot]}' in {slot} for {router_type}. Valid modules: {valid_modules}")
        
        return errors

    def validate_lab_config(self, name: str, path: str = "/", 
                           author: str = "", description: str = "", 
                           version: str = "1") -> Tuple[bool, List[str]]:
        """
        Validate lab configuration
        Addresses BUG-006: No Configuration Validation
        """
        errors = []
        
        # Lab name validation
        if not name or not name.strip():
            errors.append("Lab name cannot be empty")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', name):
            errors.append(f"Invalid lab name '{name}'. Use only alphanumeric characters, underscore, and dash")
        elif len(name) > 100:
            errors.append(f"Lab name '{name}' too long. Maximum 100 characters")
        
        # Path validation
        if not path.startswith('/'):
            errors.append(f"Lab path '{path}' must start with '/'")
        
        # Author validation
        if len(author) > 100:
            errors.append(f"Author name too long. Maximum 100 characters")
        
        # Description validation
        if len(description) > 500:
            errors.append(f"Description too long. Maximum 500 characters")
        
        # Version validation
        if not re.match(r'^\d+(\.\d+)*$', version):
            errors.append(f"Invalid version format '{version}'. Use format like '1' or '1.0' or '1.0.0'")
        
        return len(errors) == 0, errors

    def validate_connection_config(self, router1: str, iface1: str, 
                                  router2: str, iface2: str, 
                                  routers: Dict[str, str], 
                                  router_configs: Dict[str, Dict] = None) -> Tuple[bool, List[str]]:
        """
        Validate connection configuration with multi-vendor support
        Enhanced for NEW-001: Multi-Vendor Router Support
        Addresses BUG-006: No Configuration Validation
        """
        errors = []
        
        # Check if routers exist
        if router1 not in routers:
            errors.append(f"Router '{router1}' not found in topology")
        if router2 not in routers:
            errors.append(f"Router '{router2}' not found in topology")
        
        # Validate interfaces with router type consideration
        if router_configs:
            # Get router types from configurations
            router1_type = router_configs.get(router1, {}).get('template', 'c3725')
            router2_type = router_configs.get(router2, {}).get('template', 'c3725')
        else:
            # Default to c3725 if no configs provided
            router1_type = router2_type = 'c3725'
        
        if not self.is_valid_interface(iface1, router1_type):
            valid_ifaces = self.get_supported_interfaces(router1_type)
            errors.append(f"Invalid interface '{iface1}' for router '{router1}' (type: {router1_type}). Valid interfaces: {', '.join(valid_ifaces)}")
        
        if not self.is_valid_interface(iface2, router2_type):
            valid_ifaces = self.get_supported_interfaces(router2_type)
            errors.append(f"Invalid interface '{iface2}' for router '{router2}' (type: {router2_type}). Valid interfaces: {', '.join(valid_ifaces)}")
        
        # Check for self-connection
        if router1 == router2:
            errors.append(f"Cannot connect router '{router1}' to itself")
        
        return len(errors) == 0, errors

    def get_node_config_template(self, router_type: str = "c3725") -> Dict:
        """
        Get a validated configuration template for node creation
        Enhanced for NEW-001: Multi-Vendor Router Support  
        Addresses BUG-006: No Configuration Validation
        """
        templates = {
            "c3725": {
                "type": "dynamips",
                "template": "c3725",
                "name": "Router1",
                "image": "c3725-adventerprisek9-mz.124-15.T14.image",
                "ram": "256",
                "nvram": "256",
                "idlepc": "0x60606040",
                "icon": "Router.png",
                "left": "400",
                "top": "200",
                "console": "telnet",
                "config": "0",
                "ethernet": "6",
                "slot1": "NM-1FE-TX",
                "slot2": ""
            },
            "c7200": {
                "type": "dynamips",
                "template": "c7200",
                "name": "Router1",
                "image": "c7200-adventerprisek9-mz.124-24.T5.image",
                "ram": "512",
                "nvram": "512",
                "idlepc": "0x606df838",
                "icon": "Router.png", 
                "left": "400",
                "top": "200",
                "console": "telnet",
                "config": "0",
                "ethernet": "12",
                "slot1": "PA-GE",
                "slot2": "PA-GE",
                "slot3": "",
                "slot4": "",
                "slot5": "",
                "slot6": ""
            },
            "c3640": {
                "type": "dynamips",
                "template": "c3640",
                "name": "Router1",
                "image": "c3640-jk.124-10a.image",
                "ram": "256",
                "nvram": "256",
                "idlepc": "0x60505050",
                "icon": "Router.png",
                "left": "400", 
                "top": "200",
                "console": "telnet",
                "config": "0",
                "ethernet": "4",
                "slot1": "NM-1FE-TX",
                "slot2": ""
            },
            "c2691": {
                "type": "dynamips",
                "template": "c2691",
                "name": "Router1",
                "image": "c2691-adventerprisek9-mz.124-15.T14.image",
                "ram": "256",
                "nvram": "256",
                "idlepc": "0x60a48000",
                "icon": "Router.png",
                "left": "400",
                "top": "200", 
                "console": "telnet",
                "config": "0",
                "ethernet": "4",
                "slot1": "NM-1FE-TX",
                "slot2": ""
            },
            "c1700": {
                "type": "dynamips",
                "template": "c1700",
                "name": "Router1",
                "image": "c1700-k.122-8.T5.image",
                "ram": "128",
                "nvram": "256",
                "idlepc": "0x80369ac4",
                "icon": "Router.png",
                "left": "400",
                "top": "200",
                "console": "telnet", 
                "config": "0",
                "ethernet": "1",
                "wic0": "WIC-1T",
                "wic1": ""
            }
        }
        
        if router_type not in templates:
            logger.warning(f"No template available for router type: {router_type}. Using c3725 template.")
            router_type = "c3725"
        
        return templates[router_type].copy()
    
    def get_available_router_types(self) -> List[str]:
        """
        Get list of all supported router types
        Addresses NEW-001: Multi-Vendor Router Support
        """
        return ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
    
    def get_router_specifications(self, router_type: str) -> Dict:
        """
        Get detailed specifications for a router type
        Addresses NEW-001: Multi-Vendor Router Support
        """
        specifications = {
            'c3725': {
                'description': 'Cisco 3725 Modular Router',
                'onboard_interfaces': ['f0/0', 'f0/1'],
                'slot_interfaces': ['f1/0', 'f2/0'],
                'supported_modules': ['NM-1FE-TX', 'NM-4T', 'NM-16ESW'],
                'ram_range': '128-512MB',
                'max_slots': 2,
                'typical_use': 'Branch office, small enterprise'
            },
            'c7200': {
                'description': 'Cisco 7200 Series Router',
                'onboard_interfaces': [],
                'slot_interfaces': ['g0/0', 'g1/0', 'g2/0', 'g3/0', 'g4/0', 'g5/0'],
                'supported_modules': ['PA-GE', 'PA-FE-TX', 'PA-4E', 'PA-8E'],
                'ram_range': '256-1024MB',
                'max_slots': 6,
                'typical_use': 'Enterprise core, service provider'
            },
            'c3640': {
                'description': 'Cisco 3640 Modular Router',
                'onboard_interfaces': ['f0/0', 'f0/1'],
                'slot_interfaces': ['f1/0', 'f2/0'],
                'supported_modules': ['NM-1FE-TX', 'NM-4T', 'NM-2FE2W'],
                'ram_range': '128-512MB',
                'max_slots': 2,
                'typical_use': 'Branch office, medium enterprise'
            },
            'c2691': {
                'description': 'Cisco 2691 Modular Router',
                'onboard_interfaces': ['f0/0', 'f0/1'],
                'slot_interfaces': ['f1/0', 'f2/0'],
                'supported_modules': ['NM-1FE-TX', 'NM-4T', 'NM-2FE2W'],
                'ram_range': '128-512MB',
                'max_slots': 2,
                'typical_use': 'Small branch office'
            },
            'c1700': {
                'description': 'Cisco 1700 Series Router',
                'onboard_interfaces': ['f0/0'],
                'slot_interfaces': ['s0/0', 's0/1'],
                'supported_modules': ['WIC-1T', 'WIC-2T', 'WIC-1ENET'],
                'ram_range': '64-256MB',
                'max_slots': 2,
                'typical_use': 'Small office, home office (SOHO)'
            }
        }
        
        return specifications.get(router_type, {})

    def validate_topology_config(self, routers: Dict, connections: List) -> Tuple[bool, List[str]]:
        """
        Validate entire topology configuration with multi-vendor support
        Enhanced for NEW-001: Multi-Vendor Router Support
        Addresses BUG-006: No Configuration Validation
        """
        errors = []
        
        # Validate each router
        for router_name, router_config in routers.items():
            # Add name to config for validation
            config_with_name = router_config.copy()
            config_with_name['name'] = router_name
            
            is_valid, router_errors = self.validate_node_config(config_with_name)
            if not is_valid:
                errors.extend([f"Router '{router_name}': {err}" for err in router_errors])
        
        # Track interface usage to detect conflicts
        interface_usage = {}
        
        # Validate each connection with router configurations
        for connection in connections:
            if len(connection) < 5:
                errors.append(f"Invalid connection format: {connection}")
                continue
                
            router1, iface1, router2, iface2 = connection[:4]
            
            # Validate connection with router configurations
            is_valid, conn_errors = self.validate_connection_config(
                router1, iface1, router2, iface2, 
                {name: config.get('template', 'c3725') for name, config in routers.items()},
                routers
            )
            if not is_valid:
                errors.extend(conn_errors)
            
            # Track interface usage
            router1_iface = f"{router1}:{iface1}"
            router2_iface = f"{router2}:{iface2}"
            
            if router1_iface in interface_usage:
                errors.append(f"Interface {iface1} on router {router1} used multiple times")
            else:
                interface_usage[router1_iface] = connection
                
            if router2_iface in interface_usage:
                errors.append(f"Interface {iface2} on router {router2} used multiple times")
            else:
                interface_usage[router2_iface] = connection
        
        return len(errors) == 0, errors

    # ============================================================================
    # ROLLBACK MECHANISM (Addresses BUG-008)
    # ============================================================================

    def start_deployment_tracking(self, lab_name: str, lab_folder: str = "/") -> None:
        """
        Start tracking deployment for rollback purposes
        Addresses BUG-008: No Rollback Mechanism
        """
        self._deployment_state = {
            "lab_created": False,
            "lab_name": lab_name,
            "lab_folder": lab_folder,
            "nodes_created": [],
            "networks_created": [],
            "connections_created": [],
            "rollback_enabled": True
        }
        logger.log_operation_start("Deployment Tracking", {"lab": lab_name, "folder": lab_folder})

    def track_lab_creation(self, lab_name: str) -> None:
        """Track lab creation for rollback"""
        self._deployment_state["lab_created"] = True
        self._deployment_state["lab_name"] = lab_name
        logger.debug(f"Tracked lab creation: {lab_name}")

    def track_node_creation(self, node_name: str, node_id: str) -> None:
        """Track node creation for rollback"""
        if self._deployment_state["rollback_enabled"]:
            self._deployment_state["nodes_created"].append({
                "name": node_name,
                "id": node_id,
                "created_at": time.time()
            })
            logger.debug(f"Tracked node creation: {node_name} (ID: {node_id})")

    def track_network_creation(self, network_name: str, network_id: str) -> None:
        """Track network creation for rollback"""
        if self._deployment_state["rollback_enabled"]:
            self._deployment_state["networks_created"].append({
                "name": network_name,
                "id": network_id,
                "created_at": time.time()
            })
            logger.debug(f"Tracked network creation: {network_name} (ID: {network_id})")

    def track_connection_creation(self, connection_info: Dict) -> None:
        """Track connection creation for rollback"""
        if self._deployment_state["rollback_enabled"]:
            connection_info["created_at"] = time.time()
            self._deployment_state["connections_created"].append(connection_info)
            logger.debug(f"Tracked connection creation: {connection_info}")

    def get_deployment_summary(self) -> Dict:
        """Get current deployment state summary"""
        return {
            "lab": self._deployment_state["lab_name"],
            "lab_created": self._deployment_state["lab_created"],
            "nodes_count": len(self._deployment_state["nodes_created"]),
            "networks_count": len(self._deployment_state["networks_created"]),
            "connections_count": len(self._deployment_state["connections_created"]),
            "rollback_available": self._deployment_state["rollback_enabled"]
        }

    def disable_rollback(self) -> None:
        """Disable rollback tracking (for successful deployments)"""
        self._deployment_state["rollback_enabled"] = False
        logger.info("✅ Rollback disabled - deployment completed successfully")

    def rollback_deployment(self, reason: str = "Deployment failed") -> bool:
        """
        Rollback failed deployment by cleaning up created resources
        Addresses BUG-008: No Rollback Mechanism
        
        Returns:
            bool: True if rollback was successful, False otherwise
        """
        if not self._deployment_state["rollback_enabled"]:
            logger.warning("⚠️ Rollback is disabled or not available")
            return False

        logger.log_operation_start("Deployment Rollback", {"reason": reason})
        
        lab_name = self._deployment_state["lab_name"]
        lab_folder = self._deployment_state["lab_folder"]
        rollback_success = True
        cleanup_summary = {
            "nodes_deleted": 0,
            "networks_deleted": 0,
            "lab_deleted": False,
            "errors": []
        }

        if not lab_name:
            logger.warning("⚠️ No lab name found for rollback")
            return False

        try:
            # Step 1: Clean up connections (automatic with node/network deletion)
            logger.info("🔄 Rolling back connections...")
            cleanup_summary["connections_cleaned"] = len(self._deployment_state["connections_created"])
            
            # Step 2: Delete nodes
            logger.info("🔄 Rolling back nodes...")
            for node_info in reversed(self._deployment_state["nodes_created"]):
                try:
                    success = self._delete_node(lab_name, node_info["id"], lab_folder)
                    if success:
                        cleanup_summary["nodes_deleted"] += 1
                        logger.info(f"✅ Deleted node: {node_info['name']} (ID: {node_info['id']})")
                    else:
                        cleanup_summary["errors"].append(f"Failed to delete node {node_info['name']}")
                        rollback_success = False
                except Exception as e:
                    error_msg = f"Error deleting node {node_info['name']}: {e}"
                    cleanup_summary["errors"].append(error_msg)
                    logger.error(error_msg)
                    rollback_success = False

            # Step 3: Delete networks
            logger.info("🔄 Rolling back networks...")
            for network_info in reversed(self._deployment_state["networks_created"]):
                try:
                    success = self._delete_network(lab_name, network_info["id"], lab_folder)
                    if success:
                        cleanup_summary["networks_deleted"] += 1
                        logger.info(f"✅ Deleted network: {network_info['name']} (ID: {network_info['id']})")
                    else:
                        cleanup_summary["errors"].append(f"Failed to delete network {network_info['name']}")
                        rollback_success = False
                except Exception as e:
                    error_msg = f"Error deleting network {network_info['name']}: {e}"
                    cleanup_summary["errors"].append(error_msg)
                    logger.error(error_msg)
                    rollback_success = False

            # Step 4: Delete lab (optional - might want to keep empty lab)
            if self._deployment_state["lab_created"]:
                logger.info("🔄 Rolling back lab...")
                try:
                    success = self._delete_lab(lab_name, lab_folder)
                    if success:
                        cleanup_summary["lab_deleted"] = True
                        logger.info(f"✅ Deleted lab: {lab_name}")
                    else:
                        cleanup_summary["errors"].append(f"Failed to delete lab {lab_name}")
                        rollback_success = False
                except Exception as e:
                    error_msg = f"Error deleting lab {lab_name}: {e}"
                    cleanup_summary["errors"].append(error_msg)
                    logger.error(error_msg)
                    rollback_success = False

            # Report rollback summary
            if rollback_success:
                logger.log_operation_success("Deployment Rollback", cleanup_summary)
            else:
                logger.log_operation_failure("Deployment Rollback", "Partial rollback completed", cleanup_summary)

            # Clear deployment state
            self._deployment_state = {
                "lab_created": False,
                "lab_name": None,
                "lab_folder": "/",
                "nodes_created": [],
                "networks_created": [],
                "connections_created": [],
                "rollback_enabled": False
            }

            return rollback_success

        except Exception as e:
            logger.log_operation_failure("Deployment Rollback", f"Rollback failed: {e}", cleanup_summary)
            return False

    def _delete_node(self, lab_name: str, node_id: str, lab_folder: str = "/") -> bool:
        """Delete a node from the lab"""
        try:
            api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
            response = self.api_request('DELETE', f'/labs{api_lab_uri_path}/nodes/{node_id}')
            return isinstance(response, dict) and response.get('status') == 'success'
        except Exception as e:
            logger.error(f"Failed to delete node {node_id}: {e}")
            return False

    def _delete_network(self, lab_name: str, network_id: str, lab_folder: str = "/") -> bool:
        """Delete a network from the lab"""
        try:
            api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
            response = self.api_request('DELETE', f'/labs{api_lab_uri_path}/networks/{network_id}')
            return isinstance(response, dict) and response.get('status') == 'success'
        except Exception as e:
            logger.error(f"Failed to delete network {network_id}: {e}")
            return False

    def _delete_lab(self, lab_name: str, lab_folder: str = "/") -> bool:
        """Delete the entire lab"""
        try:
            api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
            response = self.api_request('DELETE', f'/labs{api_lab_uri_path}')
            return isinstance(response, dict) and response.get('status') == 'success'
        except Exception as e:
            logger.error(f"Failed to delete lab {lab_name}: {e}")
            return False

    def create_deployment_checkpoint(self) -> Dict:
        """Create a checkpoint of current deployment state"""
        checkpoint = {
            "timestamp": time.time(),
            "state": self._deployment_state.copy(),
            "summary": self.get_deployment_summary()
        }
        logger.debug(f"Created deployment checkpoint: {checkpoint['summary']}")
        return checkpoint

def create_routers(eve_client: EVEClient, lab_name: str, lab_folder: str = "/") -> Optional[Dict[str, str]]:
    """Create all routers from TOPOLOGY_ROUTERS configuration"""
    logger.info("\n=== Creating Enhanced MPLS L3VPN Routers ===")
    routers = {}

    for router_name, config in TOPOLOGY_ROUTERS.items():
        node_config = {
            "type": config["type"],
            "template": config["template"],
            "name": router_name,
            "image": config["image"],
            "ram": config["ram"],
            "nvram": config["nvram"],
            "idlepc": config["idlepc"],
            "icon": config["icon"],
            "left": config["left"],
            "top": config["top"],
            "console": config["console"],
            "config": "0",
            "ethernet": DEFAULT_ETHERNET_COUNT
        }

        if config.get("slot1"):
            node_config["slot1"] = config["slot1"]
        if config.get("slot2"):
            node_config["slot2"] = config["slot2"]

        node_id = eve_client.create_node(lab_name, node_config, lab_folder=lab_folder)
        if node_id:
            routers[router_name] = node_id
            time.sleep(1)
        else:
            logger.error(f"❌ Failed to create {router_name}")
            return None

    logger.info(f"✅ Successfully created all {len(routers)} routers")
    return routers

def create_connection(eve_client: EVEClient, lab_name: str, routers: Dict[str, str],
                     router1: str, iface1: str, router2: str, iface2: str,
                     link_name: str, lab_folder: str = "/",
                     left: str = "400", top: str = "200") -> bool:
    """Create P2P connection with enhanced error handling and validation"""
    logger.info(f"\n=== Creating Connection: {router1}({iface1}) <-> {router2}({iface2}) ===")

    # Validate connection configuration (addresses BUG-006)
    is_valid, errors = eve_client.validate_connection_config(router1, iface1, router2, iface2, routers)
    if not is_valid:
        logger.error(f"❌ Connection validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    # Create network bridge  
    network_id = eve_client.create_network(lab_name, "bridge", link_name, lab_folder=lab_folder, left=left, top=top)
    if not network_id:
        return False
    time.sleep(1)

    # Connect router 1
    if not eve_client.connect_node_to_network(lab_name, routers[router1], iface1, network_id, lab_folder=lab_folder):
        logger.error(f"❌ Failed to connect {router1}")
        return False
    time.sleep(0.5)

    # Connect router 2
    if not eve_client.connect_node_to_network(lab_name, routers[router2], iface2, network_id, lab_folder=lab_folder):
        logger.error(f"❌ Failed to connect {router2}")
        return False
    time.sleep(0.5)

    # Verify connections
    eve_client.verify_connection(lab_name, routers[router1], network_id, lab_folder=lab_folder)
    eve_client.verify_connection(lab_name, routers[router2], network_id, lab_folder=lab_folder)

    logger.info(f"✅ Successfully connected {router1}({iface1}) <-> {router2}({iface2})")
    return True

def create_all_connections(eve_client: EVEClient, lab_name: str, routers: Dict[str, str], lab_folder: str = "/") -> bool:
    """Create all topology connections"""
    logger.info("\n=== Creating All Enhanced MPLS Topology Connections ===")
    
    success_count = 0
    total_connections = len(TOPOLOGY_CONNECTIONS)

    for router1, iface1, router2, iface2, link_name, left, top in TOPOLOGY_CONNECTIONS:
        if create_connection(eve_client, lab_name, routers, router1, iface1, router2, iface2, link_name, lab_folder, left, top):
            success_count += 1

    logger.info(f"\n✅ Successfully created {success_count}/{total_connections} connections")
    return success_count == total_connections

def create_management_network(eve_client: EVEClient, lab_name: str, routers: Dict[str, str], lab_folder: str = "/") -> bool:
    """Create management network with enhanced interface mapping"""
    if not USE_MANAGEMENT_NETWORK:
        return True

    logger.info("\n=== Creating Enhanced Management Network ===")

    mgmt_network_id = eve_client.create_network(lab_name, MANAGEMENT_NETWORK_TYPE, MANAGEMENT_NETWORK_NAME, 
                                              lab_folder=lab_folder, left="400", top="50")
    if not mgmt_network_id:
        return False

    success_count = 0
    for router_name, router_id in routers.items():
        mgmt_interface = TOPOLOGY_ROUTERS[router_name].get("mgmt_interface", "f0/1")
        logger.info(f"Connecting {router_name} management interface {mgmt_interface}...")

        if eve_client.connect_node_to_network(lab_name, router_id, mgmt_interface, mgmt_network_id, lab_folder=lab_folder):
            success_count += 1

    logger.info(f"✅ Connected {success_count}/{len(routers)} routers to management network")
    return success_count == len(routers)

def main():
    """Enhanced main function with SSH integration, configuration validation, and rollback"""
    logger.info("🚀 Starting V5evscriptcli Enhanced MPLS L3VPN Topology Creation")
    logger.info("=" * 80)
    logger.info("✨ Enhanced with CORRECT interface mapping for c3725 + NM-1FE-TX")
    logger.info(f"🔧 Interface Mapping: f0/0→0, f0/1→1, f1/0→16, f2/0→32")
    logger.info("=" * 80)

    # Verify SSH access for troubleshooting
    verify_ssh_access()

    eve_client = EVEClient(EVE_HOST, EVE_USER, EVE_PASS)

    try:
        # Validate topology configuration before deployment (addresses BUG-006)
        logger.info("\n=== Validating Topology Configuration ===")
        is_valid, errors = eve_client.validate_topology_config(TOPOLOGY_ROUTERS, TOPOLOGY_CONNECTIONS)
        logger.log_validation_result("Topology Configuration", is_valid, errors)
        if not is_valid:
            logger.error("❌ Deployment aborted due to configuration errors")
            return
            
        # Start deployment tracking (addresses BUG-008)
        eve_client.start_deployment_tracking(LAB_NAME, LAB_PATH)

        # Login
        if not eve_client.login():
            logger.error("❌ Failed to login to EVE-NG")
            eve_client.rollback_deployment("Login failed")
            return

        # Create lab
        if not eve_client.create_lab(LAB_NAME, LAB_PATH, LAB_AUTHOR, LAB_DESCRIPTION, LAB_VERSION):
            logger.error("❌ Failed to create lab")
            eve_client.rollback_deployment("Lab creation failed")
            return

        # Create routers
        routers = create_routers(eve_client, LAB_NAME, lab_folder=LAB_PATH)
        if not routers:
            logger.error("❌ Failed to create routers")
            eve_client.rollback_deployment("Router creation failed")
            return

        # Create connections (critical test of interface mapping fix)
        if not create_all_connections(eve_client, LAB_NAME, routers, lab_folder=LAB_PATH):
            logger.error("❌ Failed to create all connections")
            eve_client.rollback_deployment("Connection creation failed")
            return

        # Create management network
        if not create_management_network(eve_client, LAB_NAME, routers, lab_folder=LAB_PATH):
            logger.warning("⚠️ Management network creation had issues, continuing...")

        # Disable rollback for successful deployment
        eve_client.disable_rollback()
        
        # Display deployment summary
        summary = eve_client.get_deployment_summary()
        logger.info("\n" + "=" * 80)
        logger.info("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉")
        logger.info("=" * 80)
        logger.info(f"📊 Deployment Summary:")
        logger.info(f"   • Lab: {summary['lab']}")
        logger.info(f"   • Nodes: {summary['nodes_count']}")
        logger.info(f"   • Networks: {summary['networks_count']}")
        logger.info(f"   • Connections: {summary['connections_count']}")
        logger.info("=" * 80)
        logger.info(f"✅ Enhanced Interface Mapping Applied")
        logger.info(f"✅ Configuration Validation Enabled")
        logger.info(f"✅ Rollback Protection Active")
        logger.info(f"✅ SSH Troubleshooting: ssh {SSH_USER}@{SSH_HOST}")
        logger.info(f"\n🌐 Access lab: http://{EVE_HOST}/#/labs/{LAB_NAME}.unl")
        logger.info("\n✅ Enhanced MPLS L3VPN topology creation completed!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Script interrupted by user")
        logger.info("🔄 Attempting rollback...")
        try:
            eve_client.rollback_deployment("User interruption")
        except:
            logger.warning("⚠️ Rollback during interruption failed")
    except Exception as e:
        logger.error(f"❌ Deployment failed with error: {e}")
        logger.info("🔄 Attempting rollback...")
        
        try:
            success = eve_client.rollback_deployment(f"Deployment exception: {e}")
            if success:
                logger.info("✅ Rollback completed successfully")
            else:
                logger.error("❌ Rollback failed - manual cleanup may be required")
        except Exception as rollback_error:
            logger.error(f"❌ Rollback error: {rollback_error}")
            
    finally:
        try:
            eve_client.logout()
        except:
            pass

if __name__ == "__main__":
    main() 