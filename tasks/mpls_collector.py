#!/usr/bin/env python3
"""
MPLS Collector for RR4 Complete Enhanced v4 CLI
"""

import logging
from typing import Dict, Any, List
from core.data_parser import DataParser
from core.output_handler import OutputHandler

class MPLSCollector:
    def __init__(self):
        self.logger = logging.getLogger('rr4_collector.mpls_collector')
        self.data_parser = DataParser()
    
    def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                          output_handler: OutputHandler) -> Dict[str, Any]:
        commands = [
            "show mpls interfaces",
            "show mpls ldp neighbor",
            "show mpls forwarding-table"
        ]
        
        results = {
            'hostname': hostname,
            'platform': platform,
            'layer': 'mpls',
            'success_count': 0,
            'failure_count': 0
        }
        
        for command in commands:
            try:
                if hasattr(connection, 'send_command'):
                    output = connection.send_command(command, read_timeout=60)
                    results['success_count'] += 1
                else:
                    results['failure_count'] += 1
            except Exception as e:
                self.logger.error(f"Command failed: {command} - {e}")
                results['failure_count'] += 1
        
        return results 