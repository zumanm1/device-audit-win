#!/usr/bin/env python3
"""
IGP Layer Collector for RR4 CLI
Collects IGP (OSPF/EIGRP/IS-IS) related information from devices
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rr4-complete-enchanced-v4-cli-core'))

import logging
from typing import Dict, Any, List
from data_parser import DataParser
from output_handler import OutputHandler 