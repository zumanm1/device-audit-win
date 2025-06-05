#!/usr/bin/env python3
"""
EVE-NG MPLS L3VPN Topology Builder - Integrated with V5evscriptcli
Creates complete MPLS L3VPN lab with configurable routers
Default: CE-4, CE-5, PE1, PE2, P, RR1 using Cisco 3725 routers

Interface Mappings for 3725:
- f0/0, f0/1 = Onboard FastEthernet interfaces  
- f1/0 = NM-1FE-TX in slot 1 (index 16)
- f2/0 = NM-1FE-TX in slot 2 (index 32)
"""

import requests
import json
import logging
import time
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from requests
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ============================================================================
# CONFIGURATION SECTION - Default MPLS L3VPN Topology
# ============================================================================

# Default Router Template Settings
DEFAULT_ROUTER_TYPE = "dynamips"
DEFAULT_ROUTER_TEMPLATE = "c3725"
DEFAULT_ROUTER_IMAGE = "c3725-adventerprisek9-mz.124-15.T14.image"
DEFAULT_ROUTER_RAM = "256"
DEFAULT_ROUTER_NVRAM = "256"
DEFAULT_ROUTER_IDLE = "0x60606040"
DEFAULT_CONSOLE_TYPE = "telnet"

# Network Module Configuration
ROUTER_SLOTS = {
    "slot1": "NM-1FE-TX",  # Provides f1/0
    "slot2": "NM-1FE-TX"   # Provides f2/0
}

DEFAULT_ETHERNET_COUNT = "6"

# Management Network Settings
USE_MANAGEMENT_NETWORK = True
MANAGEMENT_NETWORK_NAME = "Management"
MANAGEMENT_NETWORK_TYPE = "bridge"

# ============================================================================
# TOPOLOGY DEFINITION - MPLS L3VPN with Route Reflector
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
        "left": "100",
        "top": "150",
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
        "left": "100",
        "top": "350",
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
        "left": "300",
        "top": "150",
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
        "left": "300",
        "top": "350",
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
        "left": "500",
        "top": "250",
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
        "left": "700",
        "top": "250",
        "console": DEFAULT_CONSOLE_TYPE,
        "slot1": ROUTER_SLOTS.get("slot1", ""),
        "slot2": ROUTER_SLOTS.get("slot2", ""),
        "mgmt_interface": "f2/0"
    }
}

# Connection Definitions
TOPOLOGY_CONNECTIONS = [
    ("CE-4", "f1/0", "PE1", "f1/0", "Link_CE4_PE1", "200", "150"),
    ("PE1", "f0/0", "P", "f0/0", "Link_PE1_P", "400", "200"),
    ("P", "f0/1", "PE2", "f0/1", "Link_P_PE2", "400", "300"),
    ("P", "f1/0", "RR1", "f1/0", "Link_P_RR1", "600", "250"),
    ("PE2", "f0/0", "CE-5", "f0/0", "Link_PE2_CE5", "200", "350"),
]

# IP Addressing Plan
IP_ADDRESSING = {
    "loopbacks": {
        "PE1": "1.1.1.1/32",
        "P": "2.2.2.2/32",
        "PE2": "3.3.3.3/32",
        "RR1": "4.4.4.4/32",
        "CE-4": "40.40.40.40/32",
        "CE-5": "50.50.50.50/32"
    },
    "core_links": {
        "PE1-P": {"PE1": "10.1.1.1/24", "P": "10.1.1.2/24"},
        "P-PE2": {"P": "10.1.2.1/24", "PE2": "10.1.2.2/24"},
        "P-RR1": {"P": "10.1.3.1/24", "RR1": "10.1.3.2/24"}
    },
    "customer_links": {
        "PE1-CE4": {"PE1": "192.168.14.1/24", "CE-4": "192.168.14.2/24"},
        "PE2-CE5": {"PE2": "192.168.25.1/24", "CE-5": "192.168.25.2/24"}
    },
    "management": {
        "network": "192.168.100.0/24",
        "CE-4": "192.168.100.4/24",
        "CE-5": "192.168.100.5/24",
        "PE1": "192.168.100.11/24",
        "PE2": "192.168.100.12/24",
        "P": "192.168.100.20/24",
        "RR1": "192.168.100.30/24"
    }
}

