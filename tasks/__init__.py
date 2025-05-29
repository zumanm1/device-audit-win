#!/usr/bin/env python3
"""
Tasks Package for RR4 Complete Enhanced v4 CLI

This package contains layer-specific data collectors for network devices.
Each collector handles commands and data collection for a specific network layer.

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-27
"""

from typing import Dict, Any
import logging

# Import all collectors
from .health_collector import HealthCollector
from .interface_collector import InterfaceCollector
from .igp_collector import IGPCollector
from .mpls_collector import MPLSCollector
from .bgp_collector import BGPCollector
from .vpn_collector import VPNCollector
from .static_route_collector import StaticRouteCollector

# Collector registry
LAYER_COLLECTORS = {
    'health': HealthCollector,
    'interfaces': InterfaceCollector,
    'igp': IGPCollector,
    'mpls': MPLSCollector,
    'bgp': BGPCollector,
    'vpn': VPNCollector,
    'static': StaticRouteCollector
}

def get_layer_collector(layer: str):
    """Get collector instance for specified layer."""
    if layer not in LAYER_COLLECTORS:
        raise ValueError(f"Unknown layer: {layer}. Available layers: {list(LAYER_COLLECTORS.keys())}")
    
    collector_class = LAYER_COLLECTORS[layer]
    return collector_class()

def get_available_layers():
    """Get list of available collection layers."""
    return list(LAYER_COLLECTORS.keys())

def validate_layers(layers: list):
    """Validate that all specified layers are available."""
    available = get_available_layers()
    invalid = [layer for layer in layers if layer not in available]
    
    if invalid:
        raise ValueError(f"Invalid layers: {invalid}. Available layers: {available}")
    
    return True

__all__ = [
    'HealthCollector',
    'InterfaceCollector', 
    'IGPCollector',
    'MPLSCollector',
    'BGPCollector',
    'VPNCollector',
    'StaticRouteCollector',
    'get_layer_collector',
    'get_available_layers',
    'validate_layers',
    'LAYER_COLLECTORS'
]
