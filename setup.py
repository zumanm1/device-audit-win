from setuptools import setup, find_packages

setup(
    name="rr4-complete-enchanced-v4-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'nornir>=3.5.0',
        'nornir-netmiko>=1.0.1',
        'nornir-utils>=0.2.0',
        'nornir-napalm>=0.5.0',
        'nornir-scrapli>=2025.1.30',
        'click>=8.0.0',
        'python-dotenv>=1.0.0',
        'pyyaml>=6.0.1',
    ],
    entry_points={
        'console_scripts': [
            'rr4-cli=rr4_complete_enchanced_v4_cli.main:main',
        ],
    },
) 