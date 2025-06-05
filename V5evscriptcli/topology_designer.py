#!/usr/bin/env python3
"""
V5evscriptcli Topology Designer Module
Handles topology management and deployment functionality
"""

import json
import os
import logging
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

class TopologyDesigner:
    """Python-based topology designer for EVE-NG lab deployment"""
    
    def __init__(self):
        self.name = "V5evscriptcli Topology Designer"
        self.version = "1.0"
        
    def load_default_mpls_topology(self):
        """Load the default MPLS L3VPN topology configuration"""
        try:
            template_path = Path(__file__).parent / "templates" / "default_mpls_l3vpn.json"
            
            if not template_path.exists():
                logger.warning(f"Default MPLS topology template not found at {template_path}")
                return None
                
            with open(template_path, 'r') as f:
                topology_data = json.load(f)
                
            logger.info("✅ Default MPLS L3VPN topology loaded successfully")
            logger.info(f"Topology: {topology_data['metadata']['name']} - {topology_data['metadata']['description']}")
            logger.info(f"Routers: {topology_data['metadata']['router_count']}, Connections: {topology_data['metadata']['connection_count']}")
            
            return topology_data
            
        except Exception as e:
            logger.error(f"❌ Failed to load default MPLS topology: {e}")
            return None
    
    def get_default_topology_summary(self):
        """Get a summary of the default topology for display"""
        topology_data = self.load_default_mpls_topology()
        if not topology_data:
            return None
            
        return {
            "name": topology_data["metadata"]["name"],
            "description": topology_data["metadata"]["description"],
            "router_count": topology_data["metadata"]["router_count"],
            "connection_count": topology_data["metadata"]["connection_count"],
            "topology_type": topology_data["metadata"]["topology_type"],
            "routers": list(topology_data["routers"].keys()),
            "interface_mappings": topology_data["interface_mappings"],
            "features": [
                "Complete MPLS L3VPN setup",
                "BGP Route Reflector architecture", 
                "Customer Edge routers (CE-4, CE-5)",
                "Provider Edge routers (PE1, PE2)",
                "Provider core router (P)",
                "Management network support",
                "Cisco 3725 platform optimized",
                "Fixed interface mappings (f1/0→16, f2/0→32)"
            ]
        }
    
    def deploy_default_mpls_topology(self, eve_host, eve_user, eve_pass, lab_name=None):
        """Deploy the default MPLS L3VPN topology to EVE-NG using the proven deployment script"""
        try:
            if not lab_name:
                lab_name = "mpls_l3vpn_lab"
            
            logger.info(f"🚀 Deploying MPLS L3VPN topology to EVE-NG at {eve_host}")
            
            # Use the proven deployment script
            from deploy_mpls_topology import deploy_mpls_topology
            result = deploy_mpls_topology(eve_host, eve_user, eve_pass, lab_name)
            
            if result.get('success'):
                logger.info("✅ MPLS L3VPN topology deployed successfully using proven script!")
                
                # Enhance the result with additional configuration details
                result["configuration_guide"] = {
                    "deployment_order": [
                        "1. Configure P router first (OSPF, MPLS LDP)",
                        "2. Configure PE routers (OSPF, MPLS, BGP, VRFs)",
                        "3. Configure RR1 (OSPF, MPLS, BGP Route Reflector)",
                        "4. Configure CE routers (BGP to PEs)",
                        "5. Configure management interfaces if using management network",
                        "6. Verify MPLS LSPs and BGP VPNv4 routes",
                        "7. Test end-to-end connectivity"
                    ],
                    "key_services": [
                        "VRF_D on PE1 (AS 400 route policy, RT manipulation)",
                        "VRF_E on PE2 (AS 500 route policy, RT manipulation)",
                        "Inter-VRF communication via route policies",
                        "BGP Route Reflector for iBGP scalability"
                    ],
                    "interface_types": {
                        "f0/0, f0/1": "Onboard FastEthernet interfaces",
                        "f1/0": "NM-1FE-TX in slot 1 (index 16)",
                        "f2/0": "NM-1FE-TX in slot 2 (index 32)"
                    }
                }
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy MPLS topology: {e}")
            return {"success": False, "error": str(e)} 