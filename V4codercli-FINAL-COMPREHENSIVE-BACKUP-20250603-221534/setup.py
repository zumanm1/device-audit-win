#!/usr/bin/env python3
"""
Setup script for V4codercli - Network State Collector CLI

Cross-platform compatible setup for Windows, Linux, and macOS.
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Read version from main module
VERSION = "1.0.1-CrossPlatform"

# Read README content
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = """
V4codercli - Cross-Platform Network State Collector CLI

A comprehensive CLI-based network state collection system for IP-MPLS networks
using Nornir, Netmiko, and advanced parsing for Cisco IOS, IOS XE, and IOS XR devices.

Features:
- Cross-platform compatibility (Windows/Linux/macOS)
- SSH connection pooling and jump host support
- Multi-layer network data collection
- Comprehensive error handling and diagnostics
- Modern Python design patterns
    """

# Read requirements
requirements_file = Path(__file__).parent / "requirements-minimal.txt"
install_requires = []
if requirements_file.exists():
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # Handle conditional dependencies
                if ';' in line:
                    # Keep conditional dependencies as is
                    install_requires.append(line)
                else:
                    install_requires.append(line)

# Platform-specific requirements
extras_require = {
    'dev': [
        'pytest>=7.0.0',
        'pytest-cov>=3.0.0',
        'black>=22.0.0',
        'flake8>=4.0.0'
    ],
    'enhanced': [
        'scrapli>=2022.7.30',
        'nornir-scrapli>=2022.7.30',
        'rich>=12.0.0',
        'ttp>=0.9.0',
        'json5>=0.9.6'
    ],
    'full': [
        'pytest>=7.0.0',
        'pytest-cov>=3.0.0',
        'black>=22.0.0',
        'flake8>=4.0.0',
        'scrapli>=2022.7.30',
        'nornir-scrapli>=2022.7.30',
        'rich>=12.0.0',
        'ttp>=0.9.0',
        'json5>=0.9.6'
    ]
}

# Entry points for command-line scripts
entry_points = {
    'console_scripts': [
        'v4codercli=rr4-complete-enchanced-v4-cli:main',
        'v4-collector=rr4-complete-enchanced-v4-cli:main',
        'rr4-cli=start_rr4_cli_enhanced:main',
        'v4-health=system_health_monitor:main'
    ]
}

# Classifiers for PyPI
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: System Administrators',
    'Intended Audience :: Telecommunications Industry',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Topic :: System :: Networking',
    'Topic :: System :: Systems Administration',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Environment :: Console',
    'Natural Language :: English'
]

# Package data to include
package_data = {
    '': [
        '*.txt', '*.md', '*.csv', '*.env-t', '*.json', '*.yaml', '*.yml',
        'cisco_legacy_ssh_config'
    ]
}

# Data files to include
data_files = [
    ('config', ['rr4-complete-enchanced-v4-cli.env-t', '.env-t']),
    ('inventory', ['rr4-complete-enchanced-v4-cli-routers01.csv']),
    ('docs', ['QUICK_START.txt', 'STARTUP_COMMANDS_GUIDE.txt']),
]

setup(
    name="v4codercli",
    version=VERSION,
    author="AI Assistant",
    author_email="assistant@v4codercli.local",
    description="Cross-Platform Network State Collector CLI for Cisco Devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/v4codercli/v4codercli",
    project_urls={
        "Bug Reports": "https://github.com/v4codercli/v4codercli/issues",
        "Source": "https://github.com/v4codercli/v4codercli",
        "Documentation": "https://github.com/v4codercli/v4codercli/docs"
    },
    packages=find_packages(),
    classifiers=classifiers,
    python_requires='>=3.8',
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points=entry_points,
    package_data=package_data,
    data_files=data_files,
    include_package_data=True,
    zip_safe=False,
    
    # Cross-platform specific options
    options={
        'build_scripts': {
            'executable': sys.executable
        }
    },
    
    # Keywords for discovery
    keywords=[
        'networking', 'cisco', 'network-automation', 'cli', 'netmiko', 'nornir',
        'network-monitoring', 'mpls', 'bgp', 'ospf', 'isis', 'cross-platform',
        'ssh', 'jump-host', 'network-audit', 'network-discovery'
    ]
)

# Post-installation message
if __name__ == "__main__":
    print("\n" + "="*70)
    print("V4CODERCLI INSTALLATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("Cross-platform Network State Collector CLI v" + VERSION)
    print("\nQuick Start Commands:")
    print("  v4codercli --help                 # Show main CLI help")
    print("  rr4-cli --option 11              # First-time setup wizard")
    print("  v4-health                        # System health check")
    print("\nConfiguration:")
    print("  Edit .env-t file for your environment")
    print("  Update router inventory CSV file")
    print("\nDocumentation:")
    print("  Check QUICK_START.txt and STARTUP_COMMANDS_GUIDE.txt")
    print("\nSupported Platforms:")
    print("  ✅ Windows 10/11")
    print("  ✅ Linux (Ubuntu/CentOS/RHEL)")
    print("  ✅ macOS 11+")
    print("="*70 + "\n") 