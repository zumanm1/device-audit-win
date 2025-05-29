#!/usr/bin/env python3
"""
BGP Collector for RR4 Complete Enhanced v4 CLI
"""

import logging
from typing import Dict, Any, List

from core.data_parser import DataParser
from core.output_handler import OutputHandler

class BGPCollector:
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.bgp_collector')
        self.data_parser = DataParser()
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        commands = [
            "show ip bgp summary",
            "show ip bgp neighbors",
            "show ip bgp"
        ]
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'bgp',
            'success_count': 0,
            'failure_count': 0
        }
        
        for command in commands:
            try:
                if hasattr(connection, 'send_command'):
                    # BGP tables can be large, use longer timeout
                    timeout = 120 if 'show ip bgp' == command else 60
                    output = connection.send_command(command, read_timeout=timeout)
                    results['success_count'] += 1
                else:
                    results['failure_count'] += 1
            except Exception as e:
                self.logger.error(f"Command failed: {command} - {e}")
                results['failure_count'] += 1
        
        return results 