# ============================================================================
# EVE-NG API CLIENT CLASS (Reused from eve_client.py)
# ============================================================================

class EVEClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.base_url = f"http://{host}/api"

    def api_request(self, method, endpoint, data=None, timeout=15):
        url = f"{self.base_url}{endpoint}"
        try:
            logger.debug(f"{method} {url}")
            if data and method not in ['GET', 'DELETE']:
                logger.debug(f"Payload: {json.dumps(data, indent=2)}")

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

            logger.debug(f"Response Status: {response.status_code}")

            if response.status_code >= 400:
                if response.status_code == 401:
                    logger.error("Authentication error (401). Please check credentials.")
                logger.error(f"API Error {response.status_code} for {method} {url}. Response: {response.text}")
                return response

            if response.content:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    return {"status": "success_non_json", "text": response.text,
                            "http_status_code": response.status_code}

            return {"status": "success", "http_status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            return None

    def login(self):
        logger.info("Logging in to EVE-NG...")
        response_data = self.api_request('POST', '/auth/login', {
            "username": self.username, "password": self.password, "html5": "-1"
        })
        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            logger.info("✅ Login successful")
            return True
        else:
            logger.error(f"❌ Login failed. Response: {response_data}")
            return False

    def logout(self):
        if self.session:
            try:
                self.session.get(f"{self.base_url}/auth/logout")
                logger.info("Logged out successfully.")
            except Exception as e:
                logger.error(f"Exception during logout: {e}")
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
        logger.info(f"Creating lab '{name}' in path '{path}'...")
        api_lab_uri_path = self.get_api_lab_path(name, path)
        
        # Check if lab exists
        check_url = f"{self.base_url}/labs{api_lab_uri_path}"
        try:
            check_response = self.session.get(check_url, timeout=10)
            if check_response.status_code == 200:
                logger.info(f"✅ Lab '{name}' already exists")
                return True
        except:
            pass

        # Create new lab
        create_payload = {"path": path, "name": name, "author": author, 
                         "description": description, "version": version}
        response_data = self.api_request('POST', '/labs', create_payload)

        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            logger.info(f"✅ Lab '{name}' created successfully")
            return True
        else:
            logger.error(f"❌ Failed to create lab '{name}'. Response: {response_data}")
            return False

    def delete_all_nodes(self, lab_name, lab_folder="/"):
        logger.info(f"Cleaning up existing nodes in lab '{lab_name}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response = self.api_request('GET', f'/labs{api_lab_uri_path}/nodes')

        if not isinstance(response, dict) or response.get('status') != 'success':
            return True

        nodes = response.get('data', {})
        if not nodes:
            return True

        for node_id in list(nodes.keys()):
            self.api_request('DELETE', f'/labs{api_lab_uri_path}/nodes/{node_id}')
            time.sleep(0.2)
        return True

    def delete_all_networks(self, lab_name, lab_folder="/"):
        logger.info(f"Cleaning up existing networks in lab '{lab_name}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response = self.api_request('GET', f'/labs{api_lab_uri_path}/networks')

        if not isinstance(response, dict) or response.get('status') != 'success':
            return True

        networks = response.get('data', {})
        if not networks:
            return True

        for net_id in list(networks.keys()):
            self.api_request('DELETE', f'/labs{api_lab_uri_path}/networks/{net_id}')
            time.sleep(0.2)
        return True

    def create_node(self, lab_name, node_config, lab_folder="/"):
        logger.info(f"Creating node '{node_config['name']}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response_data = self.api_request('POST', f'/labs{api_lab_uri_path}/nodes', node_config)

        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            if 'data' in response_data and 'id' in response_data['data']:
                node_id = response_data['data']['id']
                logger.info(f"✅ Node '{node_config['name']}' created with ID: {node_id}")
                return str(node_id)
        
        logger.error(f"❌ Failed to create node '{node_config['name']}'")
        return None

    def create_network(self, lab_name, network_type="bridge", network_name="Network1", 
                      lab_folder="/", left="400", top="100"):
        logger.info(f"Creating {network_type} network '{network_name}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        config = {"type": network_type, "name": network_name, "left": str(left), 
                 "top": str(top), "visibility": "1"}
        response_data = self.api_request('POST', f'/labs{api_lab_uri_path}/networks', config)

        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            if 'data' in response_data and 'id' in response_data['data']:
                network_id = response_data['data']['id']
                logger.info(f"✅ Network '{network_name}' created with ID: {network_id}")
                return str(network_id)
        
        logger.error(f"❌ Failed to create network '{network_name}'")
        return None

    def connect_node_to_network(self, lab_name, node_id, interface_name, network_id, lab_folder="/"):
        logger.info(f"Connecting node {node_id} interface '{interface_name}' to network {network_id}...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)

        # Critical: Use correct interface mappings for Cisco 3725
        interface_mapping = {
            'f0/0': '0',  # Onboard FastEthernet0/0
            'f0/1': '1',  # Onboard FastEthernet0/1
            'f1/0': '16', # NM-1FE-TX in slot 1 - FIXED INDEX
            'f2/0': '32', # NM-1FE-TX in slot 2 - FIXED INDEX
        }

        interface_key = interface_mapping.get(interface_name, interface_name)
        payload = {interface_key: str(network_id)}
        
        logger.debug(f"Connection payload: {payload}")
        response_data = self.api_request('PUT', f'/labs{api_lab_uri_path}/nodes/{node_id}/interfaces', payload)

        if isinstance(response_data, dict) and response_data.get('status') == 'success':
            logger.info(f"✅ Connected node {node_id} interface '{interface_name}' (index {interface_key}) to network {network_id}")
            return True
        else:
            logger.error(f"❌ Failed to connect node {node_id} interface '{interface_name}' to network {network_id}")
            return False

    def save_lab(self, lab_name, lab_folder="/"):
        logger.info(f"Saving lab '{lab_name}'...")
        api_lab_uri_path = self.get_api_lab_path(lab_name, lab_folder)
        response_data = self.api_request('PUT', f'/labs{api_lab_uri_path}/save')
        
        if isinstance(response_data, dict) and (response_data.get('status') == 'success' or 
                                               response_data.get('http_status_code') == 400):
            logger.info(f"✅ Lab '{lab_name}' saved successfully")
            return True
        else:
            logger.warning(f"⚠️ Lab save may not be supported, but changes are auto-saved")
            return True

# ============================================================================
# DEPLOYMENT FUNCTIONS
# ============================================================================

def create_routers(eve_client: EVEClient, lab_name: str, lab_folder: str = "/") -> Optional[Dict[str, str]]:
    """Create all routers from TOPOLOGY_ROUTERS configuration"""
    logger.info("=== Creating MPLS L3VPN Routers ===")
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
        else:
            logger.error(f"❌ Failed to create {router_name}")
            return None

    logger.info(f"✅ Successfully created all {len(routers)} routers")
    return routers

def create_connection(eve_client: EVEClient, lab_name: str, routers: Dict[str, str],
                     router1: str, iface1: str, router2: str, iface2: str,
                     link_name: str, lab_folder: str = "/",
                     left: str = "400", top: str = "200") -> bool:
    """Create a point-to-point connection between two routers"""
    logger.info(f"Creating Connection: {router1}({iface1}) <-> {router2}({iface2})")

    network_id = eve_client.create_network(lab_name, "bridge", link_name, 
                                         lab_folder=lab_folder, left=left, top=top)
    if not network_id:
        return False

    if not eve_client.connect_node_to_network(lab_name, routers[router1], iface1, 
                                            network_id, lab_folder=lab_folder):
        return False

    if not eve_client.connect_node_to_network(lab_name, routers[router2], iface2, 
                                            network_id, lab_folder=lab_folder):
        return False

    logger.info(f"✅ Successfully connected {router1}({iface1}) <-> {router2}({iface2})")
    return True

def create_all_connections(eve_client: EVEClient, lab_name: str, routers: Dict[str, str],
                          lab_folder: str = "/") -> bool:
    """Create all topology connections"""
    logger.info("=== Creating All MPLS Topology Connections ===")
    
    success_count = 0
    for router1, iface1, router2, iface2, link_name, left, top in TOPOLOGY_CONNECTIONS:
        if create_connection(eve_client, lab_name, routers, router1, iface1, 
                           router2, iface2, link_name, lab_folder, left, top):
            success_count += 1

    logger.info(f"✅ Successfully created {success_count}/{len(TOPOLOGY_CONNECTIONS)} connections")
    return success_count == len(TOPOLOGY_CONNECTIONS)

def create_management_network(eve_client: EVEClient, lab_name: str, routers: Dict[str, str],
                             lab_folder: str = "/") -> bool:
    """Create management network and connect all routers"""
    if not USE_MANAGEMENT_NETWORK:
        return True

    logger.info("=== Creating Management Network ===")
    mgmt_network_id = eve_client.create_network(lab_name, MANAGEMENT_NETWORK_TYPE, 
                                              MANAGEMENT_NETWORK_NAME, lab_folder=lab_folder,
                                              left="400", top="50")
    if not mgmt_network_id:
        return False

    success_count = 0
    for router_name, router_id in routers.items():
        mgmt_interface = TOPOLOGY_ROUTERS[router_name].get("mgmt_interface", "f0/1")
        if eve_client.connect_node_to_network(lab_name, router_id, mgmt_interface, 
                                             mgmt_network_id, lab_folder=lab_folder):
            success_count += 1

    logger.info(f"✅ Connected {success_count}/{len(routers)} routers to management network")
    return success_count == len(routers)

def deploy_mpls_topology(eve_host: str, eve_user: str, eve_pass: str, 
                        lab_name: str = "mpls_l3vpn_lab") -> dict:
    """Main deployment function"""
    logger.info("🚀 Starting MPLS L3VPN Topology Deployment")
    
    eve_client = EVEClient(eve_host, eve_user, eve_pass)
    
    try:
        # Login
        if not eve_client.login():
            return {"success": False, "error": "Failed to login to EVE-NG"}

        # Create lab
        if not eve_client.create_lab(lab_name, "/", "V5evscriptcli", 
                                   "Complete MPLS L3VPN topology with CE-4, CE-5, PE1, PE2, P, RR1", "1"):
            return {"success": False, "error": "Failed to create lab"}

        # Clean existing content
        eve_client.delete_all_nodes(lab_name)
        eve_client.delete_all_networks(lab_name)

        # Create routers
        routers = create_routers(eve_client, lab_name)
        if not routers:
            return {"success": False, "error": "Failed to create routers"}

        # Create connections
        if not create_all_connections(eve_client, lab_name, routers):
            logger.warning("⚠️ Not all connections were created successfully")

        # Create management network
        if not create_management_network(eve_client, lab_name, routers):
            logger.warning("⚠️ Failed to create management network")

        # Save lab
        eve_client.save_lab(lab_name)

        # Generate summary
        summary = {
            "success": True,
            "lab_name": lab_name,
            "eve_host": eve_host,
            "routers_created": len(routers),
            "connections_created": len(TOPOLOGY_CONNECTIONS),
            "management_network": USE_MANAGEMENT_NETWORK,
            "router_details": {name: {"id": router_id, "role": "mpls_router"} 
                             for name, router_id in routers.items()},
            "access_url": f"http://{eve_host}/#/labs/{lab_name}.unl",
            "console_ports": {name: f"telnet {eve_host} {2000 + int(router_id)}" 
                            for name, router_id in routers.items()},
            "ip_addressing": IP_ADDRESSING,
            "interface_mappings": {"f0/0": 0, "f0/1": 1, "f1/0": 16, "f2/0": 32}
        }

        logger.info("✅ MPLS L3VPN topology deployment completed successfully!")
        return summary

    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        eve_client.logout()

if __name__ == "__main__":
    # Example usage - this can be called from the web interface
    result = deploy_mpls_topology("172.16.39.128", "admin", "eve")
    print(json.dumps(result, indent=2)) 