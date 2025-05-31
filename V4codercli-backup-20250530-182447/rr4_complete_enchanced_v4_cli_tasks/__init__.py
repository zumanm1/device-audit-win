#!/usr/bin/env python3
"""
Tasks package for RR4 Complete Enhanced v4 CLI.

This package contains task modules for collecting:
- Health information
- Interface data
- IGP routing
- MPLS configuration
- BGP routing
- VPN services
"""

__version__ = '1.0.0'

from typing import List, Optional, Type
from .base_collector import BaseCollector
from .mpls_collector import MPLSCollector
from .igp_collector import IGPCollector
from .bgp_collector import BGPCollector
from .vpn_collector import VPNCollector
from .interface_collector import InterfaceCollector
from .health_collector import HealthCollector
from .static_route_collector import StaticRouteCollector

# Layer to collector mapping
LAYER_COLLECTORS = {
    'mpls': MPLSCollector,
    'igp': IGPCollector,
    'bgp': BGPCollector,
    'vpn': VPNCollector,
    'interfaces': InterfaceCollector,
    'health': HealthCollector,
    'static': StaticRouteCollector
}

def get_layer_collector(layer: str) -> Optional[Type[BaseCollector]]:
    """Get the collector class for a given layer."""
    return LAYER_COLLECTORS.get(layer.lower())

def get_available_layers() -> List[str]:
    """Get list of available collection layers."""
    return list(LAYER_COLLECTORS.keys())

def validate_layers(layers: List[str]) -> bool:
    """Validate that all specified layers are supported."""
    available_layers = get_available_layers()
    for layer in layers:
        if layer.lower() not in available_layers:
            raise ValueError(f"Unsupported layer: {layer}. Available layers: {', '.join(available_layers)}")
    return True

__all__ = [
    'get_layer_collector',
    'get_available_layers',
    'validate_layers',
    'BaseCollector',
    'MPLSCollector',
    'IGPCollector',
    'BGPCollector',
    'VPNCollector',
    'InterfaceCollector',
    'HealthCollector',
    'StaticRouteCollector'
]
