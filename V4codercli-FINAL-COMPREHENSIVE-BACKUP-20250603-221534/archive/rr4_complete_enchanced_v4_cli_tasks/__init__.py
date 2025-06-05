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
- Static routes
- Console line configurations (NEW)
"""

__version__ = '1.0.1'

from typing import List, Optional, Type, Any

def get_layer_collector(layer: str) -> Optional[Type[Any]]:
    """Get the collector class for a given layer."""
    # Lazy imports to avoid circular dependencies
    layer_lower = layer.lower()
    
    if layer_lower == 'mpls':
        from .mpls_collector import MPLSCollector
        return MPLSCollector
    elif layer_lower == 'igp':
        from .igp_collector import IGPCollector
        return IGPCollector
    elif layer_lower == 'bgp':
        from .bgp_collector import BGPCollector
        return BGPCollector
    elif layer_lower == 'vpn':
        from .vpn_collector import VPNCollector
        return VPNCollector
    elif layer_lower == 'interfaces':
        from .interface_collector import InterfaceCollector
        return InterfaceCollector
    elif layer_lower == 'health':
        from .health_collector import HealthCollector
        return HealthCollector
    elif layer_lower == 'static':
        from .static_route_collector import StaticRouteCollector
        return StaticRouteCollector
    elif layer_lower == 'console':
        from .console_line_collector import ConsoleLineCollector
        return ConsoleLineCollector
    else:
        return None

def get_available_layers() -> List[str]:
    """Get list of available collection layers."""
    return ['mpls', 'igp', 'bgp', 'vpn', 'interfaces', 'health', 'static', 'console']

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
    'validate_layers'
]
