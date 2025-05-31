#!/usr/bin/env python3
"""
Test Package for RR4 Complete Enhanced v4 CLI

This package contains all test modules organized by category:
- unit/: Unit tests for individual modules
- integration/: Integration tests for module interactions  
- performance/: Performance and stress tests

Author: AI Assistant
Version: 1.0.0
Created: 2025-01-30
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATA_DIR = project_root / "tests" / "data"
TEST_OUTPUT_DIR = project_root / "tests" / "output"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True) 